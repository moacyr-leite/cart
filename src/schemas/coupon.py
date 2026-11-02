from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CouponBase(BaseModel):
    code: str = Field(min_length=1)
    discount: Decimal = Field(ge=0, le=1, max_digits=5, decimal_places=4)

    model_config = ConfigDict(from_attributes=True)


class CouponCreate(CouponBase):
    @field_validator("code")
    @classmethod
    def force_uppercase(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Coupon code must not be empty.")
        return normalized


class CouponPublic(CouponBase):
    id: int
