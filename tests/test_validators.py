
import pytest
from validators import (
    validate_full_name,
    validate_dob,
    validate_email,
    validate_lab_value,
    validate_patient_payload,
)


def test_valid_name():
    valid, error, cleaned = validate_full_name("Twinkle Sahu")
    assert valid is True
    assert error is None
    assert cleaned == "Twinkle Sahu"


@pytest.mark.parametrize("name", [None, "", "   ", "A", "John123"])
def test_invalid_names(name):
    valid, error, cleaned = validate_full_name(name)
    assert valid is False
    assert error is not None
    assert cleaned is None


def test_valid_dob_converts_to_iso_format():
    valid, error, cleaned = validate_dob("15/08/2000")
    assert valid is True
    assert error is None
    assert cleaned == "2000-08-15"


@pytest.mark.parametrize(
    "dob",
    ["31/02/2000", "2000-08-15", "01/01/1899"],
)
def test_invalid_dob(dob):
    valid, error, cleaned = validate_dob(dob)
    assert valid is False
    assert error is not None
    assert cleaned is None


def test_valid_email_is_normalized():
    valid, error, cleaned = validate_email(" PATIENT@Example.COM ")
    assert valid is True
    assert error is None
    assert cleaned == "patient@example.com"


@pytest.mark.parametrize(
    "email",
    ["", "not-an-email", "patient@", "patient example.com"],
)
def test_invalid_emails(email):
    valid, error, cleaned = validate_email(email)
    assert valid is False
    assert error is not None
    assert cleaned is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("glucose", "95"),
        ("haemoglobin", "14.5"),
        ("cholesterol", "180"),
    ],
)
def test_valid_lab_values(field, value):
    valid, error, cleaned = validate_lab_value(value, field)
    assert valid is True
    assert error is None
    assert isinstance(cleaned, float)


@pytest.mark.parametrize(
    "field,value",
    [
        ("glucose", "not-a-number"),
        ("glucose", "nan"),
        ("glucose", "-10"),
        ("glucose", "10"),
        ("haemoglobin", "50"),
        ("cholesterol", "900"),
        ("cholesterol", ""),
    ],
)
def test_invalid_lab_values(field, value):
    valid, error, cleaned = validate_lab_value(value, field)
    assert valid is False
    assert error is not None
    assert cleaned is None


def test_invalid_patient_payload_reports_errors():
    payload = {
        "full_name": "",
        "dob": "31/02/2000",
        "email": "invalid-email",
        "glucose": "nan",
        "haemoglobin": "50",
        "cholesterol": "900",
    }

    valid, errors, cleaned = validate_patient_payload(payload)

    assert valid is False
    assert {"full_name", "dob", "email", "glucose", "haemoglobin", "cholesterol"} <= errors.keys()
