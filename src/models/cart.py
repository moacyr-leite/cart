from sqlmodel import Field, Relationship, SQLModel

from src.models.coupon import Coupon
from src.models.product import Product


class ItemCart(SQLModel, table=True):
    cart_id: int = Field(foreign_key="cart.id", primary_key=True)
    product_id: int = Field(foreign_key="product.id", primary_key=True)
    amount: int = Field(default=1, gt=0)

    cart: "Cart" = Relationship(back_populates="itens")
    product: Product = Relationship()


class Cart(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    coupon_id: int | None = Field(default=None, foreign_key="coupon.id", nullable=True)

    coupon: Coupon | None = Relationship()
    itens: list[ItemCart] = Relationship(
        back_populates="cart",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
