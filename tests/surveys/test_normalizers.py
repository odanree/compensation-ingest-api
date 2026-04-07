from apps.surveys.normalizers import normalize_company_size, normalize_location, normalize_role_title


class TestNormalizeRoleTitle:
    def test_swe_abbreviation(self):
        title, family = normalize_role_title("swe")
        assert title == "Software Engineer"
        assert family == "Engineering"

    def test_pm_abbreviation(self):
        title, family = normalize_role_title("pm")
        assert title == "Product Manager"
        assert family == "Product"

    def test_case_insensitive(self):
        title, _ = normalize_role_title("SWE")
        assert title == "Software Engineer"

    def test_senior_engineer(self):
        title, family = normalize_role_title("Senior Software Engineer")
        assert title == "Senior Software Engineer"
        assert family == "Engineering"

    def test_unknown_title_returns_titlecased(self):
        title, family = normalize_role_title("quantum philosopher")
        assert title == "Quantum Philosopher"
        assert family == "Other"

    def test_data_scientist(self):
        title, family = normalize_role_title("Data Scientist")
        assert title == "Data Scientist"
        assert family == "Data"

    def test_extra_whitespace(self):
        title, _ = normalize_role_title("  swe  ")
        assert title == "Software Engineer"


class TestNormalizeLocation:
    def test_san_francisco_metro(self):
        result = normalize_location("San Francisco, CA")
        assert result["city"] == "San Francisco"
        assert result["state"] == "CA"
        assert result["metro"] == "San Francisco Bay Area"

    def test_city_alias_sf(self):
        result = normalize_location("sf")
        assert result["city"] == "San Francisco"
        assert result["metro"] == "San Francisco Bay Area"

    def test_city_alias_nyc(self):
        result = normalize_location("nyc")
        assert result["city"] == "New York"
        assert result["metro"] == "New York Metro"

    def test_city_state_country(self):
        result = normalize_location("London, England, UK")
        assert result["city"] == "London"
        assert result["country"] == "UK"

    def test_unknown_location_fallback(self):
        result = normalize_location("Remote")
        assert result["country"] == "Remote"
        assert result["city"] == ""


class TestNormalizeCompanySize:
    def test_enterprise_string(self):
        assert normalize_company_size("5000+") == "enterprise"

    def test_startup_string(self):
        assert normalize_company_size("startup") == "startup"

    def test_numeric_large(self):
        assert normalize_company_size("10000 employees") == "enterprise"

    def test_numeric_mid(self):
        assert normalize_company_size("500 employees") == "mid"

    def test_empty_string(self):
        assert normalize_company_size("") == ""

    def test_faang(self):
        assert normalize_company_size("faang") == "enterprise"

    def test_series_a(self):
        assert normalize_company_size("Series A startup") == "startup"
