from typing import Annotated

from fastapi import APIRouter, Header, Query, status

from src.database.session import SessionDep
from src.schemas.cart import CartPublic, ItemCartCreate, ItemCartPublic
from src.schemas.order import CheckoutReceipt, PaymentMethod
from src.services.cart import CartService
from src.services.checkout import CheckoutService
from src.services.item_cart import ItemCartService

router = APIRouter()

# ==========================================
# ROTAS DO CARRINHO (Cart)
# ==========================================


@router.post("/", response_model=CartPublic, status_code=status.HTTP_201_CREATED)
def create_cart(session: SessionDep):
    return CartService.create(session)


@router.get("/{cart_id}", response_model=CartPublic)
def read_cart(cart_id: int, session: SessionDep):
    return CartService.get(session, cart_id)


@router.get("/", response_model=list[CartPublic])
def read_carts(session: SessionDep, skip: int = 0, limit: int = 100):
    return CartService.gets(session, skip=skip, limit=limit)


@router.patch("/{cart_id}/coupon", response_model=CartPublic)
def add_coupon_to_cart(cart_id: int, coupon_code: str, session: SessionDep):
    return CartService.add_coupon(session, cart_id, coupon_code)


@router.delete("/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart(cart_id: int, session: SessionDep):
    CartService.delete(session, cart_id)


@router.delete("/{cart_id}/coupon", response_model=CartPublic)
def remove_coupon_from_cart(cart_id: int, session: SessionDep):
    return CartService.remove_coupon(session, cart_id)


# ==========================================
# ROTAS DE ITENS DO CARRINHO (ItemCart)
# ==========================================


@router.post(
    "/{cart_id}/items",
    response_model=ItemCartPublic,
    status_code=status.HTTP_201_CREATED,
)
def add_item_to_cart(cart_id: int, item_in: ItemCartCreate, session: SessionDep):
    return ItemCartService.add_item(session, cart_id, item_in)


@router.put("/{cart_id}/items/{product_id}", response_model=ItemCartPublic)
def update_item_quantity(
    cart_id: int,
    product_id: int,
    amount: Annotated[int, Query(gt=0)],
    session: SessionDep,
):
    return ItemCartService.update_quantity(session, cart_id, product_id, amount)


@router.delete("/{cart_id}/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_cart(cart_id: int, product_id: int, session: SessionDep):
    ItemCartService.remove_item(session, cart_id, product_id)


@router.post("/{cart_id}/checkout", response_model=CheckoutReceipt)
def checkout_cart(
    cart_id: int,
    payment_method: PaymentMethod,
    session: SessionDep,
    coupon_code: str | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """Finaliza o pedido aplicando descontos cumulativos (cupom + método de pagamento)."""
    return CheckoutService.process_checkout(
        session,
        cart_id,
        payment_method,
        coupon_code,
        idempotency_key,
    )
