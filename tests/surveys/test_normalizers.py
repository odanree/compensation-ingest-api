from apps.surveys.normalizers import (
    normalize_installer_type,
    normalize_location,
    normalize_panel_brand,
    normalize_system_size_band,
)


class TestNormalizePanelBrand:
    def test_sunpower_is_premium_plus(self):
        label, tier, order = normalize_panel_brand("SunPower Maxeon 3")
        assert tier == "premium-plus"
        assert order == 3

    def test_lg_is_premium(self):
        label, tier, order = normalize_panel_brand("LG NeON 2")
        assert tier == "premium"
        assert order == 2

    def test_longi_is_standard(self):
        label, tier, order = normalize_panel_brand("LONGi Hi-MO 5")
        assert tier == "standard"
        assert order == 1

    def test_case_insensitive(self):
        _, tier, _ = normalize_panel_brand("sunpower maxeon")
        assert tier == "premium-plus"

    def test_unknown_brand_returns_standard(self):
        _, tier, _ = normalize_panel_brand("NoName Solar Co")
        assert tier == "standard"

    def test_empty_string_returns_standard(self):
        _, tier, _ = normalize_panel_brand("")
        assert tier == "standard"


class TestNormalizeSystemSizeBand:
    def test_small_system(self):
        assert normalize_system_size_band(4000) == "3-5 kW"

    def test_medium_system(self):
        assert normalize_system_size_band(6500) == "5-8 kW"

    def test_large_system(self):
        assert normalize_system_size_band(10000) == "8-12 kW"

    def test_xlarge_system(self):
        assert normalize_system_size_band(15000) == "12 kW+"

    def test_boundary_exactly_5kw(self):
        assert normalize_system_size_band(5000) == "5-8 kW"

    def test_below_3kw_returns_small_band(self):
        assert normalize_system_size_band(2000) == "3-5 kW"


class TestNormalizeLocation:
    def test_san_diego_metro(self):
        result = normalize_location("San Diego, CA")
        assert result["city"] == "San Diego"
        assert result["state"] == "CA"
        assert result["metro"] == "San Diego"

    def test_city_alias_sf(self):
        result = normalize_location("sf")
        assert result["city"] == "San Francisco"
        assert result["state"] == "CA"

    def test_city_alias_la(self):
        result = normalize_location("la")
        assert result["city"] == "Los Angeles"
        assert result["state"] == "CA"

    def test_state_alias_california(self):
        result = normalize_location("Los Angeles, California")
        assert result["state"] == "CA"

    def test_unknown_location_fallback(self):
        result = normalize_location("Remote")
        assert result["city"] == ""

    def test_empty_string_fallback(self):
        result = normalize_location("")
        assert result["country"] == "US"


class TestNormalizeInstallerType:
    def test_local_string(self):
        assert normalize_installer_type("local") == "local"

    def test_national_string(self):
        assert normalize_installer_type("national") == "national"

    def test_case_insensitive(self):
        assert normalize_installer_type("Regional") == "regional"

    def test_unknown_returns_empty(self):
        assert normalize_installer_type("franchise") == ""

    def test_empty_returns_empty(self):
        assert normalize_installer_type("") == ""
