from decimal import Decimal

from sqlmodel import Field, SQLModel


class Coupon(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, min_length=1)
    discount: Decimal = Field(ge=0, le=1, max_digits=5, decimal_places=4)
