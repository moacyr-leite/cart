from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class PaymentMethod(str, Enum):
    PIX = "pix"
    CREDIT_CARD = "credit_card"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    FAILED = "failed"
    REFUNDED = "refunded"


class CheckoutItem(BaseModel):
    product_id: int
    product_name: str
    amount: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class CheckoutReceipt(BaseModel):
    order_id: int
    cart_id: int | None
    subtotal: Decimal
    coupon_code: str | None
    coupon_discount: Decimal
    payment_discount: Decimal
    total: Decimal
    payment_method: PaymentMethod
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    paid_at: datetime | None
    cancelled_at: datetime | None
    items: list[CheckoutItem]
