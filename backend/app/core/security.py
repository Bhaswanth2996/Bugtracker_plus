import hashlib
import hmac
import secrets
from base64 import b64decode, b64encode
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings

PBKDF2_ITERATIONS = 390000
PBKDF2_ALGORITHM = "sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}$"
        f"{b64encode(salt).decode()}${b64encode(digest).decode()}"
    )


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        algorithm, iter_text, salt_b64, digest_b64 = password_hash.split("$", 3)
        if not algorithm.startswith("pbkdf2_"):
            return False
        digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            plain_password.encode("utf-8"),
            b64decode(salt_b64.encode()),
            int(iter_text),
        )
        return hmac.compare_digest(digest, b64decode(digest_b64.encode()))
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.jwt_exp_minutes)
    payload = {
        "sub": user_id,
        "exp": datetime.now(tz=timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload.get("sub")
    except JWTError:
        return None
