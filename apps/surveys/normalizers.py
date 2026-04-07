import re

ROLE_NORMALIZATION_MAP = {
    # Software Engineering — generic
    "swe": "Software Engineer",
    "sw engineer": "Software Engineer",
    "software dev": "Software Engineer",
    "software developer": "Software Engineer",
    "software engineer": "Software Engineer",
    "sde": "Software Engineer",
    "sde i": "Software Engineer I",
    "sde ii": "Software Engineer II",
    "sde iii": "Software Engineer III",
    "swe i": "Software Engineer I",
    "swe ii": "Software Engineer II",
    "swe iii": "Software Engineer III",
    "swe 1": "Software Engineer I",
    "swe 2": "Software Engineer II",
    "swe 3": "Software Engineer III",
    "software engineer 1": "Software Engineer I",
    "software engineer 2": "Software Engineer II",
    "software engineer 3": "Software Engineer III",
    "l3 engineer": "Software Engineer I",
    "l4 engineer": "Software Engineer II",
    "l5 engineer": "Software Engineer III",
    "e3": "Software Engineer I",
    "e4": "Software Engineer II",
    # Senior
    "senior swe": "Senior Software Engineer",
    "senior software engineer": "Senior Software Engineer",
    "sr. software engineer": "Senior Software Engineer",
    "sr software engineer": "Senior Software Engineer",
    "l5": "Senior Software Engineer",
    "e5": "Senior Software Engineer",
    # Staff+
    "staff engineer": "Staff Software Engineer",
    "staff software engineer": "Staff Software Engineer",
    "l6": "Staff Software Engineer",
    "e6": "Staff Software Engineer",
    "principal engineer": "Principal Software Engineer",
    "principal software engineer": "Principal Software Engineer",
    "l7": "Principal Software Engineer",
    "e7": "Principal Software Engineer",
    # Product Management
    "pm": "Product Manager",
    "prod manager": "Product Manager",
    "product manager": "Product Manager",
    "apm": "Associate Product Manager",
    "associate pm": "Associate Product Manager",
    "associate product manager": "Associate Product Manager",
    "senior pm": "Senior Product Manager",
    "sr pm": "Senior Product Manager",
    "senior product manager": "Senior Product Manager",
    "director of product": "Director of Product Management",
    "director, product": "Director of Product Management",
    "vp product": "VP of Product",
    "vp of product": "VP of Product",
    # Data
    "data scientist": "Data Scientist",
    "ds": "Data Scientist",
    "data analyst": "Data Analyst",
    "da": "Data Analyst",
    "data engineer": "Data Engineer",
    "de": "Data Engineer",
    "ml engineer": "Machine Learning Engineer",
    "mle": "Machine Learning Engineer",
    "machine learning engineer": "Machine Learning Engineer",
    # Design
    "ux designer": "UX Designer",
    "ui designer": "UI Designer",
    "product designer": "Product Designer",
    "ux researcher": "UX Researcher",
    # Engineering Management
    "engineering manager": "Engineering Manager",
    "em": "Engineering Manager",
    "eng manager": "Engineering Manager",
    "director of engineering": "Director of Engineering",
    "vp engineering": "VP of Engineering",
    "vp of engineering": "VP of Engineering",
    "cto": "Chief Technology Officer",
}

ROLE_FAMILY_MAP = {
    "Software Engineer": "Engineering",
    "Software Engineer I": "Engineering",
    "Software Engineer II": "Engineering",
    "Software Engineer III": "Engineering",
    "Senior Software Engineer": "Engineering",
    "Staff Software Engineer": "Engineering",
    "Principal Software Engineer": "Engineering",
    "Engineering Manager": "Engineering",
    "Director of Engineering": "Engineering",
    "VP of Engineering": "Engineering",
    "Chief Technology Officer": "Engineering",
    "Machine Learning Engineer": "Engineering",
    "Data Engineer": "Engineering",
    "Product Manager": "Product",
    "Associate Product Manager": "Product",
    "Senior Product Manager": "Product",
    "Director of Product Management": "Product",
    "VP of Product": "Product",
    "Data Scientist": "Data",
    "Data Analyst": "Data",
    "UX Designer": "Design",
    "UI Designer": "Design",
    "Product Designer": "Design",
    "UX Researcher": "Design",
}

