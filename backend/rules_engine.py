import re

# ============================================================
# TAXONOMY DEFINITIONS
# ============================================================

COLORS_COMMON = [
    "Aqua Blue", "Beige", "Black", "Blue", "Brown", "Cream", "Green", "Grey",
    "Maroon", "Mint Green", "Multicolor", "Mustard", "Navy Blue", "Olive",
    "Orange", "Peach", "Pink", "Purple", "Red", "Teal", "White", "Yellow",
    "Lemon Yellow", "Gold"
]

KURTI_TAXONOMY = {
    "Color": COLORS_COMMON,
    "Fit/Shape": [
        "A-line", "Anarkali", "Angrakha", "Assymetrical", "Flared", "Gown",
        "High-Slit", "Jacket Kurta", "Kaftan", "Maternity", "Short Kurti",
        "Shrug Kurti", "Straight", "Tiered", "Not Available"
    ],
    "Neck": [
        "Boat", "Halter", "Keyhole", "Mandarin", "Notch", "Paan", "Round",
        "Scoop", "Shirt", "Square", "Stylised", "Surplice", "Sweetheart",
        "Tie - Up", "V-neck", "Not Available"
    ],
    "Occasion": ["Daily", "Party", "Maternity"],
    "Ornamentation": [
        "Beads & Stones", "Embroidered", "Lace border", "Mirror Work",
        "Pom-Pom", "Ruffle", "Sequinned", "Show Button",
        "Tassels and Latkans", "Tie-Ups", "Not Applicable"
    ],
    "Pattern": [
        "Checked", "Chikankari", "Colorblocked", "Dyed/ Washed", "Embellished",
        "Embroidered", "Printed", "Self-Design", "Solid", "Striped",
        "Woven Design", "Zari Woven", "Not Available"
    ],
    "PnP": [
        "Abstract", "Animal", "Bandhani", "Botanical", "Checked", "Chevron",
        "Colorblocked", "Embellished", "Ethnic Motif", "Floral", "Geometric",
        "Houndstooth", "Ikat", "Kalamkari", "Leheriya", "Micro", "Paisley",
        "Polka Dot", "Quirky", "Shibori", "Solid", "Stripe", "Tie and Dye",
        "Tribal", "Warli", "Not Available"
    ],
    "Sleeve Styling": [
        "Batwing", "Bell", "Cap", "Cape", "Cold Shoulder", "Cuffed",
        "Cut Out", "Extended", "Flared", "Flutter", "Kimono",
        "One Side Sleeve", "Puff", "Regular", "Roll-Up",
        "Shoulder Strap", "Sleeveless", "Not Available"
    ],
    "Length": [
        "Above Knee", "Ankle Length", "Calf Length", "Knee length", "Not Available"
    ],
    "Sleeve Length": [
        "Long Sleeves", "Short Sleeves", "Sleeveless",
        "Three-Quarter Sleeves", "Not Available"
    ]
}

SAREE_TAXONOMY = {
    "Blouse Color": COLORS_COMMON + ["Not Available"],
    "blouse_pattern": [
        "Same as Saree", "Same as Border", "Same as Pallu",
        "Printed", "Embroidered", "Embellished", "Solid",
        "Sequence", "Zari Woven", "Not Available", "Woven Design"
    ],
    "border": [
        "No Border", "Not Available", "Embroidered", "Solid",
        "Woven Design", "Zari", "Embellished", "Printed", "Lace", "Temple Border"
    ],
    "border_width": ["No Border", "Not Available", "Big Border", "Small Border"],
    "color": COLORS_COMMON,
    "occasion": ["Daily", "Party", "Traditional", "Celebrity Inspire"],
    "ornamentation": [
        "Embroidered", "Beads & Stones", "Mirror Work", "Sequinned",
        "Applique", "Tassels and Latkans", "Ruffle", "Lace border",
        "Pom - Pom", "Not Applicable"
    ],
    "pallu_details": [
        "Same as Saree", "Same as Border", "Embroidered", "Solid",
        "Printed", "Half & Half", "Not Available", "Zari Woven",
        "Embellished", "Woven Design"
    ],
    "pattern": [
        "Checked", "Colorblocked", "Solid", "Striped", "Embellished",
        "Dyed/ Washed", "Printed", "Self-Design", "Embroidered",
        "Woven Design", "Zari Woven", "Zari Embroidered"
    ],
    "print_or_pattern_type": [
        "Checked", "Colorblocked", "Solid", "Striped", "Embellished",
        "Leheriya", "Shibori", "Batik", "Tie and Dye",
        "Abstract", "Animal", "Bandhani", "Chevron", "Ethnic Motif",
        "Floral", "Geometric", "Paisley", "Quirky", "Tribal", "Ikat", "Warli",
        "Kalamkari", "Houndstooth", "Polka Dot", "Botanical",
        "Zari butta", "Foil", "Micro", "Butterfly", "Nath",
        "Newspaper Print", "Peacock", "Elephant"
    ]
}

