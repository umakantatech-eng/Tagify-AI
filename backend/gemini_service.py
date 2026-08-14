import os
import json
from typing import List, Dict, Any
import io
import requests
import aiohttp
import base64
from PIL import Image
from dotenv import load_dotenv
import asyncio

load_dotenv()

# ============================================================
# CATEGORY REGISTRY — Add new categories here easily
# ============================================================
CATEGORY_REGISTRY = {
    "Kurti": {
        "fields": ["Color", "Fit/Shape", "Neck", "Occasion", "Ornamentation", "Pattern", "PnP", "Sleeve Styling", "Length", "Sleeve Length"],
        "description": "A short or long Indian top garment (kurti/kurta) worn alone or with pants/leggings/palazzo. NOT a saree."
    },
    "Saree": {
        "fields": ["color", "Blouse Color", "blouse_pattern", "border", "border_width", "occasion", "ornamentation", "pallu_details", "pattern", "print_or_pattern_type"],
        "description": "A traditional Indian draped garment consisting of a long unstitched cloth, worn with a blouse piece."
    },
    "Men Shirt": {
        "fields": ["closure", "color", "hemline", "length", "neck", "occasion", "pattern", "print_or_pattern_type", "sleeve_length", "sleeve_styling", "fit_shape"],
        "description": "A men's woven shirt / casual shirt / formal shirt. Has a collar/neckline, buttons/closure, hemline, and sleeves."
    }
}

