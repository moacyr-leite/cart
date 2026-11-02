from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.core.errors import AppError, AppException
from src.core.idempotency import normalize_idempotency_key, request_fingerprint
from src.database.session import transaction
from src.models.coupon import Coupon
from src.models.order import Order, OrderItem, utcnow
from src.schemas.order import (
    CheckoutItem,
    CheckoutReceipt,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from src.services.cart import CartService
from src.services.order import OrderService, build_receipt

CENT = Decimal("0.01")
PAYMENT_DISCOUNT = {
    PaymentMethod.PIX: Decimal("0.05"),
    PaymentMethod.CREDIT_CARD: Decimal("0"),
}


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def quote(
    subtotal: Decimal, coupon_rate: Decimal, method: PaymentMethod
) -> tuple[Decimal, Decimal, Decimal]:
    """Retorna (desconto do cupom, desconto do pagamento, total)."""
    coupon_discount = money(subtotal * coupon_rate)
    after_coupon = subtotal - coupon_discount
    payment_discount = money(after_coupon * PAYMENT_DISCOUNT[method])
    return coupon_discount, payment_discount, money(after_coupon - payment_discount)


def calculate_total(subtotal: Decimal, coupon_rate: Decimal, method: PaymentMethod) -> Decimal:
    return quote(subtotal, coupon_rate, method)[2]


def _ensure_matching_request(order: Order, cart_id: int, fingerprint: str) -> None:
    if order.cart_id != cart_id:
        raise AppException(AppError.IDEMPOTENCY_KEY_REUSED)
    if order.request_fingerprint and order.request_fingerprint != fingerprint:
        raise AppException(AppError.IDEMPOTENCY_KEY_CONFLICT)


class CheckoutService:
    @staticmethod
    def process_checkout(
        session: Session,
        cart_id: int,
        method: PaymentMethod,
        coupon_code: str | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutReceipt:
        idempotency_key = normalize_idempotency_key(idempotency_key)
        coupon_key = coupon_code.strip().upper() if coupon_code else ""
        fingerprint = request_fingerprint("checkout", cart_id, method.value, coupon_key)

        try:
            with transaction(session):
                if idempotency_key:
                    existing = OrderService.get_by_idempotency_key(session, idempotency_key)
                    if existing:
                        _ensure_matching_request(existing, cart_id, fingerprint)
                        return build_receipt(existing)

                db_cart = CartService.get(session, cart_id)
                if not db_cart.itens:
                    raise AppException(AppError.CART_EMPTY)

                coupon = db_cart.coupon
                if coupon_code is not None:
                    statement = select(Coupon).where(Coupon.code == coupon_code.strip().upper())
                    coupon = session.exec(statement).first()
                    if not coupon:
                        raise AppException(AppError.COUPON_NOT_FOUND)
                elif db_cart.coupon_id is not None and coupon is None:
                    raise AppException(AppError.COUPON_NOT_FOUND)

                coupon_rate = Decimal(str(coupon.discount)) if coupon else Decimal("0")
                if not Decimal("0") <= coupon_rate <= Decimal("1"):
                    raise AppException(AppError.INVALID_COUPON_DISCOUNT)

                subtotal = Decimal("0.00")
                serialized_items: list[CheckoutItem] = []
                for item in db_cart.itens:
                    product = item.product
                    if not product:
                        raise AppException(AppError.PRODUCT_NOT_FOUND)

                    unit_price = Decimal(str(product.price))
                    item_subtotal = money(unit_price * item.amount)
                    subtotal += item_subtotal
                    serialized_items.append(
                        CheckoutItem(
                            product_id=item.product_id,
                            product_name=product.name,
                            amount=item.amount,
                            unit_price=unit_price,
                            subtotal=item_subtotal,
                        )
                    )

                coupon_discount, payment_discount, total = quote(subtotal, coupon_rate, method)

                now = utcnow()
                order = Order(
                    cart_id=cart_id,
                    subtotal=subtotal,
                    coupon_code=coupon.code if coupon else None,
                    coupon_discount=coupon_discount,
                    payment_discount=payment_discount,
                    total=total,
                    payment_method=method.value,
                    status=OrderStatus.PAID.value,
                    payment_status=PaymentStatus.APPROVED.value,
                    idempotency_key=idempotency_key,
                    request_fingerprint=fingerprint,
                    created_at=now,
                    paid_at=now,
                )
                session.add(order)
                session.flush()
                order_id = order.id
                assert order_id is not None

                for checkout_item in serialized_items:
                    session.add(
                        OrderItem(
                            order_id=order_id,
                            product_id=checkout_item.product_id,
                            product_name=checkout_item.product_name,
                            amount=checkout_item.amount,
                            unit_price=checkout_item.unit_price,
                            subtotal=checkout_item.subtotal,
                        )
                    )

                for cart_item in list(db_cart.itens):
                    session.delete(cart_item)

                db_cart.coupon_id = None
                db_cart.coupon = None
                session.add(db_cart)
        except IntegrityError:
            if idempotency_key:
                existing = OrderService.get_by_idempotency_key(session, idempotency_key)
                if existing:
                    _ensure_matching_request(existing, cart_id, fingerprint)
                    return build_receipt(existing)
            raise

        return OrderService.get_receipt(session, order_id)
