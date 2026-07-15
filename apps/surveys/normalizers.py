import re

# ---------------------------------------------------------------------------
# Panel brand → (tier_label, panel_tier, tier_order)
# tier_order: 1=standard, 2=premium, 3=premium-plus
# ---------------------------------------------------------------------------

PANEL_BRAND_MAP = {
    # Premium-plus
    "sunpower": ("SunPower Maxeon", "premium-plus", 3),
    "sunpower maxeon": ("SunPower Maxeon", "premium-plus", 3),
    "maxeon": ("SunPower Maxeon", "premium-plus", 3),
    # Premium
    "lg": ("LG NeON", "premium", 2),
    "lg neon": ("LG NeON", "premium", 2),
    "panasonic": ("Panasonic EverVolt", "premium", 2),
    "evervolt": ("Panasonic EverVolt", "premium", 2),
    "rec": ("REC Alpha", "premium", 2),
    "rec alpha": ("REC Alpha", "premium", 2),
    "silfab": ("Silfab Prime", "premium", 2),
    "solaria": ("Solaria PowerXT", "premium", 2),
    "qcells": ("Q CELLS Q.PEAK DUO", "premium", 2),
    "q cells": ("Q CELLS Q.PEAK DUO", "premium", 2),
    "q.peak": ("Q CELLS Q.PEAK DUO", "premium", 2),
    "hanwha q cells": ("Q CELLS Q.PEAK DUO", "premium", 2),
    # Standard
    "longi": ("LONGi Hi-MO", "standard", 1),
    "longi solar": ("LONGi Hi-MO", "standard", 1),
    "jinko": ("Jinko Tiger Neo", "standard", 1),
    "jinko solar": ("Jinko Tiger Neo", "standard", 1),
    "canadian solar": ("Canadian Solar HiKu", "standard", 1),
    "canadian": ("Canadian Solar HiKu", "standard", 1),
    "risen": ("Risen Energy RSM", "standard", 1),
    "hanwha": ("Hanwha Q CELLS", "standard", 1),
    "trina": ("Trina Solar Vertex", "standard", 1),
    "trina solar": ("Trina Solar Vertex", "standard", 1),
    "ja solar": ("JA Solar DeepBlue", "standard", 1),
    "ja": ("JA Solar DeepBlue", "standard", 1),
    "axitec": ("Axitec AXIpremium", "standard", 1),
    "mission solar": ("Mission Solar Energy", "standard", 1),
}

# Size bands: (min_watts_threshold, label)
SIZE_BAND_MAP = [
    (12000, "12 kW+"),
    (8000, "8-12 kW"),
    (5000, "5-8 kW"),
    (0, "3-5 kW"),
]

METRO_MAP = {
    ("San Francisco", "CA"): "San Francisco Bay Area",
    ("San Jose", "CA"): "San Francisco Bay Area",
    ("Oakland", "CA"): "San Francisco Bay Area",
    ("Sacramento", "CA"): "Sacramento Metro",
    ("Los Angeles", "CA"): "Los Angeles Metro",
    ("Santa Monica", "CA"): "Los Angeles Metro",
    ("San Diego", "CA"): "San Diego Metro",
    ("Phoenix", "AZ"): "Phoenix Metro",
    ("Scottsdale", "AZ"): "Phoenix Metro",
    ("Tucson", "AZ"): "Tucson Metro",
    ("Houston", "TX"): "Houston Metro",
    ("Dallas", "TX"): "Dallas Metro",
    ("Fort Worth", "TX"): "Dallas Metro",
    ("Austin", "TX"): "Austin Metro",
    ("Denver", "CO"): "Denver Metro",
    ("Boulder", "CO"): "Denver Metro",
    ("Miami", "FL"): "Miami Metro",
    ("Orlando", "FL"): "Orlando Metro",
    ("Tampa", "FL"): "Tampa Metro",
    ("Jacksonville", "FL"): "Jacksonville Metro",
    ("New York", "NY"): "New York Metro",
    ("Brooklyn", "NY"): "New York Metro",
    ("Newark", "NJ"): "New York Metro",
    ("Jersey City", "NJ"): "New York Metro",
    ("Boston", "MA"): "Boston Metro",
    ("Cambridge", "MA"): "Boston Metro",
    ("Portland", "OR"): "Portland Metro",
    ("Seattle", "WA"): "Seattle Metro",
    ("Chicago", "IL"): "Chicago Metro",
    ("Atlanta", "GA"): "Atlanta Metro",
    ("Charlotte", "NC"): "Charlotte Metro",
    ("Raleigh", "NC"): "Raleigh Metro",
    ("Minneapolis", "MN"): "Twin Cities Metro",
}

