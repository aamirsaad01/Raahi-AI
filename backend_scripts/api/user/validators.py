"""Validation helpers for user auth/profile flows."""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Dict, Optional

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")
CNIC_RE = re.compile(r"^\d{5}-\d{7}-\d$")


def _req_str(data: Dict, key: str) -> str:
    v = data.get(key, "")
    return str(v).strip()


def validate_signup_payload(data: Dict) -> Optional[str]:
    required = [
        "name",
        "email",
        "contact_number",
        "dob",
        "cnic",
        "password",
    ]
    for field in required:
        if not _req_str(data, field):
            return f"Missing required field: {field}"

    name = _req_str(data, "name")
    if len(name) < 2 or len(name) > 100:
        return "Name must be between 2 and 100 characters"

    email = _req_str(data, "email").lower()
    if not EMAIL_RE.match(email):
        return "Invalid email format"

    contact = _req_str(data, "contact_number")
    if not PHONE_RE.match(contact):
        return "Contact number must be 10-15 digits (optional + prefix)"

    dob = _req_str(data, "dob")
    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        return "DOB must be in YYYY-MM-DD format"
    if _age_years(dob_date) < 13:
        return "User must be at least 13 years old"

    cnic = _req_str(data, "cnic")
    if not CNIC_RE.match(cnic):
        return "CNIC must match 12345-1234567-1 format"

    medical = _req_str(data, "medical_conditions")
    if len(medical) > 500:
        return "Medical conditions must be 500 characters or fewer"

    pwd = _req_str(data, "password")
    pwd_err = validate_password_strength(pwd)
    if pwd_err:
        return pwd_err

    return None


def validate_password_strength(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[a-z]", password):
        return "Password must include at least one lowercase letter"
    if not re.search(r"[A-Z]", password):
        return "Password must include at least one uppercase letter"
    if not re.search(r"\d", password):
        return "Password must include at least one number"
    return None


def _age_years(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