# ============================================================
# UNIFIED SMART SYSTEM PROMPT
# ============================================================
SMART_SYSTEM_INSTRUCTION = """You are an expert AI product tagger for Indian fashion e-commerce. You will analyze N garment images.

═══════════════════════════════════════════════════════
STEP 1: IDENTIFY CATEGORY (for each image independently)
═══════════════════════════════════════════════════════
Look at the garment and pick ONE category:
- "Kurti": A short/long Indian top garment for women (kurta/kurti). Worn as a top. Has sleeves, neckline, body length. Typically ethnic Indian style.
- "Saree": A traditional long draped cloth worn with a blouse. Has a pallu, border, and drape.
- "Men Shirt": A men's woven shirt (casual, formal, or ethnic). Has a collar/neckline, button closure, distinct hemline. Worn by men as a top.
  → Key difference from Kurti: Men Shirts are typically straight-cut western-style or casual shirts for men. Kurtis are Indian ethnic tops for women.

═══════════════════════════════════════════════════════
STEP 2: EXTRACT ATTRIBUTES based on detected category
═══════════════════════════════════════════════════════

━━━ IF CATEGORY = "Kurti" ━━━
Extract these EXACT fields:
- Color: The DOMINANT base/background color of the garment fabric.
  ⚠️ CRITICAL RULES:
  → MUST output a value from the list. NEVER leave empty.
  → Printed garments: return the BACKGROUND fabric color (e.g., a pink kurti with white flowers → "Pink")
  → Use "Multicolor" ONLY if the garment fabric itself has equal amounts of multiple colors (like rainbow tie-dye or big color-block panels with 3+ colors).
  → Do NOT use "Multicolor" just because a print has multiple colored elements on a single-color base.
  → If the same product is shown in multiple color options side by side, pick the COLOR OF THE LARGEST/MOST VISIBLE piece.
  → STANDARDIZE LIGHT SHADES: If the fabric is off-white, very light beige, or cream (which often looks different due to warm studio lighting), consistently output "Cream" to avoid variations.
  [Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Multicolor, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Teal, White, Yellow, Lemon Yellow, Gold]
- Fit/Shape: [A-line, Anarkali, Angrakha, Assymetrical, Flared, Gown, High-Slit, Jacket Kurta, Kaftan, Maternity, Short Kurti, Shrug Kurti, Tiered] — NOTE: Classify any straight-cut as "A-line". If length is Above Knee → "Short Kurti".
- Neck: [Boat, Halter, Keyhole, Mandarin, Notch, Paan, Round, Scoop, Shirt, Square, Stylised, Surplice, Sweetheart, Tie - Up, V-neck] — NOTE: Notch = small V-slit in round neck. Round = pure circle with NO slit.
- Occasion: [Daily, Party, Maternity]
- Ornamentation: [Beads & Stones, Embroidered, Lace border, Mirror Work, Pom-Pom, Ruffle, Sequinned, Show Button, Tassels and Latkans, Tie-Ups, Not Applicable]
- Pattern: Overall surface pattern/technique on the kurti.
  [Checked, Chikankari, Colorblocked, Dyed/ Washed, Embellished, Embroidered, Printed, Self-Design, Solid, Striped, Woven Design, Zari Woven]
- PnP: The specific MOTIF or design type. Follow cascade rules STRICTLY:
  • Pattern = Solid → PnP = "Solid"
  • Pattern = Checked → PnP = "Checked"
  • Pattern = Colorblocked → PnP = "Colorblocked"
  • Pattern = Striped → PnP = "Stripe"
  • Pattern = Embellished → PnP = "Embellished"
  • Pattern = Dyed/ Washed → PnP = one of [Leheriya, Shibori, Bandhani, Tie and Dye] — pick most accurate
  • Pattern = Printed → PnP = the SPECIFIC print motif: [Abstract, Animal, Botanical, Chevron, Ethnic Motif, Floral, Geometric, Houndstooth, Ikat, Kalamkari, Micro, Paisley, Polka Dot, Quirky, Tribal, Warli]
  • Pattern = Embroidered / Chikankari / Woven Design / Zari Woven → PnP = "Ethnic Motif" (or the closest matching motif)
  [Abstract, Animal, Bandhani, Botanical, Checked, Chevron, Colorblocked, Embellished, Ethnic Motif, Floral, Geometric, Houndstooth, Ikat, Kalamkari, Leheriya, Micro, Paisley, Polka Dot, Quirky, Shibori, Solid, Stripe, Tie and Dye, Tribal, Warli]
- Sleeve Styling: 
  → Bell: Sleeve flares out widely at the bottom (like a bell). Prefer "Bell" over "Flared" for this shape.
  [Batwing, Bell, Cap, Cape, Cold Shoulder, Cuffed, Cut Out, Extended, Flared, Flutter, Kimono, One Side Sleeve, Puff, Regular, Roll-Up, Shoulder Strap, Sleeveless, Not Available]
- Length: [Above Knee, Ankle Length, Calf Length, Knee length, Not Available] — If folded/packet, output "Not Available"
- Sleeve Length:
  → Sleeveless: No sleeves at all or just straps.
  → Short Sleeves: Sleeve ends above the elbow (includes cap sleeves, half sleeves).
  → Three-Quarter Sleeves: Sleeve ends below the elbow but above the wrist (3/4th length). HINT: If arms are bent and sleeve ends at mid-forearm, it is Three-Quarter.
  → Long Sleeves: Sleeve reaches all the way down to the wrist.
  → Not Available: If the sleeves are completely hidden/folded.
  [Long Sleeves, Short Sleeves, Sleeveless, Three-Quarter Sleeves, Not Available]

━━━ IF CATEGORY = "Men Shirt" ━━━
Extract these EXACT fields with EXACT key names:

- "closure": [Asymmetrical, Symmetric] — Default: "Symmetric" for most shirts.

- "color": Dominant BASE/BACKGROUND fabric color. MUST output a value.
  → If the shirt has a pattern (like Checks, Stripes, Prints) with 3 OR MORE distinct colors → MUST output "Multicolor".
  [Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Multicolor, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Rust, Teal, White, Yellow, Lemon Yellow, Gold, Lavender]

- "hemline": Shape of bottom hem.
  → If the back hem is visibly longer/lower than the front hem → MUST output "High-Low".
  → If shirt is FOLDED, packaged, or hemline NOT visible → output "Curved"
  → If Crop length → output "Curved"
  [Curved, Straight, Asymmetric, High-Low] — Default: "Curved"

- "length": Overall shirt length.
  → If FOLDED / packaged / length unclear → output "Regular"
  → "Longline" only if shirt clearly extends well past hips
  [Regular, Longline, Crop] — Default: "Regular"

- "neck": Collar/neck type.
  → If the collar's color or pattern is noticeably different from the main body of the shirt → MUST output "Contrast Collar".
  [Mandarin, Collarless, Spread Collar, Hood, Contrast Collar]

- "occasion": Best use occasion.
  → Default: "Casual"
  → "Formal" ONLY if shirt is clearly formal (plain solid/self-design, no cargo pockets, worn formally)
  → "Party" if fabric is SATIN / SHINY / metallic-looking
  → If shirt has double cargo pockets OR is Cargo → MUST be "Casual"
  [Casual, Formal, Party]

- "pattern": [Checked, Colorblocked, Dyed/ Washed, Embellished, Printed, Self-Design, Solid, Striped]

- "print_or_pattern_type": Specific motif.
  ⚠️ MANDATORY CASCADE RULES:
    • pattern = Solid → "Solid"
    • pattern = Checked → "Checked"
    • pattern = Colorblocked → "Colorblocked"
    • pattern = Striped → "Horizontal Stripes" or "Vertical Stripes" (pick based on stripe direction)
    • pattern = Dyed/ Washed → "Faded" or "Ombre" only
    • pattern = Self-Design → "Checked" / "Horizontal Stripes" / "Vertical Stripes" / "Solid" (based on self-design detail)
    • pattern = Printed → pick specific motif from list below
  [Abstract, Animal, Back Print, Botanical, Camouflage, Cartoons, Checked, Chevron, Colorblocked, Conversational, Ethnic Motif, Faded, Floral, Geometric, Goa, Graphic Print, Horizontal Stripes, Houndstooth, Micro Print, Newspaper, Ombre, Paisley, Placement Print, Polka Dots, Quirky, Religious Print, Solid, Stripe, Tribal, Typography, Vertical Stripes]

- "sleeve_length":
  → If sleeves NOT VISIBLE (folded, sleeve cut from image) → output "Long Sleeves"
  [Short Sleeves, Long Sleeves, Three-Quarter Sleeves] — Default: "Long Sleeves"

- "sleeve_styling":
  ⚠️ STRICT RULES FOR ROLLED-UP SLEEVES:
    • If sleeves are rolled up AND held by a VISIBLE BUTTON STRAP/TIE (fita) → MUST output "Roll-Up".
    • If sleeves are simply rolled up WITHOUT any strap/tie → MUST output "Cuffed".
    • sleeve_length = Long Sleeves (not rolled) → "Cuffed"
    • sleeve_length = Short or Three-Quarter Sleeves → "Regular"
  [Regular, Roll-Up, Cuffed, Elbow Patches, Doctor Sleeves]

- "fit_shape":
  → If neck = Hood → MUST be "Shackets"
  → If a T-shirt / inner garment is VISIBLY peeking out from under the shirt → "Shirt Over Tshirt"
  → If shirt has TWO large chest/cargo pockets (cargo style) OR is clearly a cargo shirt → "Cargo"
  → Default: "Regular"
  [Regular, Shackets, Shirt Over Tshirt, Cargo]

━━━ IF CATEGORY = "Saree" ━━━
Extract these EXACT fields with EXACT key names as shown:

- "color": Dominant color of the main saree fabric drape
  → HINT: Bright greenish-yellows (like neon or lime) should be classified as "Yellow" or "Lemon Yellow", not Green.
  [Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Multicolor, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Teal, White, Yellow, Lemon Yellow, Gold]

- "Blouse Color": Color of the blouse piece.
  → If blouse is NOT visible or not identifiable → MUST output "Not Available"
  [Same list as color, plus: Not Available]

- "blouse_pattern": Pattern on the blouse.
  ⚠️ CASCADE RULE: If "Blouse Color" = "Not Available" → "blouse_pattern" MUST ALSO be "Not Available"
  → If Blouse print/pattern matches Saree's print/pattern EXACTLY → "Same as Saree"
  → If Blouse border matches Saree's border EXACTLY → "Same as Border"
  → If Blouse print matches Saree's Pallu print EXACTLY → "Same as Pallu"
  [Same as Saree, Same as Border, Same as Pallu, Printed, Embroidered, Embellished, Solid, Sequence, Zari Woven, Not Available, Woven Design]

- "border": Type of border on the saree.
  → Extract the border type EVEN IF the saree is folded, as long as a distinct edge is visible.
  → Do not confuse Printed borders (flat dye on fabric) with Embroidered (raised threadwork). Lace is a separately attached strip.
  → If NO border is visible → output "No Border"
  [No Border, Not Available, Embroidered, Solid, Woven Design, Zari, Embellished, Printed, Lace, Temple Border]

- "border_width": How wide/thick the border looks.
  ⚠️ CASCADE RULE: If "border" = "No Border" → "border_width" MUST ALSO be "No Border"
  → "Small Border": Standard narrow borders (approx 2-5 inches), taking up a small fraction of the drape.
  → "Big Border": Very wide, tall borders taking up a massive portion (15-30%+) of the saree height.
  [No Border, Not Available, Big Border, Small Border]

- "occasion": Best use occasion
  [Daily, Party, Traditional, Celebrity Inspire]

- "ornamentation": Surface embellishments visible on the saree
  → Distinguish carefully: Embroidery is thread, Lace is attached mesh/cutwork, Sequinned/Mirror are shiny additions.
  [Embroidered, Beads & Stones, Mirror Work, Sequinned, Applique, Tassels and Latkans, Ruffle, Lace border, Pom - Pom, Not Applicable]

- "pallu_details": The decorative end piece hanging over the shoulder.
  ⚠️ CRITICAL RULE: If the saree is FOLDED (like a packed rectangle), CROPPED so pallu is not shown, or pallu is simply NOT VISIBLE → output "Not Available". Do NOT guess.
  → If the Pallu has the exact same print/pattern as the rest of the Saree body (no different design at the end) → "Same as Saree"
  → If the Pallu's print/design matches the Saree's border design EXACTLY → "Same as Border"
  [Same as Saree, Same as Border, Embroidered, Solid, Printed, Half & Half, Not Available, Zari Woven, Embellished, Woven Design]

- "pattern": Overall pattern of the main saree body
  [Checked, Colorblocked, Solid, Striped, Embellished, Dyed/ Washed, Printed, Self-Design, Embroidered, Woven Design, Zari Woven, Zari Embroidered]

- "print_or_pattern_type": Specific print motif or design.
  ⚠️ CASCADE RULES (MANDATORY):
    • pattern = Solid → print_or_pattern_type MUST be "Solid"
    • pattern = Checked → print_or_pattern_type MUST be "Checked"
    • pattern = Colorblocked → print_or_pattern_type MUST be "Colorblocked"
    • pattern = Striped → print_or_pattern_type MUST be "Striped"
    • pattern = Embellished → print_or_pattern_type MUST be "Embellished"
    • pattern = Dyed/ Washed → print_or_pattern_type MUST be ONE OF: [Leheriya, Shibori, Batik, Tie and Dye] — pick the most visually accurate
  [Checked, Colorblocked, Solid, Striped, Embellished, Leheriya, Shibori, Batik, Tie and Dye, Abstract, Animal, Bandhani, Chevron, Ethnic Motif, Floral, Geometric, Paisley, Quirky, Tribal, Ikat, Warli, Kalamkari, Houndstooth, Polka Dot, Botanical, Zari butta, Foil, Micro, Butterfly, Nath, Newspaper Print, Peacock, Elephant]

═══════════════════════════════════════════════════════
OUTPUT FORMAT (STRICT)
═══════════════════════════════════════════════════════
Return ONLY a raw JSON ARRAY of N objects. Each object MUST have:
- "_category": "Kurti" or "Saree" (detected category)
- "Reasoning": Brief visual analysis explaining category detection + key classification decisions
- "Confidence": "High" / "Medium" / "Low"
- All fields for the detected category (listed above)
- For fields of OTHER categories, DO NOT include them at all.

Example for a mixed batch:
[
  {"_category": "Kurti", "Reasoning": "...", "Color": "Red", "Fit/Shape": "A-line", ...},
  {"_category": "Saree", "Reasoning": "...", "color": "Green", "Blouse Color": "Matching", "blouse_pattern": "Embroidered", "border": "Zari Border", "border_width": "Small Border", "occasion": "Festive", "ornamentation": "Zari Work", "pallu_details": "Woven", "pattern": "Woven Design", "print_or_pattern_type": "Ethnic Motif"}
]
"""

