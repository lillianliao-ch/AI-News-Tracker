import math

from candidate_cleaner.transformers import normalize_datetime, normalize_phone


def test_normalize_phone_digits_only():
    assert normalize_phone("139-1234-5678") == "13912345678"


def test_normalize_phone_invalid():
    assert normalize_phone("12345") is None
    assert normalize_phone(None) is None


def test_normalize_datetime_formats():
    assert normalize_datetime("2025-09-26 10:30:00") == "2025-09-26T10:30:00"
    assert normalize_datetime("2025/09/26") == "2025-09-26T00:00:00"


def test_normalize_datetime_invalid():
    assert normalize_datetime("invalid") is None
    assert normalize_datetime(float("nan")) is None
