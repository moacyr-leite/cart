from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    cart_id: int | None = Field(default=None, index=True)
    subtotal: Decimal = Field(max_digits=12, decimal_places=2)
    coupon_code: str | None = Field(default=None, max_length=255)
    coupon_discount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    payment_discount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    total: Decimal = Field(max_digits=12, decimal_places=2)
    payment_method: str = Field(max_length=32)
    status: str = Field(default="pending", max_length=32)
    payment_status: str = Field(default="pending", max_length=32)
    idempotency_key: str | None = Field(default=None, unique=True, index=True, max_length=255)
    request_fingerprint: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)
    paid_at: datetime | None = Field(default=None)
    cancelled_at: datetime | None = Field(default=None)

    items: list["OrderItem"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int
    product_name: str = Field(max_length=255)
    amount: int = Field(gt=0)
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    subtotal: Decimal = Field(max_digits=12, decimal_places=2)

    order: Order = Relationship(back_populates="items")
