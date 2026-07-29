import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
import io
import requests
from PIL import Image
from dotenv import load_dotenv
import asyncio

load_dotenv()

SYSTEM_INSTRUCTION = """You are an Elite Enterprise-Grade Computer Vision AI for E-Commerce Fashion Cataloging (Indian Ethnic Wear & Apparel).
Your task is to analyze N provided images as N distinct products to generate 100% precise tags following strict taxonomy, body landmark visual cues, and visual texture definitions.

---

### ⚙️ EXECUTION ALGORITHM (Follow Sequentially):

STEP 1 [IMAGE SELECTION RULE]: 
- Primary focus is the main product image.
- Switch to Image 2 ONLY IF Image 1 clearly shows the BACK SIDE (peeth) of the model/garment. Otherwise, ignore extra images.

STEP 2 [BASE COLOR RULE]: 
- Extract the MAIN FABRIC BASE COLOR ONLY.
- IGNORE colors of prints, embroidery, zari, borders, tassels, or buttons.

STEP 3 [CROPPED / FOLDED / VISIBILITY RULE]:
- Inspect if bottom hem, sleeve openings, and sleeve shoulders are fully visible.
- IF garment length is cut off by photo frame -> "Length": "Not Available".
- CRITICAL: Do NOT mark other attributes as "Not Available" just because the hem/length is cropped. If the upper body is visible, you MUST predict Fit/Shape, Neck, Pattern, etc. If the sleeves are visible, you MUST predict Sleeve Length and Styling. Only mark the specific hidden part as "Not Available".

STEP 4 [PATTERN & PNP DEPENDENCY RULES]:
- IF Pattern == "Solid" -> PnP MUST BE "Solid".
- IF Pattern == "Embroidered" or Pattern == "Embellished" -> PnP MUST describe the motif (e.g., "Floral", "Ethnic Motif", "Geometric"). PnP CANNOT be "Solid".
- IF Pattern == "Dyed/ Washed" -> PnP MUST BE ONE OF ["Tie and Dye", "Bandhani", "Leheriya", "Shibori"]
- IF Pattern == "Striped" -> PnP MUST BE "Stripe"
- IF Pattern == "Checked" -> PnP MUST BE "Checked"
- IF Pattern == "Printed" -> PnP MUST BE a specific motif (e.g., "Floral", "Geometric", "Paisley", etc.). It MUST NOT be empty or "-".

---

### 👗 VISUAL LANDMARK & SHAPE DEFINITIONS (STRICT TAXONOMY):

#### 1. Fit/Shape (Visual Landmarks):
CRITICAL VISUAL DIFFERENCE FOR ANARKALI vs A-LINE vs STRAIGHT:
- "Anarkali": Fitted at chest ONLY (bust line tak fitted). Heavy gathers/kalis flare starts IMMEDIATELY BELOW THE BUST LINE (empire waistline).
- "A-line": Looks like a narrow column at the top, but the lower half (waist se niche) has a widening flare forming an 'A' shape.
- "Straight": Uniform straight vertical fall (uniform column) from bust/waist to hemline WITHOUT any waist curve/flare. Regular side slits start at hip level.

Other Shapes:
- "Angrakha": Overlapping diagonal front panels crossing chest and tying at the side with strings/tassels.
- "Assymetrical": Hemline is visibly uneven, slanted, or high-low (front short, back long).
- "Flared": Fitted at chest AND waist; wide voluminous flare starts strictly FROM WAIST LINE downwards.
- "Gown": Full floor-length continuous flared silhouette without side slits.
- "High-Slit": Side slits start high near waist or ribcage (well above hip level).
- "Jacket Kurta": Kurta with an attached or overlay outer jacket.
- "Kaftan": Loose, boxy robe-like tunic with wide wing-like flowing sides attached to armhole/side seam.
- "Maternity": Extra fabric volume/gathers around belly area, often with concealed nursing zippers.
- "Short Kurti": Hemline ends above mid-thigh or around hip level.
- "Shrug Kurti": Kurta with attached lightweight open shrug overlay.
- "Tiered": Multiple horizontal gathered layers/panels stacked top-to-bottom from waist/hip downwards.
- "Not Available": Folded or hidden.

#### 2. Neck (Geometric Cut Landmarks):
- "Boat": Wide across collarbones horizontally, shallow depth in front.
- "Halter": Fabric straps wrap or tie behind neck, leaving shoulders completely bare.
- "Keyhole": Closed/high neckline featuring a small teardrop or circular cutout on upper chest.
- "Mandarin": Short stand-up band collar encircling the neck (Chinese collar).
- "Notch": Round or Mandarin collar featuring a sharp small vertical 'V' slit cut at central front. (Do NOT confuse Notch with V-neck. V-neck is a full V shape from the shoulders down).
- "Paan": Betel-leaf shape — wide curved top tapering smoothly down to a sharp central bottom point.
- "Round": Standard circular curve around neck base.
- "Scoop": Deep, wide U-shaped curve exposing upper chest.
- "Shirt": Fold-over collar with front button placket (formal shirt style).
- "Square": Horizontal straight bottom edge with two 90-degree vertical side edges.
- "Stylised": Unconventional, asymmetrical, or custom designer cut neckline.
- "Surplice": Diagonal overlapping crossover panels forming a natural V neck.
- "Sweetheart": Curved top edges mimicking top half of a heart over bust.
- "Tie - Up": Neckline with attached fabric strings tied into a bow or knot.
- "V-neck": Two straight lines sloping downwards meeting at a central sharp point.
- "Not Available"

#### 3. Length (Height Landmarks):
- "Above Knee": Hemline ends above kneecap.
- "Knee length": Hemline ends directly at kneecap.
- "Calf Length": Hemline ends between knee and ankle (mid-calf level).
- "Ankle Length": Hemline touches or ends near ankle bone.
- "Not Available": Hemline is cropped out of image frame or folded.

#### 4. Sleeve Length (Arm Landmarks):
CRITICAL: Watch the wrist bone carefully!
- "Sleeveless": Armhole completely exposed; no sleeve fabric covering arm.
- "Short Sleeves": Ends above elbow (bicep/mid-arm level).
- "Three-Quarter Sleeves": Ends ANYWHERE between the elbow and the wrist bone. Even if it is lower forearm, it MUST be Three-Quarter Sleeves.
- "Long Sleeves": MUST physically touch or cover the wrist joint/palm. Do NOT output Long Sleeves if any wrist skin is visible below the sleeve.
- "Not Available": Arms/sleeves cropped out or folded.

#### 5. Sleeve Styling:
- "Batwing": Loose underarm seam extending wide from wrist down to waist.
- "Bell": Fitted at upper arm, flaring wide outwards towards sleeve opening.
- "Cap": Covers only shoulder joint, extremely short length.
- "Cape": Loose fabric draped over shoulders hanging like a cape overlay.
- "Cold Shoulder": Cutout hole exposing shoulder cap while sleeve fabric continues down arm.
- "Cuffed": Fitted fabric band/cuff encircling wrist or sleeve opening.
- "Cut Out": Patterned slits or design cutouts on sleeve fabric.
- "Extended": Shoulder seam drops down past natural shoulder line.
- "Flared": Sleeve widens outwards continuously from armhole.
- "Flutter": Short, ruffled/wavy gathered loose sleeve.
- "Kimono": Wide, loose, continuous sleeve integrated from shoulder to opening.
- "One Side Sleeve": Single shoulder sleeve; opposite shoulder fully bare.
- "Puff": Gathered fabric creating puffed volume at shoulder or cuff.
- "Regular": Standard straight fitted sleeve contouring arm.
- "Roll-Up": Sleeve fabric rolled up and held with a button tab strap.
- "Shoulder Strap": Thin vertical straps holding top without full shoulder coverage.
- "Sleeveless": No sleeve attached.
- "Not Available": Sleeves hidden, cropped, or folded.

#### 6. Ornamentation (Surface Texture & Embellishment Cues):
- "Beads & Stones": 3D shiny/colored beads, rhinestones, or artificial pearls glued/stitched onto fabric.
- "Embroidered": Thread work stitched onto fabric forming raised decorative motifs (zari, silk, or cotton thread).
- "Lace border": Decorative net, crochet, or fabric borders stitched along hem, neck, or sleeve edges.
- "Mirror Work": Small reflective glass or shiny plastic pieces secured with embroidery thread.
- "Pom-Pom": Small fluffy fabric/thread balls attached along borders or necklines.
- "Ruffle": Gathered or pleated fabric strips creating frills along hem, neck, or sleeves.
- "Sequinned": Flat shiny metallic or plastic discs (sitaare) stitched onto fabric for shimmer.
- "Show Button": Decorative buttons placed purely for visual design (non-functional placket).
- "Tassels and Latkans": Hanging bunches of threads, beads, or fabric ornaments attached to neck/side strings.
- "Tie-Ups": Fabric strings or dori tied together forming bows/knots.
- "Not Applicable": Completely plain fabric surface with zero surface decorations, threads, or attachments.

#### 7. Pattern (Fabric Creation Technique Cues):
- "Checked": Intersecting horizontal and vertical lines forming a grid of squares.
- "Chikankari": Traditional white-on-white or soft pastel intricate thread embroidery.
- "Colorblocked": Large solid patches of different distinct colors joined together.
- "Dyed/ Washed": Ombre gradient shade transitions, tie-dye wash.
- "Embellished": Surface decorated heavily with 3D elements like sequins, mirrors, beads, or stones.
- "Embroidered": Raised needlework stitched onto fabric surface with colored or metallic thread.
- "Printed": Flat ink design printed directly onto fabric surface.
- "Self-Design": Pattern woven into fabric using same color yarn creating subtle raised texture/relief.
- "Solid": Single uniform color throughout without any prints, design, or decorations.
- "Striped": Parallel straight lines (vertical, horizontal, or diagonal).
- "Woven Design": Pattern created directly during fabric weaving using different colored yarns.
- "Zari Woven": Metallic gold/silver metallic thread patterns woven directly into fabric (Banarasi style).

#### 8. PnP (Print & Pattern Motif Cues):
["Abstract", "Animal", "Bandhani", "Botanical", "Checked", "Chevron", "Colorblocked", "Embellished", "Ethnic Motif", "Floral", "Geometric", "Houndstooth", "Ikat", "Kalamkari", "Leheriya", "Micro", "Paisley", "Polka Dot", "Quirky", "Shibori", "Solid", "Stripe", "Tie and Dye", "Tribal", "Warli"]

#### 9. Color (Base Fabric Only):
["Aqua Blue", "Beige", "Black", "Blue", "Brown", "Cream", "Green", "Grey", "Maroon", "Mint Green", "Mustard", "Navy Blue", "Olive", "Orange", "Peach", "Pink", "Purple", "Red", "Teal", "White", "Yellow", "Multicolour"]

#### 10. Occasion:
["Daily", "Party", "Maternity"]

---

### 📝 FEW-SHOT EXAMPLES (For Edge Cases):
Example 1: A white kurti folded up inside a transparent plastic bag.
Output: {{"_visual_analysis":"STEP 1: Main product. STEP 2: White. STEP 3: Garment is folded in packet. Shoulders and hem not visible. STEP 4: Solid.", "Color":"White", "Fit/Shape":"Not Available", "Neck":"Not Available", "Occasion":"Daily", "Ornamentation":"Not Applicable", "Pattern":"Solid", "PnP":"Solid", "Sleeve Styling":"Not Available", "Length":"Not Available", "Sleeve Length":"Not Available"}}

Example 2: A dark blue kurti where the front center has bright geometric shapes. Neck has a V-slit in a round collar.
Output: {{"_visual_analysis":"STEP 1: Main product. STEP 2: Multicolour due to heavy contrast. STEP 3: Flare visible. STEP 4: Notch neck detected.", "Color":"Multicolour", "Fit/Shape":"A-line", "Neck":"Notch", "Occasion":"Daily", "Ornamentation":"Not Applicable", "Pattern":"Printed", "PnP":"Geometric", "Sleeve Styling":"Regular", "Length":"Calf Length", "Sleeve Length":"Three-Quarter Sleeves"}}

Example 3: A black kurti with heavy golden embroidery around the neck. The neck is round at the top but has a sharp V-cut in the middle.
Output: {{"_visual_analysis":"STEP 1: Main product. STEP 2: Black. STEP 3: Full garment visible. STEP 4: Notch neck detected.", "Color":"Black", "Fit/Shape":"Straight", "Neck":"Notch", "Occasion":"Party", "Ornamentation":"Embroidered", "Pattern":"Embroidered", "PnP":"Solid", "Sleeve Styling":"Regular", "Length":"Knee length", "Sleeve Length":"Three-Quarter Sleeves"}}

Example 4: A kurti that fits closely at the bust and waist, but then visibly widens and flares outwards from the waist downwards forming an A shape.
Output: {{"_visual_analysis":"STEP 1: Main product. STEP 2: Identified base color. STEP 3: Flare starts strictly from waist down, forming A shape -> A-line (not Straight, not Anarkali). STEP 4: Floral print detected.", "Color":"Red", "Fit/Shape":"A-line", "Neck":"Round", "Occasion":"Daily", "Ornamentation":"Not Applicable", "Pattern":"Printed", "PnP":"Floral", "Sleeve Styling":"Regular", "Length":"Calf Length", "Sleeve Length":"Three-Quarter Sleeves"}}

---

### 📋 EXACT OUTPUT SCHEMA & COLUMN ORDER:

Output ONLY raw valid JSON ARRAY of N objects corresponding to the N input images. No markdown code blocks, no preamble. 
Must include `_visual_analysis` for internal step-by-step landmark verification, followed by exact columns:
[
  {
    "_visual_analysis": "STEP 1: Image view check... STEP 2: Base color check... STEP 3: Flare origin check... STEP 4: Ornamentation/Pattern texture check... STEP 5: Sleeve & Hem visibility check...",
    "Color": "...",
    "Fit/Shape": "...",
    "Neck": "...",
    "Occasion": "...",
    "Ornamentation": "...",
    "Pattern": "...",
    "PnP": "...",
    "Sleeve Styling": "...",
    "Length": "...",
    "Sleeve Length": "..."
  }
]
"""

