import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update optimize_image_bytes
content = content.replace("def optimize_image_bytes(img_bytes, max_size=512):", "def optimize_image_bytes(img_bytes, max_size=1024):")

# 2. Add Schema generation to generate_content
new_generation_block = """
        # Build Schema dynamically
        from rules_engine import TAXONOMY
        
        item_schema = genai.types.Schema(
            type=genai.types.Type.OBJECT,
            properties={
                "_visual_analysis": genai.types.Schema(type=genai.types.Type.STRING),
                "Color": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Color"]),
                "Fit/Shape": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Fit/Shape"]),
                "Neck": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Neck"]),
                "Occasion": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Occasion"]),
                "Ornamentation": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Ornamentation"]),
                "Pattern": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Pattern"]),
                "PnP": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["PnP"]),
                "Sleeve Styling": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Sleeve Styling"]),
                "Length": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Length"]),
                "Sleeve Length": genai.types.Schema(type=genai.types.Type.STRING, enum=TAXONOMY["Sleeve Length"]),
            },
            required=["_visual_analysis", "Color", "Fit/Shape", "Neck", "Occasion", "Ornamentation", "Pattern", "PnP", "Sleeve Styling", "Length", "Sleeve Length"]
        )
        
        array_schema = genai.types.Schema(
            type=genai.types.Type.ARRAY,
            items=item_schema
        )

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

old_generation_block = r"""        def fetch_from_gemini\(\):
            return model\.generate_content\(
                contents,
                generation_config=genai\.GenerationConfig\(
                    response_mime_type="application/json",
                    temperature=0\.0,
                \)
            \)"""

content = re.sub(old_generation_block, new_generation_block.strip(), content, flags=re.MULTILINE|re.DOTALL)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
