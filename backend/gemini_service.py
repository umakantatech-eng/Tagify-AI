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

SYSTEM_INSTRUCTION = """Expert AI for Kurtis. Analyze N images as N distinct products.
Rules per product:
1. Color: MAIN fabric base color only. Ignore border/print.
2. FOLDED RULE: ONLY if the kurti is physically folded up so the full body/length is hidden -> Not Available. If it is fully spread out flat on a floor/bed, you MUST extract the actual Fit/Shape, Length, and Sleeve Length normally.
3. Pattern & PnP Rules:
   - "Solid" Pattern: If the main body fabric is plain/solid, Pattern="Solid" and PnP="Solid". Mirror work, embroidery, or prints ONLY at the neck/border do NOT change the pattern.
   - Strict Matching: Solid->Solid, Striped->Stripe, Checked->Checked, Embellished->Embellished.
4. Fit & Length Rules:
   - If Length is 'Above Knee', Fit/Shape MUST be 'Short Kurti'.
   - A-line vs Straight: CRITICAL: The user has explicitly requested to classify ANY Straight kurti as 'A-line'. Therefore, DO NOT use 'Straight' for Fit/Shape. If it falls straight down, classify it as 'A-line'.

DEFINITIONS FOR ACCURACY (STRICT ADHERENCE REQUIRED):
Fit/Shape:
- Short Kurti: Kurti that ends above the knee.
- A-line: Flared from waist forming an 'A' shape, OR any straight cut top to bottom. (Merge all Straight into A-line).
- Straight: DO NOT USE. Classify all straight kurtis as 'A-line'.
Neck:
- Boat: Wide neckline passing near the collarbones.
- Notch: A round or mandarin collar with a distinct V-cut or slit in the front center (often with tie-ups). DO NOT call this Round.
- V-neck: A clean, deep or shallow V shape, coming to a point at the chest. No extra collars. DO NOT call this Round.
- Round: A simple circular curve. If there is ANY V-cut or split, it is NOT Round, it is Notch.
Sleeve Styling:
- Bell: Normal at the top, but flaring out wide SPECIFICALLY at the bottom/cuff like a bell shape. DO NOT confuse with Flared.
- Flared: Loosely widening continuously throughout the ENTIRE sleeve length.
Sleeve Length:
- Long Sleeves: Reaching all the way down to the wrist bone.
- Three-Quarter Sleeves: Ending below the elbow but well above the wrist, exposing the lower forearm. DO NOT confuse Long and Three-Quarter.

CRITICAL ACCURACY STEP: You MUST perform a visual analysis before classifying.

Output ONLY raw JSON ARRAY of N objects.
Fields & STRICT allowed values:
Color: Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Teal, White, Yellow
Fit/Shape: A-line, Anarkali, Angrakha, Assymetrical, Flared, Gown, High-Slit, Jacket Kurta, Kaftan, Maternity, Short Kurti, Shrug Kurti, Straight, Tiered
Neck: Boat, Halter, Keyhole, Mandarin, Notch, Paan, Round, Scoop, Shirt, Square, Stylised, Surplice, Sweetheart, Tie - Up, V-neck
Occasion: Daily, Party, Maternity
Ornamentation: Beads & Stones, Embroidered, Lace border, Mirror Work, Pom-Pom, Ruffle, Sequinned, Show Button, Tassels and Latkans, Tie-Ups, Not Applicable
Pattern: Checked, Chikankari, Colorblocked, Dyed/ Washed, Embellished, Embroidered, Printed, Self-Design, Solid, Striped, Woven Design, Zari Woven
PnP: Abstract, Animal, Bandhani, Botanical, Checked, Chevron, Colorblocked, Embellished, Ethnic Motif, Floral, Geometric, Houndstooth, Ikat, Kalamkari, Leheriya, Micro, Paisley, Polka Dot, Quirky, Shibori, Solid, Stripe, Tie and Dye, Tribal, Warli
Sleeve Styling: Batwing, Bell, Cap, Cape, Cold Shoulder, Cuffed, Cut Out, Extended, Flared, Flutter, Kimono, One Side Sleeve, Puff, Regular, Roll-Up, Shoulder Strap, Sleeveless, Not Available
Length: Above Knee, Ankle Length, Calf Length, Knee length, Not Available
Sleeve Length: Long Sleeves, Short Sleeves, Sleeveless, Three-Quarter Sleeves, Not Available
Confidence: High/Medium/Low
Format exactly: [{"Reasoning":"Analyze Neck (is there a V-cut?), Sleeves (wrist or forearm? bell or flared?), and Shape (straight or triangle?)","Color":"..","Fit/Shape":"..","Neck":"..","Occasion":"..","Ornamentation":"..","Pattern":"..","PnP":"..","Sleeve Styling":"..","Length":"..","Sleeve Length":"..","Confidence":".."}]
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
    
    for i, task in enumerate(tasks):
        img_data = task["data"]
        
        if task["is_url"]:
            img_bytes = download_image(img_data)
            if not img_bytes: 
                contents.append(f"Product {i+1}: Image failed to download.")
                continue
        else:
            img_bytes = img_data

        try:
            img = Image.open(io.BytesIO(img_bytes))
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
        response = await asyncio.to_thread(fetch_from_gemini)
        
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
