from fastapi import APIRouter

from src.database.session import SessionDep
from src.schemas.order import CheckoutReceipt
from src.services.order import OrderService

router = APIRouter()


@router.get("/{order_id}", response_model=CheckoutReceipt)
def read_order(order_id: int, session: SessionDep):
    return OrderService.get_receipt(session, order_id)


@router.post("/{order_id}/cancel", response_model=CheckoutReceipt)
def cancel_order(order_id: int, session: SessionDep):
    return OrderService.cancel(session, order_id)
