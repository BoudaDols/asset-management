"""Tests for app.core.validators module."""

from app.core.validators import (
    validate_code_format,
    validate_instance_code,
    validate_name,
    validate_xor_catalog_ref,
)


class TestValidateCodeFormat:
    """Test validate_code_format for catalog codes (^[A-Z0-9_]{1,50}$)."""

    def test_valid_simple_uppercase(self):
        assert validate_code_format("EP") is True

    def test_valid_with_underscore(self):
        assert validate_code_format("RES_DIST") is True

    def test_valid_with_numbers(self):
        assert validate_code_format("LEVEL3") is True

    def test_valid_single_char(self):
        assert validate_code_format("A") is True

    def test_valid_max_length(self):
        assert validate_code_format("A" * 50) is True

    def test_invalid_empty_string(self):
        assert validate_code_format("") is False

    def test_invalid_lowercase(self):
        assert validate_code_format("ep") is False

    def test_invalid_mixed_case(self):
        assert validate_code_format("Ep") is False

    def test_invalid_hyphen(self):
        assert validate_code_format("RES-DIST") is False

    def test_invalid_space(self):
        assert validate_code_format("RES DIST") is False

    def test_invalid_too_long(self):
        assert validate_code_format("A" * 51) is False

    def test_invalid_special_chars(self):
        assert validate_code_format("EP@#") is False


class TestValidateName:
    """Test validate_name for name fields (non-empty, non-whitespace, max 255)."""

    def test_valid_simple_name(self):
        assert validate_name("Eau potable") is True

    def test_valid_single_char(self):
        assert validate_name("A") is True

    def test_valid_with_leading_trailing_spaces(self):
        assert validate_name("  Eau potable  ") is True

    def test_valid_max_length(self):
        assert validate_name("A" * 255) is True

    def test_invalid_empty_string(self):
        assert validate_name("") is False

    def test_invalid_whitespace_only_space(self):
        assert validate_name("   ") is False

    def test_invalid_whitespace_only_tab(self):
        assert validate_name("\t\t") is False

    def test_invalid_whitespace_only_newline(self):
        assert validate_name("\n") is False

    def test_invalid_too_long(self):
        assert validate_name("A" * 256) is False


class TestValidateInstanceCode:
    """Test validate_instance_code for instance codes (^[A-Za-z0-9_\\-]{1,50}$)."""

    def test_valid_alphanumeric(self):
        assert validate_instance_code("pump001") is True

    def test_valid_with_hyphen(self):
        assert validate_instance_code("pump-001") is True

    def test_valid_with_underscore(self):
        assert validate_instance_code("pump_001") is True

    def test_valid_mixed_case(self):
        assert validate_instance_code("Pump001") is True

    def test_valid_single_char(self):
        assert validate_instance_code("a") is True

    def test_valid_max_length(self):
        assert validate_instance_code("a" * 50) is True

    def test_invalid_empty_string(self):
        assert validate_instance_code("") is False

    def test_invalid_space(self):
        assert validate_instance_code("pump 001") is False

    def test_invalid_special_chars(self):
        assert validate_instance_code("pump@001") is False

    def test_invalid_too_long(self):
        assert validate_instance_code("a" * 51) is False

    def test_invalid_dot(self):
        assert validate_instance_code("pump.001") is False


class TestValidateXorCatalogRef:
    """Test validate_xor_catalog_ref for exactly-one-non-null constraint."""

    def test_valid_only_prim(self):
        assert validate_xor_catalog_ref("PRIM1", None, None) is True

    def test_valid_only_seco(self):
        assert validate_xor_catalog_ref(None, "SECO1", None) is True

    def test_valid_only_tert(self):
        assert validate_xor_catalog_ref(None, None, "TERT1") is True

    def test_invalid_all_none(self):
        assert validate_xor_catalog_ref(None, None, None) is False

    def test_invalid_two_set_prim_seco(self):
        assert validate_xor_catalog_ref("PRIM1", "SECO1", None) is False

    def test_invalid_two_set_prim_tert(self):
        assert validate_xor_catalog_ref("PRIM1", None, "TERT1") is False

    def test_invalid_two_set_seco_tert(self):
        assert validate_xor_catalog_ref(None, "SECO1", "TERT1") is False

    def test_invalid_all_set(self):
        assert validate_xor_catalog_ref("PRIM1", "SECO1", "TERT1") is False
