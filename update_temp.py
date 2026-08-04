import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r'generation_config=genai.GenerationConfig\(\s*response_mime_type="application/json",\s*\)',
    'generation_config=genai.GenerationConfig(response_mime_type="application/json", temperature=0.0)',
    content
)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
