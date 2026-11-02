from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from src.core.errors import AppError, AppException
from src.database.session import transaction
from src.models.order import Order, utcnow
from src.models.product import Product
from src.schemas.order import (
    CheckoutItem,
    CheckoutReceipt,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)


def build_receipt(order: Order) -> CheckoutReceipt:
    return CheckoutReceipt(
        order_id=order.id,
        cart_id=order.cart_id,
        subtotal=order.subtotal,
        coupon_code=order.coupon_code,
        coupon_discount=order.coupon_discount,
        payment_discount=order.payment_discount,
        total=order.total,
        payment_method=PaymentMethod(order.payment_method),
        status=OrderStatus(order.status),
        payment_status=PaymentStatus(order.payment_status),
        created_at=order.created_at,
        paid_at=order.paid_at,
        cancelled_at=order.cancelled_at,
        items=[
            CheckoutItem(
                product_id=item.product_id,
                product_name=item.product_name,
                amount=item.amount,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ],
    )


class OrderService:
    @staticmethod
    def get(session: Session, order_id: int) -> Order:
        statement = (
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))  # type: ignore[arg-type]
        )
        order = session.exec(statement).first()
        if not order:
            raise AppException(AppError.ORDER_NOT_FOUND)
        return order

    @staticmethod
    def get_by_idempotency_key(session: Session, key: str) -> Order | None:
        statement = (
            select(Order).where(Order.idempotency_key == key).options(selectinload(Order.items))  # type: ignore[arg-type]
        )
        return session.exec(statement).first()

    @staticmethod
    def get_receipt(session: Session, order_id: int) -> CheckoutReceipt:
        return build_receipt(OrderService.get(session, order_id))

    @staticmethod
    def cancel(session: Session, order_id: int) -> CheckoutReceipt:
        with transaction(session):
            order = OrderService.get(session, order_id)
            if order.status == OrderStatus.CANCELLED.value:
                return build_receipt(order)

            if order.status != OrderStatus.PAID.value:
                raise AppException(AppError.ORDER_NOT_CANCELLABLE)

            for item in order.items:
                product = session.get(Product, item.product_id)
                if product:
                    product.amount += item.amount
                    session.add(product)

            order.status = OrderStatus.CANCELLED.value
            order.payment_status = PaymentStatus.REFUNDED.value
            order.cancelled_at = utcnow()
            session.add(order)
            session.flush()

        return OrderService.get_receipt(session, order_id)
