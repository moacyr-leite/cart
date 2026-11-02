from decimal import Decimal

from src.schemas.order import PaymentMethod
from src.services.checkout import calculate_total, quote


def test_quote_applies_coupon_before_pix_discount():
    coupon_discount, payment_discount, total = quote(
        Decimal("100.00"), Decimal("0.10"), PaymentMethod.PIX
    )

    assert coupon_discount == Decimal("10.00")
    assert payment_discount == Decimal("4.50")
    assert total == Decimal("85.50")


def test_quote_with_credit_card_only_applies_coupon():
    coupon_discount, payment_discount, total = quote(
        Decimal("100.00"), Decimal("0.10"), PaymentMethod.CREDIT_CARD
    )

    assert coupon_discount == Decimal("10.00")
    assert payment_discount == Decimal("0.00")
    assert total == Decimal("90.00")


def test_quote_rounds_discounts_to_cents():
    coupon_discount, payment_discount, total = quote(
        Decimal("0.05"), Decimal("0.10"), PaymentMethod.CREDIT_CARD
    )

    assert coupon_discount == Decimal("0.01")
    assert payment_discount == Decimal("0.00")
    assert total == Decimal("0.04")


def test_calculate_total_returns_the_quoted_total():
    assert calculate_total(Decimal("100.00"), Decimal("0.10"), PaymentMethod.PIX) == Decimal(
        "85.50"
    )
