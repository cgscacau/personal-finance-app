"""
Testes para módulo de utilidades
"""

import pytest
from datetime import date, datetime
from app.utils import (
    format_currency,
    format_percentage,
    parse_currency,
    format_date,
    parse_date,
    is_valid_email,
    sanitize_string,
    hash_transaction_id,
    calculate_percentage_change,
    safe_divide
)


class TestFormatCurrency:
    """Testes para formatação de moeda"""
    
    def test_format_positive_value(self):
        assert format_currency(1234.56) == "R$ 1.234,56"
    
    def test_format_negative_value(self):
        assert format_currency(-1234.56) == "-R$ 1.234,56"
    
    def test_format_zero(self):
        assert format_currency(0) == "R$ 0,00"
    
    def test_format_with_custom_currency(self):
        assert format_currency(100.50, "USD") == "USD 100,50"
    
    def test_format_invalid_value(self):
        assert format_currency(None) == "R$ 0,00"


class TestFormatPercentage:
    """Testes para formatação de porcentagem"""
    
    def test_format_percentage(self):
        assert format_percentage(0.1555) == "15,55%"
    
    def test_format_percentage_with_decimals(self):
        assert format_percentage(0.1555, decimals=1) == "15,6%"
    
    def test_format_zero_percentage(self):
        assert format_percentage(0) == "0,00%"


class TestParseCurrency:
    """Testes para parsing de moeda"""
    
    def test_parse_brazilian_format(self):
        assert parse_currency("R$ 1.234,56") == 1234.56
    
    def test_parse_without_symbol(self):
        assert parse_currency("1.234,56") == 1234.56
    
    def test_parse_invalid_value(self):
        assert parse_currency("invalid") is None
    
    def test_parse_none(self):
        assert parse_currency(None) is None


class TestFormatDate:
    """Testes para formatação de data"""
    
    def test_format_date_object(self):
        d = date(2024, 1, 15)
        assert format_date(d) == "15/01/2024"
    
    def test_format_datetime_object(self):
        dt = datetime(2024, 1, 15, 10, 30)
        assert format_date(dt) == "15/01/2024"
    
    def test_format_iso_string(self):
        assert format_date("2024-01-15") == "15/01/2024"
    
    def test_format_custom_format(self):
        d = date(2024, 1, 15)
        assert format_date(d, fmt="%Y-%m-%d") == "2024-01-15"


class TestParseDate:
    """Testes para parsing de data"""
    
    def test_parse_brazilian_format(self):
        result = parse_date("15/01/2024")
        assert result == date(2024, 1, 15)
    
    def test_parse_iso_format(self):
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)
    
    def test_parse_invalid_date(self):
        assert parse_date("invalid") is None
    
    def test_parse_custom_formats(self):
        result = parse_date("01-15-2024", formats=["%m-%d-%Y"])
        assert result == date(2024, 1, 15)


class TestEmailValidation:
    """Testes para validação de email"""
    
    def test_valid_email(self):
        assert is_valid_email("user@example.com") is True
    
    def test_valid_email_with_subdomain(self):
        assert is_valid_email("user@mail.example.com") is True
    
    def test_invalid_email_no_at(self):
        assert is_valid_email("userexample.com") is False
    
    def test_invalid_email_no_domain(self):
        assert is_valid_email("user@") is False
    
    def test_invalid_email_empty(self):
        assert is_valid_email("") is False


class TestSanitizeString:
    """Testes para sanitização de strings"""
    
    def test_sanitize_normal_string(self):
        assert sanitize_string("Hello World") == "Hello World"
    
    def test_sanitize_with_max_length(self):
        long_text = "a" * 1000
        result = sanitize_string(long_text, max_length=10)
        assert len(result) == 10
    
    def test_sanitize_empty_string(self):
        assert sanitize_string("") == ""
    
    def test_sanitize_none(self):
        assert sanitize_string(None) == ""


class TestHashTransactionId:
    """Testes para geração de hash"""
    
    def test_hash_consistent(self):
        hash1 = hash_transaction_id("2024-01-15", "Test", 100.00)
        hash2 = hash_transaction_id("2024-01-15", "Test", 100.00)
        assert hash1 == hash2
    
    def test_hash_different_values(self):
        hash1 = hash_transaction_id("2024-01-15", "Test", 100.00)
        hash2 = hash_transaction_id("2024-01-16", "Test", 100.00)
        assert hash1 != hash2
    
    def test_hash_length(self):
        result = hash_transaction_id("test")
        assert len(result) == 64  # SHA256


class TestCalculatePercentageChange:
    """Testes para cálculo de variação percentual"""
    
    def test_positive_change(self):
        result = calculate_percentage_change(100, 150)
        assert result == 0.5  # 50% aumento
    
    def test_negative_change(self):
        result = calculate_percentage_change(100, 50)
        assert result == -0.5  # 50% redução
    
    def test_no_change(self):
        result = calculate_percentage_change(100, 100)
        assert result == 0.0
    
    def test_from_zero(self):
        result = calculate_percentage_change(0, 100)
        assert result == float('inf')


class TestSafeDivide:
    """Testes para divisão segura"""
    
    def test_normal_division(self):
        assert safe_divide(10, 2) == 5.0
    
    def test_division_by_zero(self):
        assert safe_divide(10, 0) == 0.0
    
    def test_division_by_zero_custom_default(self):
        assert safe_divide(10, 0, default=999) == 999
    
    def test_invalid_types(self):
        assert safe_divide("invalid", 2) == 0.0
