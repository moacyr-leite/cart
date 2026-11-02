import hashlib
import re

from src.core.errors import AppError, AppException

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,255}$")


def normalize_idempotency_key(value: str | None) -> str | None:
    if value is None:
        return None

    key = value.strip()
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(key):
        raise AppException(AppError.INVALID_IDEMPOTENCY_KEY)
    return key


def request_fingerprint(*parts: object) -> str:
    payload = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
