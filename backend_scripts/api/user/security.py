"""Password hashing and verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Tuple

PBKDF2_ITERATIONS = 120_000
PBKDF2_ALGO = "sha256"
_SEP = "$"


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    """Return a PBKDF2 hash string."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGO,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2{_SEP}{iterations}{_SEP}{salt}{_SEP}{digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify plaintext password against stored PBKDF2 hash.

    Falls back to legacy SHA256 hashes for backward compatibility.
    """
    if not stored_hash:
        return False

    if stored_hash.startswith("pbkdf2$"):
        try:
            _, iterations, salt, digest = stored_hash.split(_SEP, 3)
            calc = hashlib.pbkdf2_hmac(
                PBKDF2_ALGO,
                password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            ).hex()
            return hmac.compare_digest(calc, digest)
        except Exception:
            return False

    # Legacy fallback (old system stored plain SHA256 hex)
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)

