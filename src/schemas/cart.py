from pydantic import BaseModel, ConfigDict, Field

from src.schemas.coupon import CouponPublic
from src.schemas.product import ProductPublic


class ItemCartCreate(BaseModel):
    product_id: int
    amount: int = Field(default=1, gt=0)


class ItemCartPublic(BaseModel):
    cart_id: int
    product_id: int
    amount: int
    product: ProductPublic | None = None

    model_config = ConfigDict(from_attributes=True)


class CartPublic(BaseModel):
    id: int
    coupon_id: int | None = None
    coupon: CouponPublic | None = None
    itens: list[ItemCartPublic] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
