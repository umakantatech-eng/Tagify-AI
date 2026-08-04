import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the imports and remove api_lock
new_imports = """
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
"""
content = re.sub(r'import os.*?load_dotenv\(\)', new_imports.strip(), content, flags=re.DOTALL)

# Find get_gemini_model and replace it with raw API execution logic
raw_http_logic = """
async def analyze_product_images(tasks: List[Dict[str, Any]], user_api_key: str = None):
    api_key = user_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return [{"error": "API Key not configured properly in .env"}] * len(tasks)

    custom_prompts = [t.get("custom_prompt") for t in tasks if t.get("custom_prompt")]
    unique_custom = list(set(custom_prompts))
    custom_prompt_text = unique_custom[0] if unique_custom else None
    
    sys_inst = SYSTEM_INSTRUCTION
    if custom_prompt_text:
        sys_inst += f"\\n\\nCRITICAL OVERRIDE RULE: The user specifically requested: \\\"{custom_prompt_text}\\\".\\nYou MUST ONLY analyze and extract the specific attributes mentioned in the user's request.\\nFor ALL OTHER attributes that the user did NOT ask for, you MUST set their value to exactly \\\"-\\\" without any analysis.\\nDo not waste time extracting or outputting anything the user did not explicitly ask for! This is a strict requirement."
    
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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
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
"""

# Replace everything from def get_gemini_model to the end
content = re.sub(r'def get_gemini_model.*', raw_http_logic.strip(), content, flags=re.DOTALL)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