def get_gemini_model(user_api_key=None, custom_prompt=None):
    api_key = user_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("Please configure your GEMINI_API_KEY in the .env file")
        return None
        
    genai.configure(api_key=api_key)
    
    sys_inst = SYSTEM_INSTRUCTION
    if custom_prompt:
        sys_inst += f"""
        
CRITICAL OVERRIDE RULE: The user specifically requested: "{custom_prompt}".
You MUST ONLY analyze and extract the specific attributes mentioned in the user's request. 
For ALL OTHER attributes that the user did NOT ask for, you MUST set their value to exactly "-" without any analysis.
Do not waste time extracting or outputting anything the user did not explicitly ask for! This is a strict requirement.
"""

    try:
        model = genai.GenerativeModel('gemini-3.5-flash-lite', system_instruction=sys_inst)
        return model
    except Exception as e:
        print(f"Error initializing model: {e}")
        return None

def download_image(url):
    # Spoof a real browser to prevent Meesho/CDN from detecting the bot
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

def optimize_image_bytes(img_bytes, max_size=512):
    try:
        with Image.open(io.BytesIO(img_bytes)) as img:
            # Convert to RGB if necessary (e.g. RGBA/PNG)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Resize if it's larger than max_size
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return img_bytes

async def analyze_product_images(tasks: List[Dict[str, Any]], user_api_key: str = None):
    """
    tasks: list of dicts like [{"job_id": "...", "data": "url_or_bytes", "is_url": True}]
    """
    custom_prompts = [t.get("custom_prompt") for t in tasks if t.get("custom_prompt")]
    unique_custom = list(set(custom_prompts))
    custom_prompt_text = unique_custom[0] if unique_custom else None
    
    model = get_gemini_model(user_api_key, custom_prompt_text)
    if not model:
        return [{"error": "API Key not configured properly in .env"}] * len(tasks)

    contents = []
    download_coroutines = []
    
    for t in tasks:
        if t["is_url"]:
            download_coroutines.append(asyncio.to_thread(download_image, t["data"]))
        else:
            async def return_bytes(b): return b
            download_coroutines.append(return_bytes(t["data"]))
            
    print(f"Starting concurrent download of {len(tasks)} images...")
    try:
        downloaded_bytes_list = await asyncio.gather(*download_coroutines)
        print("Downloads completed.")
    except Exception as e:
        print(f"Error during concurrent download: {e}")
        return [{"error": f"Download failed: {e}"}] * len(tasks)
    
    for i, (task, img_bytes) in enumerate(zip(tasks, downloaded_bytes_list)):
        if task["is_url"] and not img_bytes:
            contents.append(f"Product {i+1}: Image failed to download.")
            continue
            
        try:
            # Apply Nano-optimization (resize & compress) before sending to Gemini
            optimized_bytes = optimize_image_bytes(img_bytes)
            img = Image.open(io.BytesIO(optimized_bytes))
            contents.append(img)
            contents.append(f"Product {i+1}")
        except Exception as e:
            contents.append(f"Product {i+1}: Invalid image data.")
            
    if not contents:
        return [{"error": "No valid images provided"}] * len(tasks)
        
    contents.append(f"Analyze the {len(tasks)} provided products according to the system instructions and return a JSON ARRAY containing {len(tasks)} objects.")
    try:
        def fetch_from_gemini():
            return model.generate_content(
                contents,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
        
        # Run synchronous generate_content in a separate thread so it doesn't block the FastAPI event loop
        print("Sending payload to Gemini API...")
        response = await asyncio.to_thread(fetch_from_gemini)
        print("Received response from Gemini API.")
        
        try:
            result_json = json.loads(response.text)
            # Ensure it's a list
            if not isinstance(result_json, list):
                result_json = [result_json]
                
            # Pad or truncate to match tasks length just in case AI messes up
            while len(result_json) < len(tasks):
                result_json.append({"error": "AI did not return data for this product"})
                
            return result_json[:len(tasks)]
            
        except json.JSONDecodeError:
            print("Failed to parse JSON:", response.text)
            return [{"error": "Invalid JSON response from AI", "raw": response.text}] * len(tasks)
            
    except Exception as e:
        print(f"API Error: {e}")
        return [{"error": str(e)}] * len(tasks)