CITY_ALIASES = {
    "sf": ("San Francisco", "CA"),
    "la": ("Los Angeles", "CA"),
    "nyc": ("New York", "NY"),
    "phx": ("Phoenix", "AZ"),
    "bay area": ("San Francisco", "CA"),
}

STATE_ALIASES = {
    "ca": ("", "CA"), "california": ("", "CA"),
    "tx": ("", "TX"), "texas": ("", "TX"),
    "fl": ("", "FL"), "florida": ("", "FL"),
    "az": ("", "AZ"), "arizona": ("", "AZ"),
    "ny": ("", "NY"), "new york": ("", "NY"),
    "nj": ("", "NJ"), "new jersey": ("", "NJ"),
    "ma": ("", "MA"), "massachusetts": ("", "MA"),
    "co": ("", "CO"), "colorado": ("", "CO"),
    "or": ("", "OR"), "oregon": ("", "OR"),
    "wa": ("", "WA"), "washington": ("", "WA"),
    "nc": ("", "NC"), "north carolina": ("", "NC"),
    "ga": ("", "GA"), "georgia": ("", "GA"),
    "il": ("", "IL"), "illinois": ("", "IL"),
    "mn": ("", "MN"), "minnesota": ("", "MN"),
}


def normalize_panel_brand(raw_brand: str) -> tuple[str, str, int]:
    """Return (panel_tier_label, panel_tier, tier_order).

    Falls back to (raw_brand.title(), 'standard', 1) for unknown brands.
    """
    cleaned = raw_brand.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned in PANEL_BRAND_MAP:
        return PANEL_BRAND_MAP[cleaned]
    # Fuzzy: check substring match
    for key, val in PANEL_BRAND_MAP.items():
        if key in cleaned or cleaned.startswith(key.split()[0]):
            return val
    return (raw_brand.strip().title(), "standard", 1)


def normalize_system_size_band(watts: int | float) -> str:
    """Map raw system size in watts to a size band label."""
    for threshold, label in SIZE_BAND_MAP:
        if watts >= threshold:
            return label
    return "3-5 kW"


def normalize_location(raw_location: str) -> dict:
    """Parse a location string into {city, state, country, metro}."""
    raw = raw_location.strip()
    lower = raw.lower()

    if lower in CITY_ALIASES:
        city, state = CITY_ALIASES[lower]
        metro = METRO_MAP.get((city, state), "")
        return {"city": city, "state": state, "country": "US", "metro": metro}

    if lower in STATE_ALIASES:
        _, state = STATE_ALIASES[lower]
        return {"city": "", "state": state, "country": "US", "metro": ""}

    parts = [p.strip() for p in raw.split(",")]
    if len(parts) >= 2:
        city = parts[0]
        state = parts[1].upper() if len(parts[1].strip()) <= 3 else parts[1]
        country = parts[2] if len(parts) > 2 else "US"
        metro = METRO_MAP.get((city, state), "")
        return {"city": city, "state": state, "country": country, "metro": metro}

    return {"city": "", "state": raw, "country": "US", "metro": ""}


def normalize_installer_type(raw: str) -> str:
    """Map free-text installer description to InstallerType choice key."""
    if not raw:
        return ""
    lower = raw.lower().strip()
    if any(x in lower for x in [
        "national", "sunrun", "tesla", "sunpower inc", "vivint",
        "sunnova", "loanpal", "goodleap", "freedom solar",
    ]):
        return "national"
    if any(x in lower for x in ["utility", "pge", "sce", "sdge", "developer", "project"]):
        return "utility"
    if any(x in lower for x in ["regional", "multi-state", "multi state"]):
        return "regional"
    if any(x in lower for x in ["local", "family", "independent", "owner"]):
        return "local"
    match = re.search(r"(\d+)\s*(location|office|crew|truck)", lower)
    if match:
        count = int(match.group(1))
        if count >= 21:
            return "national"
        if count >= 6:
            return "regional"
        return "local"
    return "local"
