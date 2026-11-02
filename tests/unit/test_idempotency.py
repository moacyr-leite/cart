import pytest

from src.core.errors import AppError, AppException
from src.core.idempotency import normalize_idempotency_key, request_fingerprint


def test_missing_idempotency_key_stays_none():
    assert normalize_idempotency_key(None) is None


def test_idempotency_key_is_trimmed():
    assert normalize_idempotency_key(" checkout-1 ") == "checkout-1"


@pytest.mark.parametrize("value", ["", "chave com espaco", "a" * 256, "chave!"])
def test_invalid_idempotency_key_is_rejected(value):
    with pytest.raises(AppException) as exc_info:
        normalize_idempotency_key(value)

    assert exc_info.value.error is AppError.INVALID_IDEMPOTENCY_KEY


def test_fingerprint_is_deterministic_and_order_sensitive():
    first = request_fingerprint("checkout", 1, "pix", "PROMO10")
    second = request_fingerprint("checkout", 1, "pix", "PROMO10")
    different = request_fingerprint("checkout", 1, "credit_card", "PROMO10")

    assert first == second
    assert first != different
    assert len(first) == 64