METRO_MAP = {
    ("San Francisco", "CA"): "San Francisco Bay Area",
    ("San Jose", "CA"): "San Francisco Bay Area",
    ("Palo Alto", "CA"): "San Francisco Bay Area",
    ("Mountain View", "CA"): "San Francisco Bay Area",
    ("Sunnyvale", "CA"): "San Francisco Bay Area",
    ("Menlo Park", "CA"): "San Francisco Bay Area",
    ("New York", "NY"): "New York Metro",
    ("Brooklyn", "NY"): "New York Metro",
    ("Seattle", "WA"): "Seattle Metro",
    ("Bellevue", "WA"): "Seattle Metro",
    ("Redmond", "WA"): "Seattle Metro",
    ("Austin", "TX"): "Austin Metro",
    ("Boston", "MA"): "Boston Metro",
    ("Cambridge", "MA"): "Boston Metro",
    ("Chicago", "IL"): "Chicago Metro",
    ("Los Angeles", "CA"): "Los Angeles Metro",
    ("Santa Monica", "CA"): "Los Angeles Metro",
    ("Denver", "CO"): "Denver Metro",
    ("Atlanta", "GA"): "Atlanta Metro",
    ("Miami", "FL"): "Miami Metro",
}

CITY_ALIASES = {
    "nyc": ("New York", "NY"),
    "new york city": ("New York", "NY"),
    "sf": ("San Francisco", "CA"),
    "san francisco bay area": ("San Francisco", "CA"),
    "bay area": ("San Francisco", "CA"),
    "la": ("Los Angeles", "CA"),
}


def normalize_role_title(raw_title: str) -> tuple[str, str]:
    """Return (normalized_title, family)."""
    cleaned = raw_title.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    normalized = ROLE_NORMALIZATION_MAP.get(cleaned, raw_title.strip().title())
    family = ROLE_FAMILY_MAP.get(normalized, "Other")
    return normalized, family


def normalize_location(raw_location: str) -> dict:
    """Parse a location string into {city, state, country, metro}."""
    raw = raw_location.strip()
    lower = raw.lower()

    if lower in CITY_ALIASES:
        city, state = CITY_ALIASES[lower]
        metro = METRO_MAP.get((city, state), "")
        return {"city": city, "state": state, "country": "US", "metro": metro}

    parts = [p.strip() for p in raw.split(",")]
    if len(parts) >= 2:
        city = parts[0]
        state = parts[1].upper() if len(parts[1].strip()) <= 3 else parts[1]
        country = parts[2] if len(parts) > 2 else "US"
        metro = METRO_MAP.get((city, state), "")
        return {"city": city, "state": state, "country": country, "metro": metro}

    return {"city": "", "state": "", "country": raw, "metro": ""}


def normalize_company_size(raw: str) -> str:
    """Map a raw headcount string to a CompanySize choice key."""
    if not raw:
        return ""
    lower = raw.lower().strip()
    if any(x in lower for x in ["startup", "1-50", "<50", "seed", "series a"]):
        return "startup"
    if any(x in lower for x in ["51-200", "small", "series b"]):
        return "small"
    if any(x in lower for x in ["201-1000", "mid", "series c", "series d"]):
        return "mid"
    if any(x in lower for x in ["1001-5000", "large", "pre-ipo"]):
        return "large"
    if any(x in lower for x in ["5000+", "enterprise", "public", "faang"]):
        return "enterprise"
    match = re.search(r"(\d+)", lower)
    if match:
        count = int(match.group(1))
        if count <= 50:
            return "startup"
        if count <= 200:
            return "small"
        if count <= 1000:
            return "mid"
        if count <= 5000:
            return "large"
        return "enterprise"
    return ""
