import hashlib
import os

_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, _, expected_hex = stored.partition("$")
    if not salt_hex or not expected_hex:
        return False
    candidate = hash_password(password, bytes.fromhex(salt_hex))
    return candidate == stored
