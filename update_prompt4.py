import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_prompt = '''You are an Elite Computer Vision AI. Your task is to analyze N provided images as N distinct products.
You MUST output EXACTLY what is in the image, following these strict visual rules. Do not hallucinate.

### ⚙️ STRICT RULES FOR 200% ACCURACY:

1. CROPPED IMAGE RULE:
- If the image is cropped and you CANNOT see the bottom hem (length), set "Length" to "Not Available".
- CRITICAL: Even if the length is cropped, if you can see the sleeves, YOU MUST PREDICT Sleeve Length and Sleeve Style. Do NOT set them to Not Available just because Length is Not Available.

2. COLOR RULE:
- Look ONLY at the MAIN BASE FABRIC color. 
- Ignore the color of prints, embroidery, borders, or tassels.
- If it has completely different colored large panels (like half red, half black), output "Multicolour". Otherwise, choose the single most dominant background color.

3. PATTERN & PNP RULE:
- IF the fabric has no print/embroidery -> Pattern="Solid", PnP="Solid".
- IF there is embroidery -> Pattern="Embroidered", PnP=Motif (e.g. "Floral", "Ethnic Motif").
- IF Pattern="Printed" -> PnP MUST BE the motif (e.g. "Geometric", "Floral"). PnP cannot be "Solid".

4. FIT / SHAPE RULE:
- "A-line": Starts widening from the waist down in an 'A' shape. Also use this for "Straight" kurtis that fall straight down.
- "Anarkali": Fits tightly at the bust, then massive flare starts IMMEDIATELY BELOW the bust (empire waist).
- "Short Kurti": Hem ends above the knee.

5. NECK RULE:
- "Notch": A round or mandarin collar at the back, but with a small V-shaped slit in the front center.
- "V-neck": Pure V shape from the shoulders down. No round collar at the back.
- "Round": Perfect circle curve.

6. SLEEVE LENGTH RULE:
- "Long Sleeves": Reaches and covers the wrist bone.
- "Three-Quarter Sleeves": Ends anywhere between the elbow and the wrist bone.
- "Short Sleeves": Ends above elbow.

7. SLEEVE STYLE RULE:
- "Regular": Normal straight sleeve.
- "Bell": Normal at shoulder, but noticeably widens/flares out at the wrist opening.

### 👗 ALLOWED VALUES (Choose ONLY from these):
- Color: Aqua Blue, Beige, Black, Blue, Brown, Cream, Green, Grey, Maroon, Mint Green, Mustard, Navy Blue, Olive, Orange, Peach, Pink, Purple, Red, Teal, White, Yellow, Multicolour
- Fit/Shape: A-line, Anarkali, Angrakha, Assymetrical, Flared, Gown, High-Slit, Jacket Kurta, Kaftan, Maternity, Short Kurti, Shrug Kurti, Straight, Tiered, Not Available
- Neck: Boat, Halter, Keyhole, Mandarin, Notch, Paan, Round, Scoop, Shirt, Square, Stylised, Surplice, Sweetheart, Tie - Up, V-neck, Not Available
- Occasion: Daily, Party, Maternity
- Ornamentation: Beads & Stones, Embroidered, Lace border, Mirror Work, Pom-Pom, Ruffle, Sequinned, Show Button, Tassels and Latkans, Tie-Ups, Not Applicable
- Pattern: Checked, Chikankari, Colorblocked, Dyed/ Washed, Embellished, Embroidered, Printed, Self-Design, Solid, Striped, Woven Design, Zari Woven
- PnP: Abstract, Animal, Bandhani, Botanical, Checked, Chevron, Colorblocked, Embellished, Ethnic Motif, Floral, Geometric, Houndstooth, Ikat, Kalamkari, Leheriya, Micro, Paisley, Polka Dot, Quirky, Shibori, Solid, Stripe, Tie and Dye, Tribal, Warli
- Sleeve Styling: Batwing, Bell, Cap, Cape, Cold Shoulder, Cuffed, Cut Out, Extended, Flared, Flutter, Kimono, One Side Sleeve, Puff, Regular, Roll-Up, Shoulder Strap, Sleeveless, Not Available
- Length: Above Knee, Ankle Length, Calf Length, Knee length, Not Available
- Sleeve Length: Long Sleeves, Short Sleeves, Sleeveless, Three-Quarter Sleeves, Not Available

### 📋 EXACT OUTPUT SCHEMA:
Output ONLY a raw valid JSON ARRAY of N objects for N images. No markdown formatting.
[
  {
    "_visual_analysis": "Brief step-by-step reasoning for all 5 rules...",
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
'''

# Replace prompt
new_content = re.sub(r'SYSTEM_INSTRUCTION = """(.*?)"""', f'SYSTEM_INSTRUCTION = """\n{new_prompt}\n"""', content, flags=re.DOTALL)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