CATEGORY_TAXONOMY = {
    "Kurti": KURTI_TAXONOMY,
    "Saree": SAREE_TAXONOMY,
}


# ============================================================
# COLOR ALIAS MAP — common AI color names → taxonomy values
# ============================================================
COLOR_ALIASES = {
    # Exact alias → taxonomy value
    "multicolour": "Multicolor",
    "multi color": "Multicolor",
    "multi-color": "Multicolor",
    "multi colour": "Multicolor",
    "multi-colour": "Multicolor",
    "light blue": "Aqua Blue",
    "sky blue": "Blue",
    "light green": "Mint Green",
    "lime": "Lemon Yellow",
    "lime green": "Lemon Yellow",
    "neon yellow": "Lemon Yellow",
    "dark green": "Green",
    "bottle green": "Green",
    "dark blue": "Navy Blue",
    "royal blue": "Blue",
    "baby pink": "Pink",
    "hot pink": "Pink",
    "magenta": "Pink",
    "lavender": "Purple",
    "violet": "Purple",
    "dark red": "Maroon",
    "wine": "Maroon",
    "burgundy": "Maroon",
    "off white": "Cream",
    "off-white": "Cream",
    "ivory": "Cream",
    "khaki": "Beige",
    "camel": "Beige",
    "nude": "Beige",
    "charcoal": "Grey",
    "silver": "Grey",
    "copper": "Gold",
    "dark grey": "Grey",
    "light grey": "Grey",
    "dark brown": "Brown",
    "tan": "Brown",
    "chocolate": "Brown",
    "turquoise": "Teal",
    "cyan": "Aqua Blue",
    "coral": "Orange",
    "rust": "Orange",
    "peach orange": "Peach",
    "skin": "Peach",
    "salmon": "Peach",
    "fluorescent": "Yellow",
    "yellow green": "Lemon Yellow",
    "mustard yellow": "Mustard",
    "dark yellow": "Mustard",
    "golden yellow": "Mustard",
    "olive green": "Olive",
    "army green": "Olive",
    "military green": "Olive",
    "golden": "Gold",
    "dark orange": "Orange",
}

# Color name → taxonomy value prefix map for partial matching
# Order matters: more specific entries must come before generic ones
COLOR_SAFE_SUBSTRINGS = {
    "aqua": "Aqua Blue",
    "mint": "Mint Green",
    "navy": "Navy Blue",
    "mustard": "Mustard",
    "olive": "Olive",
    "lemon": "Lemon Yellow",
    "maroon": "Maroon",
    "peach": "Peach",
    "teal": "Teal",
    "cream": "Cream",
    "beige": "Beige",
    "gold": "Gold",
    "pink": "Pink",
    "blue": "Blue",
    "green": "Green",
    "red": "Red",
    "black": "Black",
    "white": "White",
    "grey": "Grey",
    "gray": "Grey",
    "brown": "Brown",
    "orange": "Orange",
    "yellow": "Yellow",
    "purple": "Purple",
}


