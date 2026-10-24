from fastapi import APIRouter, HTTPException, Query, status
from typing import Annotated, List

from src.services.checkout import CheckoutReceipt, CheckoutService, PaymentMethod
from src.database.session import SessionDep  # Sua dependência anotada do SQLModel
from src.models.cart import CartPublic, CartCreate, ItemCartCreate, ItemCartPublic
from src.services.cart import CartService
from src.services.item_cart import ItemCartService

router = APIRouter()

# ==========================================
# ROTAS DO CARRINHO (Cart)
# ==========================================

@router.post("/", response_model=CartPublic, status_code=status.HTTP_201_CREATED)
def create_cart(cart_in: CartCreate, session: SessionDep):
    result = CartService.create(session, cart_in)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return result.value

@router.get("/{cart_id}", response_model=CartPublic)
def read_cart(cart_id: int, session: SessionDep):
    result = CartService.get(session, cart_id)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return result.value

@router.get("/", response_model=List[CartPublic])
def read_carts(session: SessionDep, skip: int = 0, limit: int = 100):
    # Listagens puras retornam a lista direto do service
    return CartService.gets(session, skip=skip, limit=limit)

@router.patch("/{cart_id}/coupon", response_model=CartPublic)
def add_coupon_to_cart(cart_id: int, coupon_code: str, session: SessionDep):
    result = CartService.add_coupon(session, cart_id, coupon_code)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return result.value

@router.delete("/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart(cart_id: int, session: SessionDep):
    result = CartService.delete(session, cart_id)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return None

@router.delete("/{cart_id}/coupon", response_model=CartPublic)
def remove_coupon_from_cart(cart_id: int, session: SessionDep):
    result = CartService.remove_coupon(session, cart_id)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return result.value


# ==========================================
# ROTAS DE ITENS DO CARRINHO (ItemCart)
# ==========================================

@router.post("/{cart_id}/items", response_model=ItemCartPublic, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(cart_id: int, item_in: ItemCartCreate, session: SessionDep):
    # A rota consome o ItemCartService passando o ID que veio do carrinho na URL
    result = ItemCartService.add_item(session, cart_id, item_in)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return result.value

@router.put("/{cart_id}/items/{product_id}", response_model=ItemCartPublic)
def update_item_quantity(
    cart_id: int,
    product_id: int,
    amount: Annotated[int, Query(gt=0)],
    session: SessionDep,
):
    result = ItemCartService.update_quantity(session, cart_id, product_id, amount)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return result.value

@router.delete("/{cart_id}/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_cart(cart_id: int, product_id: int, session: SessionDep):
    result = ItemCartService.remove_item(session, cart_id, product_id)
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return None

@router.post("/{cart_id}/checkout", response_model=CheckoutReceipt)
def checkout_cart(
    cart_id: int,
    payment_method: PaymentMethod,
    session: SessionDep,
    coupon_code: str | None = None,
):
    """
    Finaliza o pedido aplicando descontos cumulativos (cupom + método de pagamento).
    """
    result = CheckoutService.process_checkout(
        session, cart_id, payment_method, coupon_code
    )
    if not result.is_success:
        raise HTTPException(status_code=result.error.status_code, detail=result.error.detail)
    return result.value