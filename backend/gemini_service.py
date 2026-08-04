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

SYSTEM_INSTRUCTION = """Expert AI for Kurtis. Analyze N images as N distinct products.
Rules per product:
1. Color: MAIN fabric base color only. Ignore border/print. CRITICAL: Distinguish carefully between 'Blue' and 'Navy Blue'. If the fabric is a very dark shade of blue, you MUST output 'Navy Blue'. If the garment is heavily split between two or more distinct, highly contrasting colors (e.g., side panels vs center panel), output 'Multicolour'.
2. FOLDED RULE: If the kurti is physically folded up (like a rectangular packet) so the full body/flare is hidden, Fit/Shape and Length MUST be 'Not Available'. Do not guess A-line just because the folded edges are straight. If it is fully spread out flat on a floor/bed, extract normally.
3. Pattern & PnP Rules:
   - "Solid" Pattern: If the main body fabric is plain/solid, Pattern="Solid" and PnP="Solid". BUT if there is embroidery on the chest/neck, you MUST set Pattern="Embroidered" and PnP="Motif" (like Ethnic Motif).
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
- V-neck: The fabric is cut in straight diagonal lines from the shoulders down to the chest, forming a strict 'V'. NO round collar at the back/top.
- Notch: Has a small, sharp V-shaped slit in the front center of an otherwise round neck. It does NOT need to have a collar at the back. DO NOT call this Round.
- Round: A perfectly continuous circular curve. If there is ANY tiny V-cut or slit, it is NOT Round, it is Notch.
- Mandarin: A short stand-up collar going around the neck, with NO deep V-slit. (If it has a V-slit, call it Notch).
- Sweetheart: Curved neckline that looks like the top half of a heart (two curves meeting at the chest).
- Keyhole: A closed neck with a distinct hole (circle or teardrop) cut out below the collar.
- Boat: Very wide neckline passing horizontally near the collarbones, sitting wide on the shoulders.
- Square: A neckline with straight horizontal and vertical lines forming sharp 90-degree corners. DO NOT call this round.
- Tie - Up: Any neckline that features strings, cords, or ribbons used to tie it together at the front. If there are strings, it is Tie - Up.
- Stylised: A complex, unique, or designer neckline that doesn't fit standard simple shapes (e.g., overlapping flaps, intricate cutouts).
Sleeve Styling:
- Bell: Flaring out wide at the bottom/cuff like a bell shape. If the sleeve noticeably widens at the end, choose Bell (prefer Bell over Flared for wide cuffs).
- Flared: Only use if the ENTIRE sleeve is extremely loose from the shoulder down. If it's normal at the shoulder but wide at the wrist, it is Bell.
Sleeve Length:
- Long Sleeves: Reaching all the way down to the wrist bone.
- Three-Quarter Sleeves: Ending below the elbow but well above the wrist, exposing the lower forearm. DO NOT confuse Long and Three-Quarter.

CRITICAL ACCURACY STEP: You MUST perform a visual analysis before classifying.

Output ONLY raw JSON ARRAY of N objects.
Fields & STRICT allowed values:
Color: Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Multicolour, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Teal, White, Yellow
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

async def analyze_product_images(tasks: List[Dict[str, Any]], user_api_key: str = None):
    api_key = user_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return [{"error": "API Key not configured properly in .env"}] * len(tasks)

    custom_prompts = [t.get("custom_prompt") for t in tasks if t.get("custom_prompt")]
    unique_custom = list(set(custom_prompts))
    custom_prompt_text = unique_custom[0] if unique_custom else None
    
    sys_inst = SYSTEM_INSTRUCTION
    if custom_prompt_text:
        sys_inst += f"""

CRITICAL OVERRIDE RULE: The user specifically requested: "{custom_prompt_text}".
You MUST ONLY analyze and extract the specific attributes mentioned in the user's request.
For ALL OTHER attributes that the user did NOT ask for, you MUST set their value to exactly "-" without any analysis.
Do not waste time extracting or outputting anything the user did not explicitly ask for! This is a strict requirement."""
    
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
            # We don't need to open with PIL anymore since we just base64 it, but let's compress it if needed
            # For simplicity, we just base64 encode the raw bytes. If they are large, we might want PIL compression.
            # We'll use PIL just to ensure it's a valid image and convert to JPEG to save bandwidth.
            img = Image.open(io.BytesIO(img_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Compress to standard 1024 max size
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
            parts.append({"text": f"Product {i+1}: Invalid image data."})
            
    if not parts:
        return [{"error": "No valid images provided"}] * len(tasks)
        
    parts.append({"text": f"Analyze the {len(tasks)} provided products according to the system instructions and return a JSON ARRAY containing {len(tasks)} objects."})

    payload = {
        "systemInstruction": {
            "parts": [{"text": sys_inst}]
        },
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={'Content-Type': 'application/json'}) as response:
                if response.status == 429:
                    # Specific exception for rate limits to handle in main.py
                    raise Exception("429 Too Many Requests")
                
                resp_json = await response.json()
                
                if 'error' in resp_json:
                    raise Exception(f"Gemini API Error: {resp_json['error'].get('message', str(resp_json['error']))}")
                    
                text_response = resp_json['candidates'][0]['content']['parts'][0]['text']
                
                try:
                    result_json = json.loads(text_response)
                    if not isinstance(result_json, list):
                        result_json = [result_json]
                        
                    while len(result_json) < len(tasks):
                        result_json.append({"error": "AI did not return data for this product"})
                        
                    return result_json[:len(tasks)]
                except json.JSONDecodeError:
                    return [{"error": "Invalid JSON response from AI", "raw": text_response}] * len(tasks)

    except Exception as e:
        if "429" in str(e):
            return [{"error": "429 Too Many Requests"}] * len(tasks)
        print(f"API Error: {e}")
        return [{"error": str(e)}] * len(tasks)
