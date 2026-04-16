"""User service utilities used by auth routes/app startup."""

from __future__ import annotations

from typing import Dict, Optional

from api.user.security import hash_password
from api.utils.db_helper import DatabaseHelper

ADMIN_EMAIL = "admin@raahi.com"
ADMIN_PASSWORD = "admin"


def ensure_default_admin() -> None:
    """Create a default admin account if missing."""
    db = DatabaseHelper()
    try:
        user = db.get_user_by_email(ADMIN_EMAIL)
        if user:
            return
        db.create_user_profile(
            name="Raahi Admin",
            email=ADMIN_EMAIL,
            contact_number="+920000000000",
            dob="1990-01-01",
            cnic="00000-0000000-0",
            medical_conditions="",
            password_hash=hash_password(ADMIN_PASSWORD),
            is_admin=True,
        )
    finally:
        db.close()

