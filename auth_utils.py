"""Small shared helper for password hashing.

Used by both Account.py (MySQL) and Account1.py (SQLite) so passwords are
never stored or compared in plaintext.
"""

import hashlib
import secrets

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """Hash a plaintext password with PBKDF2-HMAC-SHA256 and a random salt.

    Returns a string "<salt_hex>$<hash_hex>" that comfortably fits inside the
    existing VARCHAR(255)/TEXT password column, so no schema migration is
    needed beyond what's already in this project.
    """
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    )
    return f"{salt}${digest.hex()}"


def verify_password(stored: str, provided: str) -> bool:
    """Check a plaintext password against a value from hash_password().

    Falls back to a plain comparison if `stored` doesn't look like one of our
    hashes (e.g. an account created before this change), so existing accounts
    in an existing database keep working.
    """
    if "$" not in stored:
        return secrets.compare_digest(stored, provided)

    salt, hash_hex = stored.split("$", 1)
    try:
        digest = hashlib.pbkdf2_hmac(
            "sha256", provided.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
        )
    except ValueError:
        # `stored` had a "$" but wasn't actually salt$hash - treat as legacy plaintext.
        return secrets.compare_digest(stored, provided)
    return secrets.compare_digest(digest.hex(), hash_hex)