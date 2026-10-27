"""
VitalSense AI - Input Validation Module
Implements robust server-side validation for patient records and laboratory parameters.
"""

from datetime import datetime, date
import math
import re
from typing import Dict, Any, Tuple, Optional

# Documented Laboratory Measurement Units and Application Plausibility Limits
# NOTE: These plausibility limits are input sanity checks for this academic application
# to prevent nonsensical or malicious input. They are NOT medical diagnostic thresholds.
LAB_UNITS = {
    "glucose": "mg/dL",
    "haemoglobin": "g/dL",
    "cholesterol": "mg/dL",
}

LAB_LIMITS = {
    "glucose": {
        "min": 20.0,
        "max": 1000.0,
        "unit": "mg/dL",
        "description": "Blood Glucose Level (mg/dL)"
    },
    "haemoglobin": {
        "min": 2.0,
        "max": 30.0,
        "unit": "g/dL",
        "description": "Haemoglobin Concentration (g/dL)"
    },
    "cholesterol": {
        "min": 50.0,
        "max": 800.0,
        "unit": "mg/dL",
        "description": "Total Serum Cholesterol (mg/dL)"
    },
}

# Regex for standard international names (supports letters, accents, spaces, hyphens, apostrophes, and periods)
# Enforces that at least one letter exists and prevents control characters
NAME_PATTERN = re.compile(r"^[^\W\d_][\w\s.'-]{1,99}$", re.UNICODE)
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*(?:\.[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*)+$"
)