def get_nearest_taxonomy_value(key: str, value: str, taxonomy: dict) -> str:
    """Strict taxonomy matching with alias support for Color fields."""
    if key not in taxonomy:
        return value

    valid_values = taxonomy[key]
    val_str = str(value).strip()
    val_lower = val_str.lower()

    # Empty / null → default
    if not val_lower or val_lower in {"-", "none", "null", "n/a", "na", "not applicable", ""}:
        if val_lower in {"not applicable"}:
            return "Not Applicable"
        return _default_value(key)

    # 1. Exact match (case insensitive)
    for v in valid_values:
        if v.lower() == val_lower:
            return v

    # 2. Color fields: use alias map first (no false partial matches)
    if key in {"Color", "color", "Blouse Color"}:
        # Check alias map
        if val_lower in COLOR_ALIASES:
            alias_result = COLOR_ALIASES[val_lower]
            if alias_result in valid_values:
                return alias_result

        # Check if any valid color name is exactly in the value (e.g. "Dark Pink" → "Pink")
        # Use safe-substring map with priority ordering
        for substr, mapped_color in COLOR_SAFE_SUBSTRINGS.items():
            if substr in val_lower and mapped_color in valid_values:
                # Avoid false: "Mint Green" should not match "Green" first
                # Prefer longer match
                return mapped_color

        # Multicolor as last resort for color fields
        if "multicolor" in val_lower or "multicolour" in val_lower or "multi" in val_lower:
            return "Multicolor"

        return _default_value(key)

    # 3. Non-color fields: exact substring match (longer target values first to avoid greedy short matches)
    sorted_valid = sorted(valid_values, key=lambda x: -len(x))
    for v in sorted_valid:
        if v.lower() == val_lower:
            return v

    for v in sorted_valid:
        if val_lower in v.lower() or v.lower() in val_lower:
            return v

    return _default_value(key)


def _default_value(key: str) -> str:
    """Return a sensible default when no taxonomy match is found."""
    na_fields = {
        "Color", "color", "Fit/Shape", "Neck", "Sleeve Styling",
        "Length", "Sleeve Length", "Occasion", "Pattern", "PnP",
        "Blouse Color", "blouse_pattern", "border_width",
        "pallu_details", "print_or_pattern_type"
    }
    nb_fields = {"border"}
    nap_fields = {"Ornamentation", "ornamentation"}

    if key in na_fields:
        return "Not Available"
    if key in nb_fields:
        return "No Border"
    if key in nap_fields:
        return "Not Applicable"
    return "Not Available"


# ============================================================
# CATEGORY DETECTION
# ============================================================

def _detect_category_from_keys(ai_result: dict) -> str:
    saree_indicators = {
        "color", "Blouse Color", "blouse_pattern",
        "pallu_details", "print_or_pattern_type", "border"
    }
    kurti_indicators = {"Fit/Shape", "Neck", "Sleeve Styling", "Sleeve Length", "PnP"}
    result_keys = set(ai_result.keys())
    saree_score = len(saree_indicators & result_keys)
    kurti_score = len(kurti_indicators & result_keys)
    if saree_score > kurti_score:
        return "Saree"
    return "Kurti"


# ============================================================
# MAIN VALIDATION ENTRY POINT
# ============================================================

