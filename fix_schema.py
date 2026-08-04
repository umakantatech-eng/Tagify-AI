import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_generation_block = """
        # Build Schema dynamically using raw dict
        from rules_engine import TAXONOMY
        
        item_schema = {
            "type": "OBJECT",
            "properties": {
                "_visual_analysis": {"type": "STRING"},
                "Color": {"type": "STRING", "enum": TAXONOMY["Color"]},
                "Fit/Shape": {"type": "STRING", "enum": TAXONOMY["Fit/Shape"]},
                "Neck": {"type": "STRING", "enum": TAXONOMY["Neck"]},
                "Occasion": {"type": "STRING", "enum": TAXONOMY["Occasion"]},
                "Ornamentation": {"type": "STRING", "enum": TAXONOMY["Ornamentation"]},
                "Pattern": {"type": "STRING", "enum": TAXONOMY["Pattern"]},
                "PnP": {"type": "STRING", "enum": TAXONOMY["PnP"]},
                "Sleeve Styling": {"type": "STRING", "enum": TAXONOMY["Sleeve Styling"]},
                "Length": {"type": "STRING", "enum": TAXONOMY["Length"]},
                "Sleeve Length": {"type": "STRING", "enum": TAXONOMY["Sleeve Length"]}
            },
            "required": ["_visual_analysis", "Color", "Fit/Shape", "Neck", "Occasion", "Ornamentation", "Pattern", "PnP", "Sleeve Styling", "Length", "Sleeve Length"]
        }
        
        array_schema = {
            "type": "ARRAY",
            "items": item_schema
        }

        def fetch_from_gemini():
            return model.generate_content(
                contents,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=array_schema,
                    temperature=0.0,
                )
            )
"""

old_generation_block_pattern = r'# Build Schema dynamically.*?temperature=0\.0,\s*\)\s*\)'
content = re.sub(old_generation_block_pattern, new_generation_block.strip(), content, flags=re.MULTILINE|re.DOTALL)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