def validate_full_name(name_str: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates patient full name.
    
    Rules:
    - Required and cannot be whitespace only
    - Trimmed of leading/trailing whitespace
    - Length between 2 and 100 characters
    - Allows international letters, hyphens, apostrophes, spaces, periods
    - Rejects control characters, numbers, and symbols
    
    Returns: (is_valid, error_message, cleaned_name)
    """
    if name_str is None:
        return False, "Full name is required.", None
        
    cleaned = name_str.strip()
    if not cleaned:
        return False, "Full name cannot be empty or contain only whitespace.", None
        
    if len(cleaned) < 2:
        return False, "Full name must be at least 2 characters long.", None
        
    if len(cleaned) > 100:
        return False, "Full name cannot exceed 100 characters.", None
        
    # Check for control characters
    if any(ord(c) < 32 for c in cleaned):
        return False, "Full name contains invalid control characters.", None

    # Check that name consists of letters, spaces, hyphens, periods, and apostrophes
    # Must contain at least one alphabetic character
    has_alpha = any(c.isalpha() for c in cleaned)
    if not has_alpha:
        return False, "Full name must contain alphabetic characters.", None

    for char in cleaned:
        if not (char.isalpha() or char in (" ", "-", "'", ".")):
            return False, f"Full name contains invalid character: '{char}'. Only letters, spaces, hyphens, apostrophes, and periods are permitted.", None

    return True, None, cleaned


def validate_dob(dob_str: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates Date of Birth in strict DD/MM/YYYY format.
    
    Rules:
    - Must strictly match DD/MM/YYYY format (e.g. 15/08/2000)
    - Must be a real calendar date (checks leap years, 31/02/2000 is rejected)
    - Cannot be a future date
    - Year must be 1900 or later (realistic lifespan check)
    - Converts validated date to ISO format YYYY-MM-DD for database storage
    
    Returns: (is_valid, error_message, iso_dob)
    """
    if not dob_str:
        return False, "Date of birth is required.", None
        
    cleaned = dob_str.strip()
    if not cleaned:
        return False, "Date of birth cannot be empty.", None

    # Check strict format pattern first: 2 digits / 2 digits / 4 digits
    format_regex = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    if not format_regex.match(cleaned):
        return (
            False,
            "Date of birth must be in the exact format DD/MM/YYYY (e.g., 15/08/2000).",
            None,
        )

    # Validate that it is an actual calendar date using datetime.strptime
    try:
        parsed_date = datetime.strptime(cleaned, "%d/%m/%Y").date()
    except ValueError:
        return False, f"'{cleaned}' is not a valid calendar date. Please check day and month values.", None

    today = date.today()
    if parsed_date > today:
        return False, "Date of birth cannot be in the future.", None

    if parsed_date.year < 1900:
        return False, "Year of birth must be 1900 or later.", None

    # Return valid ISO date string for database persistence (YYYY-MM-DD)
    iso_date = parsed_date.strftime("%Y-%m-%d")
    return True, None, iso_date


def format_dob_for_display(iso_date_str: str) -> str:
    """
    Converts ISO date string (YYYY-MM-DD) to DD/MM/YYYY for user interface display.
    """
    if not iso_date_str:
        return ""
    try:
        parsed = datetime.strptime(iso_date_str.strip(), "%Y-%m-%d")
        return parsed.strftime("%d/%m/%Y")
    except ValueError:
        return iso_date_str


def validate_email(email_str: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates patient email address.
    
    Rules:
    - Required and non-empty
    - Trimmed of whitespace
    - Standard email syntax check
    - Max length 254 characters (RFC 5321)
    
    Returns: (is_valid, error_message, cleaned_email)
    """
    if email_str is None:
        return False, "Email address is required.", None
        
    cleaned = email_str.strip().lower()
    if not cleaned:
        return False, "Email address cannot be empty.", None

    if len(cleaned) > 254:
        return False, "Email address cannot exceed 254 characters.", None

    # Disallow internal spaces or control characters
    if " " in cleaned or any(ord(c) < 32 for c in cleaned):
        return False, "Email address contains invalid characters or whitespace.", None

    if not EMAIL_PATTERN.match(cleaned):
        return False, "Please enter a valid email address (e.g., patient@example.com).", None

    return True, None, cleaned


def validate_lab_value(
    value_raw: Any, 
    field_name: str
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Validates a laboratory measurement (glucose, haemoglobin, or cholesterol).
    
    Rules:
    - Required numeric value (int or float)
    - Rejects strings that cannot be converted to float
    - Rejects NaN, +inf, -inf
    - Rejects negative values
    - Enforces documented plausibility limits (academic input sanity checks)
    
    Returns: (is_valid, error_message, cleaned_float)
    """
    if field_name not in LAB_LIMITS:
        raise ValueError(f"Unknown laboratory field: {field_name}")
        
    limits = LAB_LIMITS[field_name]
    label = limits["description"]
    unit = limits["unit"]

    if value_raw is None or (isinstance(value_raw, str) and not value_raw.strip()):
        return False, f"{label} is required.", None

    # Attempt numeric conversion
    try:
        if isinstance(value_raw, str):
            val_str = value_raw.strip()
            # Reject scientific notation like 'inf', 'nan' explicitly
            if val_str.lower() in ("nan", "inf", "-inf", "+inf"):
                return False, f"{label} must be a valid real number.", None
            num_val = float(val_str)
        elif isinstance(value_raw, (int, float)):
            num_val = float(value_raw)
        else:
            return False, f"{label} must be a valid numeric value.", None
    except (ValueError, TypeError):
        return False, f"{label} must be a valid number (e.g., 95.5).", None

    # Check for NaN and Infinity
    if math.isnan(num_val) or math.isinf(num_val):
        return False, f"{label} cannot be NaN or infinity.", None

    # Check for negative numbers
    if num_val < 0:
        return False, f"{label} cannot be negative.", None

    # Enforce plausibility limits
    if num_val < limits["min"] or num_val > limits["max"]:
        return (
            False,
            f"{label} ({num_val} {unit}) is outside the plausible academic input range of {limits['min']} to {limits['max']} {unit}.",
            None,
        )

    # Round to 2 decimal places for consistent precision
    return True, None, round(num_val, 2)


def validate_patient_payload(
    form_data: Dict[str, Any]
) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """
    Validates complete patient form submission.
    
    Returns:
        is_valid: bool indicating if all fields are valid
        errors: dict mapping field names to user-friendly error messages
        cleaned_data: dict of normalized, parsed values ready for DB or AI
    """
    errors: Dict[str, str] = {}
    cleaned: Dict[str, Any] = {}

    # 1. Full Name
    valid_name, err_name, clean_name = validate_full_name(form_data.get("full_name"))
    if not valid_name:
        errors["full_name"] = err_name
    else:
        cleaned["full_name"] = clean_name

    # 2. Date of Birth
    valid_dob, err_dob, iso_dob = validate_dob(form_data.get("dob"))
    if not valid_dob:
        errors["dob"] = err_dob
    else:
        cleaned["dob"] = iso_dob  # Stored as YYYY-MM-DD
        cleaned["dob_display"] = format_dob_for_display(iso_dob)  # DD/MM/YYYY

    # 3. Email
    valid_email, err_email, clean_email = validate_email(form_data.get("email"))
    if not valid_email:
        errors["email"] = err_email
    else:
        cleaned["email"] = clean_email

    # 4. Glucose
    valid_gluc, err_gluc, clean_gluc = validate_lab_value(form_data.get("glucose"), "glucose")
    if not valid_gluc:
        errors["glucose"] = err_gluc
    else:
        cleaned["glucose"] = clean_gluc

    # 5. Haemoglobin
    valid_hb, err_hb, clean_hb = validate_lab_value(form_data.get("haemoglobin"), "haemoglobin")
    if not valid_hb:
        errors["haemoglobin"] = err_hb
    else:
        cleaned["haemoglobin"] = clean_hb

    # 6. Cholesterol
    valid_chol, err_chol, clean_chol = validate_lab_value(form_data.get("cholesterol"), "cholesterol")
    if not valid_chol:
        errors["cholesterol"] = err_chol
    else:
        cleaned["cholesterol"] = clean_chol

    is_valid = len(errors) == 0
    return is_valid, errors, cleaned