def download_image(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.meesho.com/',
        'Connection': 'keep-alive'
    }
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

async def analyze_product_images(tasks: List[Dict[str, Any]], user_api_key: str = None):
    """
    Analyzes product images using a smart unified prompt.
    Auto-detects category (Kurti/Saree/etc) per image and returns appropriate fields.
    """
    api_key = user_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return [{"error": "API Key not configured properly in .env"}] * len(tasks)

    # Build system instruction
    sys_inst = SMART_SYSTEM_INSTRUCTION
    
    # Check for any custom prompt (partial attribute override)
    custom_prompts = [t.get("custom_prompt") for t in tasks if t.get("custom_prompt")]
    unique_custom = list(set(custom_prompts))
    custom_prompt_text = unique_custom[0] if unique_custom else None
    if custom_prompt_text:
        sys_inst += f"""

ADDITIONAL USER REQUEST: The user specifically asked about: "{custom_prompt_text}".
Focus extra attention on accurately tagging attributes related to this request. Still output ALL standard fields for the detected category.
"""
    
    # Build image parts
    parts = []
    for i, task in enumerate(tasks):
        img_data = task["data"]
        
        if task["is_url"]:
            img_bytes = download_image(img_data)
            if not img_bytes:
                parts.append({"text": f"Product {i+1}: Image failed to download."})
                continue
        else:
            img_bytes = img_data

        try:
            img = Image.open(io.BytesIO(img_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((1024, 1024))
            out_io = io.BytesIO()
            img.save(out_io, format='JPEG', quality=85)
            b64_img = base64.b64encode(out_io.getvalue()).decode('utf-8')
            
            parts.append({
                "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": b64_img
                }
            })
            parts.append({"text": f"Product {i+1}"})
        except Exception as e:
            print(f"Image processing error for product {i+1}: {e}")
            parts.append({"text": f"Product {i+1}: Invalid image data."})
            
    if not parts:
        return [{"error": "No valid images provided"}] * len(tasks)
        
    parts.append({
        "text": f"Analyze the {len(tasks)} provided products. Detect the category of EACH product independently. Return a JSON ARRAY of exactly {len(tasks)} objects."
    })

    payload = {
        "systemInstruction": {
            "parts": [{"text": sys_inst}]
        },
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status == 429:
                    raise Exception("429 Too Many Requests")
                
                resp_json = await response.json()
                
                if 'error' in resp_json:
                    raise Exception(f"Gemini API Error: {resp_json['error'].get('message', str(resp_json['error']))}")
                    
                text_response = resp_json['candidates'][0]['content']['parts'][0]['text']
                
                try:
                    result_json = json.loads(text_response)
                    if not isinstance(result_json, list):
                        result_json = [result_json]
                        
                    # Pad if AI returned fewer results
                    while len(result_json) < len(tasks):
                        result_json.append({"error": "AI did not return data for this product"})
                        
                    return result_json[:len(tasks)]
                except json.JSONDecodeError:
                    print(f"JSON parse error. Raw response: {text_response[:500]}")
                    return [{"error": "Invalid JSON response from AI", "raw": text_response}] * len(tasks)

    except Exception as e:
        if "429" in str(e):
            return [{"error": "429 Too Many Requests"}] * len(tasks)
        print(f"API Error: {e}")
        return [{"error": str(e)}] * len(tasks)
