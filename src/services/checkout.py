from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Session, select

from src.core.errors import AppError
from src.core.result import Result
from src.database.session import begin_write_transaction
from src.models.cart import Cart
from src.models.coupon import Coupon
from src.models.product import ProductPublic


class PaymentMethod(str, Enum):
    PIX = "pix"
    CREDIT_CARD = "credit_card"


CENT = Decimal("0.01")
PAYMENT_DISCOUNT = {
    PaymentMethod.PIX: Decimal("0.05"),
    PaymentMethod.CREDIT_CARD: Decimal("0"),
}


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_total(
    subtotal: Decimal, coupon_rate: Decimal, method: PaymentMethod
) -> Decimal:
    coupon_discount = money(subtotal * coupon_rate)
    after_coupon = subtotal - coupon_discount
    payment_discount = money(after_coupon * PAYMENT_DISCOUNT[method])
    return money(after_coupon - payment_discount)


class CheckoutItem(BaseModel):
    cart_id: int
    product_id: int
    amount: int
    product: ProductPublic
    unit_price: Decimal
    subtotal: Decimal


class CheckoutReceipt(BaseModel):
    cart_id: int
    subtotal: Decimal
    coupon_code: Optional[str]
    coupon_discount: Decimal
    payment_discount: Decimal
    total: Decimal
    payment_method: PaymentMethod
    items: list[CheckoutItem]


class CheckoutService:
    @staticmethod
    def process_checkout(
        session: Session,
        cart_id: int,
        method: PaymentMethod,
        coupon_code: Optional[str] = None,
    ) -> Result[CheckoutReceipt]:
        begin_write_transaction(session)
        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            session.rollback()
            return Result.fail(AppError.CART_NOT_FOUND)

        if not db_cart.itens:
            session.rollback()
            return Result.fail(AppError.CART_EMPTY)

        coupon = db_cart.coupon
        if coupon_code is not None:
            statement = select(Coupon).where(
                Coupon.code == coupon_code.strip().upper()
            )
            coupon = session.exec(statement).first()
            if not coupon:
                session.rollback()
                return Result.fail(AppError.COUPON_NOT_FOUND)
        elif db_cart.coupon_id is not None and coupon is None:
            session.rollback()
            return Result.fail(AppError.COUPON_NOT_FOUND)

        coupon_rate = Decimal(str(coupon.discount)) if coupon else Decimal("0")
        if not Decimal("0") <= coupon_rate <= Decimal("1"):
            session.rollback()
            return Result.fail(AppError.INVALID_COUPON_DISCOUNT)

        subtotal = Decimal("0.00")
        serialized_items: list[CheckoutItem] = []
        for item in db_cart.itens:
            product = item.product
            if not product:
                session.rollback()
                return Result.fail(AppError.PRODUCT_NOT_FOUND)

            unit_price = Decimal(str(product.price))
            item_subtotal = money(unit_price * item.amount)
            subtotal += item_subtotal
            serialized_items.append(
                CheckoutItem(
                    cart_id=item.cart_id,
                    product_id=item.product_id,
                    amount=item.amount,
                    product=ProductPublic.model_validate(product),
                    unit_price=unit_price,
                    subtotal=item_subtotal,
                )
            )

        coupon_discount = money(subtotal * coupon_rate)
        subtotal_after_coupon = subtotal - coupon_discount
        payment_discount = money(
            subtotal_after_coupon * PAYMENT_DISCOUNT[method]
        )
        total = calculate_total(subtotal, coupon_rate, method)

        receipt = CheckoutReceipt(
            cart_id=cart_id,
            subtotal=subtotal,
            coupon_code=coupon.code if coupon else None,
            coupon_discount=coupon_discount,
            payment_discount=payment_discount,
            total=total,
            payment_method=method,
            items=serialized_items,
        )

        for item in list(db_cart.itens):
            session.delete(item)

        db_cart.coupon_id = None
        session.add(db_cart)
        session.commit()
        return Result.success(receipt)
