import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

lock_import = "import asyncio\nfrom typing import List, Dict, Any"
content = content.replace("from typing import List, Dict, Any", lock_import)

# Create global lock
lock_init = "import asyncio\n\napi_lock = asyncio.Lock()\n"
content = content.replace("import asyncio\n\nload_dotenv()", f"{lock_init}\nload_dotenv()")

# Add lock around model config and generation
target_block = """
    model = get_gemini_model(user_api_key, custom_prompt_text)
    if not model:
        return [{"error": "API Key not configured properly in .env"}] * len(tasks)

    contents = []
"""

replacement_block = """
    contents = []
"""
content = content.replace(target_block, replacement_block)

target_gen = """
    try:
        def fetch_from_gemini():
            return model.generate_content(
                contents,
                generation_config=genai.GenerationConfig(response_mime_type="application/json", temperature=0.0)
            )
        
        # Run synchronous generate_content in a separate thread so it doesn't block the FastAPI event loop
        response = await asyncio.to_thread(fetch_from_gemini)
"""

replacement_gen = """
    try:
        async with api_lock:
            model = get_gemini_model(user_api_key, custom_prompt_text)
            if not model:
                return [{"error": "API Key not configured properly in .env"}] * len(tasks)
                
            def fetch_from_gemini():
                return model.generate_content(
                    contents,
                    generation_config=genai.GenerationConfig(response_mime_type="application/json", temperature=0.0)
                )
            
            # Run synchronous generate_content in a separate thread so it doesn't block the FastAPI event loop
            response = await asyncio.to_thread(fetch_from_gemini)
"""
content = content.replace(target_gen, replacement_gen)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
