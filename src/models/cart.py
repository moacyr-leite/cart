from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

from src.models.coupon import Coupon, CouponPublic  
from src.models.product import Product, ProductPublic


# ==========================================
# 1. SCHEMAS DE ITEM DO CARRINHO (ItemCart)
# Colocamos o Item primeiro para o Cart poder usá-lo abaixo
# ==========================================
class ItemCartBase(SQLModel):
    product_id: int
    amount: int = Field(default=1, gt=0)


class ItemCart(ItemCartBase, table=True):
    cart_id: Optional[int] = Field(default=None, foreign_key="cart.id", primary_key=True)
    product_id: int = Field(foreign_key="product.id", primary_key=True)
    
    # Relacionamentos bidirecionais diretos do SQLAlchemy
    cart: "Cart" = Relationship(back_populates="itens")
    product: "Product" = Relationship()
    
    model_config = {"from_attributes": True}


class ItemCartCreate(ItemCartBase):
    pass


class ItemCartPublic(SQLModel):
    cart_id: int
    product_id: int
    amount: int
    product: Optional[ProductPublic] = None

    model_config = {"from_attributes": True}


# ==========================================
# 2. SCHEMAS DO CARRINHO PRINCIPAL (Cart)
# ==========================================
class CartBase(SQLModel):
    pass 


class Cart(CartBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    coupon_id: Optional[int] = Field(default=None, foreign_key="coupon.id", nullable=True)
    
    coupon: Optional[Coupon] = Relationship()
    
    # Como ItemCart está no mesmo arquivo, o relacionamento é mapeado instantaneamente
    itens: List[ItemCart] = Relationship(
        back_populates="cart", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    model_config = {"from_attributes": True}


class CartCreate(CartBase):
    id: Optional[int] = Field(default=None, gt=0)


class CartPublic(CartBase):
    id: int
    coupon_id: Optional[int] = None
    coupon: Optional[CouponPublic] = None
    itens: List[ItemCartPublic] = Field(default_factory=list)

    model_config = {"from_attributes": True}
