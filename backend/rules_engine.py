import re

# ============================================================
# TAXONOMY DEFINITIONS — Add new categories here
# ============================================================

COLORS_COMMON = [
    "Aqua Blue", "Beige", "Black", "Blue", "Brown", "Cream", "Green", "Grey",
    "Maroon", "Mint Green", "Multicolor", "Mustard", "Navy Blue", "Olive",
    "Orange", "Peach", "Pink", "Purple", "Red", "Teal", "White", "Yellow",
    "Lemon Yellow", "Gold"
]

KURTI_TAXONOMY = {
    "Color": COLORS_COMMON,
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

SAREE_TAXONOMY = {
    # ── ORDER MATCHES REQUIRED HEADER ORDER ──

    # 1. Blouse Color
    "Blouse Color": COLORS_COMMON + ["Not Available"],

    # 2. blouse_pattern — "Not Available" if blouse not visible
    "blouse_pattern": [
        "Same as Saree", "Same as Border", "Same as Pallu", "Printed", "Embroidered",
        "Embellished", "Solid", "Sequence", "Zari Woven", "Not Available", "Woven Design"
    ],

    # 3. border
    "border": [
        "No Border", "Not Available", "Embroidered", "Solid", "Woven Design",
        "Zari", "Embellished", "Printed", "Lace", "Temple Border"
    ],

    # 4. border_width
    "border_width": ["No Border", "Not Available", "Big Border", "Small Border"],

    # 5. color
    "color": COLORS_COMMON,

    # 6. occasion
    "occasion": [
        "Daily", "Party", "Traditional", "Celebrity Inspire"
    ],

    # 7. ornamentation
    "ornamentation": [
        "Embroidered", "Beads & Stones", "Mirror Work", "Sequinned",
        "Applique", "Tassels and Latkans", "Ruffle", "Lace border",
        "Pom - Pom", "Not Applicable"
    ],

    # 8. pallu_details
    "pallu_details": [
        "Same as Saree", "Same as Border", "Embroidered", "Solid", "Printed",
        "Half & Half", "Not Available", "Zari Woven", "Embellished", "Woven Design"
    ],

    # 9. pattern
    "pattern": [
        "Checked", "Colorblocked", "Solid", "Striped", "Embellished",
        "Dyed/ Washed", "Printed", "Self-Design", "Embroidered", "Woven Design",
        "Zari Woven", "Zari Embroidered"
    ],

    # 10. print_or_pattern_type
    "print_or_pattern_type": [
        "Checked", "Colorblocked", "Solid", "Striped", "Embellished",
        "Leheriya", "Shibori", "Batik", "Tie and Dye",
        "Abstract", "Animal", "Bandhani", "Chevron", "Ethnic Motif",
        "Floral", "Geometric", "Paisley", "Quirky", "Tribal", "Ikat", "Warli",
        "Kalamkari", "Houndstooth", "Polka Dot", "Botanical",
        "Zari butta", "Foil", "Micro", "Butterfly", "Nath", "Newspaper Print",
        "Peacock", "Elephant"
    ],

    # 11. transparency
    "transparency": ["Yes", "No", "Not Available"]
}

# Master taxonomy registry — add new categories here
CATEGORY_TAXONOMY = {
    "Kurti": KURTI_TAXONOMY,
    "Saree": SAREE_TAXONOMY,
    # "Lehenga": LEHENGA_TAXONOMY,
}


# ============================================================
# TAXONOMY VALUE MATCHING
# ============================================================

def get_nearest_taxonomy_value(key: str, value: str, taxonomy: dict) -> str:
    """Fuzzy match a value against allowed taxonomy values."""
    if key not in taxonomy:
        return value

    valid_values = taxonomy[key]
    val_str = str(value).strip()
    val_lower = val_str.lower()

    if not val_lower or val_lower in ["-", "none", "null", ""]:
        return _default_value(key)

    # Exact match (case insensitive)
    for v in valid_values:
        if v.lower() == val_lower:
            return v

    # Partial / substring match
    for v in valid_values:
        if val_lower in v.lower() or v.lower() in val_lower:
            return v

    return _default_value(key)


def _default_value(key: str) -> str:
    """Return a sensible default when no taxonomy match is found."""
    na_fields = {
        "Length", "Sleeve Length", "Sleeve Styling", "Fit/Shape", "Neck",
        "Blouse_color", "Blouse_pattern", "Pallu_details", "Transparency"
    }
    nb_fields = {"Border", "Border_width"}
    nap_fields = {"Ornamentation"}
    if key in na_fields:
        return "Not Available"
    if key in nb_fields:
        return "No Border"
    if key in nap_fields:
        return "Not Applicable"
    return ""


# ============================================================
# CATEGORY DETECTION
# ============================================================

def is_saree_result(ai_result: dict) -> bool:
    saree_keys = {"color", "Blouse Color", "blouse_pattern", "border",
                  "border_width", "pallu_details", "print_or_pattern_type", "transparency"}
    return bool(saree_keys.intersection(ai_result.keys()))


def _detect_category_from_keys(ai_result: dict) -> str:
    saree_indicators = {"color", "Blouse Color", "blouse_pattern",
                        "pallu_details", "transparency", "print_or_pattern_type"}
    kurti_indicators = {"Fit/Shape", "Neck", "Sleeve Styling", "Sleeve Length", "PnP"}
    result_keys = set(ai_result.keys())
    if len(saree_indicators & result_keys) > len(kurti_indicators & result_keys):
        return "Saree"
    return "Kurti"


# ============================================================
# MAIN VALIDATION ENTRY POINT
# ============================================================

def validate_and_correct(ai_result: dict) -> dict:
    """
    Detects category from AI result and applies category-specific
    validation + hard cascade rules.
    """
    category = ai_result.get("_category", "").strip()
    if category not in CATEGORY_TAXONOMY:
        category = _detect_category_from_keys(ai_result)

    taxonomy = CATEGORY_TAXONOMY.get(category, KURTI_TAXONOMY)

    validated = {"_category": category}

    # Copy non-taxonomy fields (Reasoning, Confidence)
    for k, v in ai_result.items():
        if k not in taxonomy and k != "_category":
            validated[k] = v

    # Map all fields to nearest valid taxonomy value
    for key in taxonomy.keys():
        val = ai_result.get(key, "")
        validated[key] = get_nearest_taxonomy_value(key, val, taxonomy)

    # Apply category-specific hard rules
    if category == "Kurti":
        validated = _apply_kurti_rules(validated)
    elif category == "Saree":
        validated = _apply_saree_rules(validated)

    return validated


# ============================================================
# KURTI HARD RULES
# ============================================================

def _apply_kurti_rules(result: dict) -> dict:
    # Rule 1: Above Knee → Short Kurti
    if result.get("Length") == "Above Knee":
        result["Fit/Shape"] = "Short Kurti"

    # Rule 2: Never use "Straight" — convert to A-line
    if result.get("Fit/Shape") == "Straight":
        result["Fit/Shape"] = "A-line"

    # Rule 3: Pattern → PnP cascade
    pat = result.get("Pattern", "")
    pnp_direct_map = {
        "Solid": "Solid",
        "Checked": "Checked",
        "Striped": "Stripe",
        "Embellished": "Embellished",
        "Colorblocked": "Colorblocked",
    }
    if pat in pnp_direct_map:
        result["PnP"] = pnp_direct_map[pat]
    elif pat == "Dyed/ Washed":
        valid_pnp = ["Tie and Dye", "Leheriya", "Shibori", "Bandhani", "Batik"]
        if result.get("PnP") not in valid_pnp:
            result["PnP"] = "Tie and Dye"

    # Rule 4: Embroidery/Chikankari → Party
    pat_orn = [pat, result.get("Ornamentation", "")]
    is_party = any(t in f for f in pat_orn for t in ["Chikankari", "Embellished", "Embroidered"])
    if is_party:
        result["Occasion"] = "Party"
    elif result.get("Occasion") not in ["Daily", "Party", "Maternity"]:
        result["Occasion"] = "Daily"

    return result


# ============================================================
# SAREE HARD RULES (CASCADE)
# ============================================================

def _apply_saree_rules(result: dict) -> dict:
    # ── RULE 1: "Blouse Color" = Not Available → blouse_pattern = Not Available ──
    if result.get("Blouse Color") == "Not Available":
        result["blouse_pattern"] = "Not Available"

    # ── RULE 2: border cascade ──
    border = result.get("border", "")
    if border in ["No Border", "Not Available", ""]:
        result["border"] = "No Border" if border != "Not Available" else "Not Available"
        result["border_width"] = border if border != "" else "No Border"

    # ── RULE 3: Pallu — normalize to Not Available if not in valid list ──
    pallu = result.get("pallu_details", "")
    valid_pallu = SAREE_TAXONOMY["pallu_details"]
    if pallu not in valid_pallu:
        result["pallu_details"] = "Not Available"

    # ── RULE 4: pattern → print_or_pattern_type cascade ──
    pattern = result.get("pattern", "")
    pnp = result.get("print_or_pattern_type", "")

    pattern_pnp_map = {
        "Solid": "Solid",
        "Checked": "Checked",
        "Colorblocked": "Colorblocked",
        "Striped": "Striped",
        "Embellished": "Embellished",
    }
    if pattern in pattern_pnp_map:
        result["print_or_pattern_type"] = pattern_pnp_map[pattern]
    elif pattern == "Dyed/ Washed":
        valid_dyed = ["Leheriya", "Shibori", "Batik", "Tie and Dye"]
        if pnp not in valid_dyed:
            result["print_or_pattern_type"] = "Tie and Dye"

    # ── RULE 5: occasion normalization ──
    valid_occasions = SAREE_TAXONOMY["occasion"]
    if result.get("occasion") not in valid_occasions:
        orn = result.get("ornamentation", "")
        pat = result.get("pattern", "")
        festive_triggers = ["Embroidered", "Zari", "Sequin", "Sequence", "Embellished", "Beads", "Mirror"]
        if any(t in pat + orn for t in festive_triggers):
            result["occasion"] = "Party"
        else:
            result["occasion"] = "Daily"

    # ── RULE 6: transparency normalization ──
    trans = result.get("transparency", "")
    if trans.lower() in ["true", "yes", "transparent", "sheer", "semi-transparent"]:
        result["transparency"] = "Yes"
    elif trans.lower() in ["false", "no", "opaque", "not transparent"]:
        result["transparency"] = "No"
    elif trans not in ["Yes", "No", "Not Available"]:
        result["transparency"] = "Not Available"

    return result
