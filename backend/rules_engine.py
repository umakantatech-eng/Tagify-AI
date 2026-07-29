import re

# Taxonomy Definition
TAXONOMY = {
    "Color": ["Aqua Blue", "Beige", "Black", "Blue", "Brown", "Cream", "Green", "Grey", "Maroon", "Mint Green", "Mustard", "Navy Blue", "Olive", "Orange", "Peach", "Pink", "Purple", "Red", "Teal", "White", "Yellow"],
    "Fit/Shape": ["A-line", "Anarkali", "Angrakha", "Assymetrical", "Flared", "Gown", "High-Slit", "Jacket Kurta", "Kaftan", "Maternity", "Short Kurti", "Shrug Kurti", "Straight", "Tiered", "Not Available"],
    "Neck": ["Boat", "Halter", "Keyhole", "Mandarin", "Notch", "Paan", "Round", "Scoop", "Shirt", "Square", "Stylised", "Surplice", "Sweetheart", "Tie - Up", "V-neck", "Not Available"],
    "Occasion": ["Daily", "Party", "Maternity"],
    "Ornamentation": ["Beads & Stones", "Embroidered", "Lace border", "Mirror Work", "Pom-Pom", "Ruffle", "Sequinned", "Show Button", "Tassels and Latkans", "Tie-Ups", "Not Applicable"],
    "Pattern": ["Checked", "Chikankari", "Colorblocked", "Dyed/ Washed", "Embellished", "Embroidered", "Printed", "Self-Design", "Solid", "Striped", "Woven Design", "Zari Woven", "Not Available"],
    "PnP": ["Abstract", "Animal", "Bandhani", "Botanical", "Checked", "Chevron", "Colorblocked", "Embellished", "Ethnic Motif", "Floral", "Geometric", "Houndstooth", "Ikat", "Kalamkari", "Leheriya", "Micro", "Paisley", "Polka Dot", "Quirky", "Shibori", "Solid", "Stripe", "Tie and Dye", "Tribal", "Warli", "Not Available"],
    "Sleeve Styling": ["Batwing", "Bell", "Cap", "Cape", "Cold Shoulder", "Cuffed", "Cut Out", "Extended", "Flared", "Flutter", "Kimono", "One Side Sleeve", "Puff", "Regular", "Roll-Up", "Shoulder Strap", "Sleeveless", "Not Available"],
    "Length": ["Above Knee", "Ankle Length", "Calf Length", "Knee length", "Not Available"],
    "Sleeve Length": ["Long Sleeves", "Short Sleeves", "Sleeveless", "Three-Quarter Sleeves", "Not Available"]
}

def get_nearest_taxonomy_value(key, value):
    if key not in TAXONOMY:
        return value
    
    valid_values = TAXONOMY[key]
    val_lower = str(value).strip().lower()
    
    # Exact match (case insensitive)
    for valid_val in valid_values:
        if valid_val.lower() == val_lower:
            return valid_val
            
    # Substring match as fallback
    for valid_val in valid_values:
        if val_lower in valid_val.lower() or valid_val.lower() in val_lower:
            return valid_val
            
    # Default if no match found
    if key in ["Length", "Sleeve Length", "Sleeve Styling", "Ornamentation", "Fit/Shape"]:
        return "Not Available" if key != "Ornamentation" else "Not Applicable"
        
    return "" 


def validate_and_correct(ai_result):
    """
    Takes the raw JSON output from AI and applies all rules.
    """
    validated_result = {}
    
    # 1. Map to nearest taxonomy
    for key in TAXONOMY.keys():
        val = ai_result.get(key, "")
        validated_result[key] = get_nearest_taxonomy_value(key, val)
        
    # Copy over non-taxonomy fields if any
    for k, v in ai_result.items():
        if k not in TAXONOMY:
            validated_result[k] = v
            
    # ---------------------------------------------------------
    # Hard Rules Enforcement (User specific constraints)
    # ---------------------------------------------------------
    
    # Rule 1: Folded Kurti
    # Handled by prompt, but if Length is Not Available due to fold, maybe force others
    
    # Rule 2: If Length is Above Knee, Fit/Shape MUST be Short Kurti
    if validated_result.get("Length") == "Above Knee":
        validated_result["Fit/Shape"] = "Short Kurti"
        
    # Rule 3: Pattern -> PnP matching for Solid, Checked, Striped, Embellished
    pat = validated_result.get("Pattern", "")
    if pat == "Solid":
        validated_result["PnP"] = "Solid"
    elif pat == "Checked":
        validated_result["PnP"] = "Checked"
    elif pat == "Striped":
        validated_result["PnP"] = "Stripe"
    elif pat == "Embellished":
        validated_result["PnP"] = "Embellished"
    elif pat == "Dyed/ Washed":
        valid_pnp = ["Tie and Dye", "Leheriya", "Batik", "Shibori", "Bandhani"]
        if validated_result.get("PnP") not in valid_pnp:
            validated_result["PnP"] = "Tie and Dye"
            
    # Rule 4: Occasion Rule
    # If Pattern or Ornamentation is Chikankari, Embellished, or Embroidered -> Party
    pat_orn = [pat, validated_result.get("Ornamentation", "")]
    party_keywords = ["Chikankari", "Embellished", "Embroidered"]
    
    # Check if any keyword matches
    is_party = False
    for p in pat_orn:
        if p and any(keyword in p for keyword in party_keywords):
            is_party = True
            break
            
    if is_party:
        validated_result["Occasion"] = "Party"
    else:
        # If it's not a party keyword, ensure it's Daily or Maternity
        if validated_result.get("Occasion") not in ["Daily", "Maternity"]:
            validated_result["Occasion"] = "Daily"
            
    return validated_result
