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
        "fields": ["Saree_color", "Blouse_color", "Blouse_pattern", "Border", "Border_width", "Occasion", "Ornamentation", "Pallu_details", "Pattern", "Print_and_pattern", "Transparency"],
        "description": "A traditional Indian draped garment consisting of a long unstitched cloth, worn with a blouse piece."
    }
    # To add a new category e.g. Lehenga:
    # "Lehenga": {
    #     "fields": ["Color", "Pattern", "Occasion", "Ornamentation", ...],
    #     "description": "..."
    # }
}

# ============================================================
# UNIFIED SMART SYSTEM PROMPT
# ============================================================
SMART_SYSTEM_INSTRUCTION = """You are an expert AI product tagger for Indian fashion e-commerce. You will analyze N garment images.

═══════════════════════════════════════════════════════
STEP 1: IDENTIFY CATEGORY (for each image independently)
═══════════════════════════════════════════════════════
Look at the garment and pick ONE category:
- "Kurti": A short/long Indian top garment (kurta/kurti). Worn as a top. Has sleeves, neckline, body length.
- "Saree": A traditional long draped cloth worn with a blouse. Has a pallu, border, and drape.

═══════════════════════════════════════════════════════
STEP 2: EXTRACT ATTRIBUTES based on detected category
═══════════════════════════════════════════════════════

━━━ IF CATEGORY = "Kurti" ━━━
Extract these EXACT fields:
- Color: Main fabric base color [Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Multicolour, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Teal, White, Yellow]
- Fit/Shape: [A-line, Anarkali, Angrakha, Assymetrical, Flared, Gown, High-Slit, Jacket Kurta, Kaftan, Maternity, Short Kurti, Shrug Kurti, Tiered] — NOTE: Classify any straight-cut as "A-line". If length is Above Knee → "Short Kurti".
- Neck: [Boat, Halter, Keyhole, Mandarin, Notch, Paan, Round, Scoop, Shirt, Square, Stylised, Surplice, Sweetheart, Tie - Up, V-neck] — NOTE: Notch = small V-slit in round neck. Round = pure circle with NO slit.
- Occasion: [Daily, Party, Maternity]
- Ornamentation: [Beads & Stones, Embroidered, Lace border, Mirror Work, Pom-Pom, Ruffle, Sequinned, Show Button, Tassels and Latkans, Tie-Ups, Not Applicable]
- Pattern: [Checked, Chikankari, Colorblocked, Dyed/ Washed, Embellished, Embroidered, Printed, Self-Design, Solid, Striped, Woven Design, Zari Woven]
- PnP: [Abstract, Animal, Bandhani, Botanical, Checked, Chevron, Colorblocked, Embellished, Ethnic Motif, Floral, Geometric, Houndstooth, Ikat, Kalamkari, Leheriya, Micro, Paisley, Polka Dot, Quirky, Shibori, Solid, Stripe, Tie and Dye, Tribal, Warli]
- Sleeve Styling: [Batwing, Bell, Cap, Cape, Cold Shoulder, Cuffed, Cut Out, Extended, Flared, Flutter, Kimono, One Side Sleeve, Puff, Regular, Roll-Up, Shoulder Strap, Sleeveless, Not Available]
- Length: [Above Knee, Ankle Length, Calf Length, Knee length, Not Available] — If folded/packet, output "Not Available"
- Sleeve Length: [Long Sleeves, Short Sleeves, Sleeveless, Three-Quarter Sleeves, Not Available]

━━━ IF CATEGORY = "Saree" ━━━
Extract these EXACT fields with EXACT key names as shown:

- "color": Dominant color of the main saree fabric drape
  [Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Multicolor, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Teal, White, Yellow, Lemon Yellow, Gold]

- "Blouse Color": Color of the blouse piece.
  → If blouse is NOT visible or not identifiable → MUST output "Not Available"
  [Same list as color, plus: Not Available]

- "blouse_pattern": Pattern on the blouse.
  ⚠️ CASCADE RULE: If "Blouse Color" = "Not Available" → "blouse_pattern" MUST ALSO be "Not Available"
  [Same as Saree, Same as Border, Same as Pallu, Printed, Embroidered, Embellished, Solid, Sequence, Zari Woven, Not Available, Woven Design]

- "border": Type of border on the saree.
  → If NO border is visible → output "No Border"
  [No Border, Not Available, Embroidered, Solid, Woven Design, Zari, Embellished, Printed, Lace, Temple Border]

- "border_width": How wide/thick the border looks.
  ⚠️ CASCADE RULE: If "border" = "No Border" → "border_width" MUST ALSO be "No Border"
  [No Border, Not Available, Big Border, Small Border]

- "occasion": Best use occasion
  [Daily, Party, Traditional, Celebrity Inspire]

- "ornamentation": Surface embellishments visible on the saree
  [Embroidered, Beads & Stones, Mirror Work, Sequinned, Applique, Tassels and Latkans, Ruffle, Lace border, Pom - Pom, Not Applicable]

- "pallu_details": The decorative end piece hanging over the shoulder.
  ⚠️ CRITICAL RULE: If the saree is FOLDED (like a packed rectangle), CROPPED so pallu is not shown, or pallu is simply NOT VISIBLE → output "Not Available". Do NOT guess.
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

- "transparency": Is the fabric see-through?
  → "Yes" = clearly transparent/sheer fabric (georgette, chiffon, net)
  → "No" = opaque fabric (silk, cotton, crepe)
  → "Not Available" = cannot determine from image
  [Yes, No, Not Available]

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
  {"_category": "Saree", "Reasoning": "...", "color": "Green", "Blouse Color": "Matching", "blouse_pattern": "Embroidered", "border": "Zari Border", "border_width": "Small Border", "occasion": "Festive", "ornamentation": "Zari Work", "pallu_details": "Woven", "pattern": "Woven Design", "print_or_pattern_type": "Ethnic Motif", "transparency": "No"}
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
