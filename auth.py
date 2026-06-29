"""Password hashing and session helpers. Standard library only.

Passwords are hashed with PBKDF2-HMAC-SHA256 (hashlib, built in to Python --
no third-party crypto dependency required). Sessions are random opaque
tokens stored server-side in the `sessions` SQLite table (not signed
cookies), so they remain valid even if the app later runs behind multiple
worker processes.
"""
import hashlib
import hmac
import os
import secrets
import datetime

PBKDF2_ITERATIONS = 260000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, iterations, salt, hex_digest = stored_hash.split("$")
        iterations = int(iterations)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return hmac.compare_digest(digest.hex(), hex_digest)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def generate_temp_password(length: int = 10) -> str:
    """A short random password for coach-issued resets ("forgot password").
    Avoids visually ambiguous characters (0/O, 1/l/I) since it's typically
    read aloud or typed out from a text message."""
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))
