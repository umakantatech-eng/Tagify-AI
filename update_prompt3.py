import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_prompt = '''You are an Elite Computer Vision AI. Your task is to analyze N provided images as N distinct products.
You MUST output EXACTLY what is in the image, following these strict rules. Do not hallucinate.

### ⚙️ STRICT RULES:
1. FOCUS: Only analyze the main product. If the image is cropped and you cannot see the full length, DO NOT guess. Set "Length" to "Not Available", but STILL output the Fit, Neck, and Sleeves if they are visible!
2. COLOR: Look ONLY at the base fabric color. Ignore embroidery, prints, or borders.
3. PNP & PATTERN: 
   - If it has embroidery, Pattern = "Embroidered" and PnP = Motif (e.g. "Floral", "Ethnic Motif").
   - If it has no print/embroidery, Pattern = "Solid" and PnP = "Solid".
4. SHAPE: 
   - "A-line": Flares out from waist.
   - "Straight": Falls straight down like a column.
   - "Anarkali": Flares immediately from below the bust.
5. NECK: 
   - "Notch": Round or Mandarin collar with a small V-slit in the center.
   - "V-neck": Pure V shape from shoulders down.
6. SLEEVES:
   - "Long Sleeves": Covers the wrist bone.
   - "Three-Quarter Sleeves": Ends between elbow and wrist.
   - "Short Sleeves": Ends above elbow.

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

### 📝 EXAMPLES:
Example 1: A white top folded in a packet.
Output: {{"_visual_analysis":"Folded. Can't see shape.", "Color":"White", "Fit/Shape":"Not Available", "Neck":"Not Available", "Occasion":"Daily", "Ornamentation":"Not Applicable", "Pattern":"Solid", "PnP":"Solid", "Sleeve Styling":"Not Available", "Length":"Not Available", "Sleeve Length":"Not Available"}}

Example 2: A blue kurta. Shoulders visible, bottom is cropped. Has floral print.
Output: {{"_visual_analysis":"Cropped bottom. Length is NA but upper body visible.", "Color":"Blue", "Fit/Shape":"Straight", "Neck":"Round", "Occasion":"Daily", "Ornamentation":"Not Applicable", "Pattern":"Printed", "PnP":"Floral", "Sleeve Styling":"Regular", "Length":"Not Available", "Sleeve Length":"Three-Quarter Sleeves"}}

### 📋 EXACT OUTPUT SCHEMA:
Output ONLY a raw valid JSON ARRAY of N objects for N images.
[
  {
    "_visual_analysis": "Brief step-by-step reasoning...",
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

# Ensure gemini-3.5-flash-lite is set
new_content = re.sub(r"genai\.GenerativeModel\('gemini-.*?'", "genai.GenerativeModel('gemini-3.5-flash-lite'", new_content)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