def validate_and_correct(ai_result: dict) -> dict:
    """
    Detects category from AI result, maps all values to nearest taxonomy,
    then applies hard cascade rules.
    """
    category = ai_result.get("_category", "").strip()
    if not category or category not in CATEGORY_TAXONOMY:
        category = _detect_category_from_keys(ai_result)
    if category not in CATEGORY_TAXONOMY:
        category = "Kurti"

    taxonomy = CATEGORY_TAXONOMY[category]
    validated = {"_category": category}

    # Preserve non-taxonomy meta fields
    for k, v in ai_result.items():
        if k not in taxonomy and k != "_category":
            validated[k] = v

    # Map every taxonomy field
    for key in taxonomy.keys():
        raw_val = ai_result.get(key, "")
        validated[key] = get_nearest_taxonomy_value(key, raw_val, taxonomy)

    # Apply hard rules
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

    # Rule 2: Straight → A-line
    if result.get("Fit/Shape") == "Straight":
        result["Fit/Shape"] = "A-line"

    # Rule 3: Pattern → PnP strict cascade
    pat = result.get("Pattern", "")
    pnp = result.get("PnP", "")

    PATTERN_PNP_MAP = {
        "Solid": "Solid",
        "Checked": "Checked",
        "Striped": "Stripe",
        "Embellished": "Embellished",
        "Colorblocked": "Colorblocked",
        "Woven Design": "Ethnic Motif",
        "Zari Woven": "Ethnic Motif",
        "Embroidered": "Ethnic Motif",
        "Chikankari": "Ethnic Motif",
    }

    if pat in PATTERN_PNP_MAP:
        result["PnP"] = PATTERN_PNP_MAP[pat]
    elif pat == "Dyed/ Washed":
        valid_pnp_dyed = {"Tie and Dye", "Leheriya", "Shibori", "Bandhani"}
        if pnp not in valid_pnp_dyed:
            result["PnP"] = "Tie and Dye"
    elif pat == "Printed":
        # For Printed, PnP should be the specific motif — keep AI value if valid
        valid_pnp_printed = {
            "Abstract", "Animal", "Bandhani", "Botanical", "Chevron",
            "Ethnic Motif", "Floral", "Geometric", "Houndstooth", "Ikat",
            "Kalamkari", "Leheriya", "Micro", "Paisley", "Polka Dot",
            "Quirky", "Shibori", "Tie and Dye", "Tribal", "Warli"
        }
        if pnp not in valid_pnp_printed:
            result["PnP"] = "Floral"   # default for printed

    # Rule 4: Occasion logic
    if pat in {"Chikankari", "Embroidered", "Zari Woven"}:
        result["Occasion"] = "Party"
    elif pat == "Embellished":
        result["Occasion"] = "Party"
    elif result.get("Occasion") not in {"Daily", "Party", "Maternity"}:
        result["Occasion"] = "Daily"

    return result


# ============================================================
# SAREE HARD RULES (CASCADE)
# ============================================================

def _apply_saree_rules(result: dict) -> dict:
    # Rule 1: Blouse Not Available → blouse_pattern Not Available
    if result.get("Blouse Color") == "Not Available":
        result["blouse_pattern"] = "Not Available"

    # Rule 2: Border cascade
    border = result.get("border", "")
    if border == "No Border":
        result["border_width"] = "No Border"
    elif not border or border == "Not Available":
        result["border"] = "No Border"
        result["border_width"] = "No Border"

    # Rule 3: Pallu normalization
    pallu = result.get("pallu_details", "")
    valid_pallu = set(SAREE_TAXONOMY["pallu_details"])
    if pallu not in valid_pallu:
        result["pallu_details"] = "Not Available"

    # Rule 4: pattern → print_or_pattern_type cascade
    pattern = result.get("pattern", "")
    pnp = result.get("print_or_pattern_type", "")

    PATTERN_PNP_MAP = {
        "Solid": "Solid",
        "Checked": "Checked",
        "Colorblocked": "Colorblocked",
        "Striped": "Striped",
        "Embellished": "Embellished",
    }

    if pattern in PATTERN_PNP_MAP:
        result["print_or_pattern_type"] = PATTERN_PNP_MAP[pattern]
    elif pattern == "Dyed/ Washed":
        valid_dyed = {"Leheriya", "Shibori", "Batik", "Tie and Dye"}
        if pnp not in valid_dyed:
            result["print_or_pattern_type"] = "Shibori"
        # Tie and Dye → Shibori per business rule
        elif pnp == "Tie and Dye":
            result["print_or_pattern_type"] = "Shibori"
    elif pnp == "Tie and Dye":
        # Anywhere Tie and Dye appears for Saree → Shibori
        result["print_or_pattern_type"] = "Shibori"

    # Rule 5: Occasion — only override if invalid
    valid_occasions = set(SAREE_TAXONOMY["occasion"])
    current_occ = result.get("occasion", "")
    if current_occ not in valid_occasions:
        if pattern in {"Printed", "Solid", "Striped", "Checked", "Dyed/ Washed"}:
            result["occasion"] = "Daily"
        else:
            result["occasion"] = "Party"

    return result
