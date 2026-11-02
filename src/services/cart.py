from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from src.core.errors import AppError, AppException
from src.database.session import transaction
from src.models.cart import Cart, ItemCart
from src.models.coupon import Coupon
from src.models.product import Product


class CartService:
    @staticmethod
    def _load(session: Session, cart_id: int) -> Cart | None:
        statement = (
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                selectinload(Cart.coupon),  # type: ignore[arg-type]
                selectinload(Cart.itens).selectinload(  # type: ignore[arg-type]
                    ItemCart.product  # type: ignore[arg-type]
                ),
            )
        )
        return session.exec(statement).first()

    @staticmethod
    def create(session: Session) -> Cart:
        with transaction(session):
            db_cart = Cart()
            session.add(db_cart)
            session.flush()
            cart_id = db_cart.id
        assert cart_id is not None
        return CartService.get(session, cart_id)

    @staticmethod
    def get(session: Session, cart_id: int) -> Cart:
        db_cart = CartService._load(session, cart_id)
        if not db_cart:
            raise AppException(AppError.CART_NOT_FOUND)
        return db_cart

    @staticmethod
    def gets(session: Session, skip: int = 0, limit: int = 100) -> list[Cart]:
        statement = (
            select(Cart)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Cart.coupon),  # type: ignore[arg-type]
                selectinload(Cart.itens).selectinload(  # type: ignore[arg-type]
                    ItemCart.product  # type: ignore[arg-type]
                ),
            )
        )
        return list(session.exec(statement).all())

    @staticmethod
    def add_coupon(session: Session, cart_id: int, coupon_code: str) -> Cart:
        with transaction(session):
            db_cart = session.get(Cart, cart_id)
            if not db_cart:
                raise AppException(AppError.CART_NOT_FOUND)

            statement = select(Coupon).where(Coupon.code == coupon_code.strip().upper())
            db_coupon = session.exec(statement).first()
            if not db_coupon:
                raise AppException(AppError.COUPON_NOT_FOUND)

            db_cart.coupon_id = db_coupon.id
            session.add(db_cart)
            session.flush()
        return CartService.get(session, cart_id)

    @staticmethod
    def remove_coupon(session: Session, cart_id: int) -> Cart:
        with transaction(session):
            db_cart = session.get(Cart, cart_id)
            if not db_cart:
                raise AppException(AppError.CART_NOT_FOUND)

            db_cart.coupon_id = None
            db_cart.coupon = None
            session.add(db_cart)
            session.flush()
        return CartService.get(session, cart_id)

    @staticmethod
    def delete(session: Session, cart_id: int) -> None:
        with transaction(session):
            db_cart = CartService._load(session, cart_id)
            if not db_cart:
                raise AppException(AppError.CART_NOT_FOUND)

            for item in list(db_cart.itens):
                product = session.get(Product, item.product_id)
                if not product:
                    raise AppException(AppError.PRODUCT_NOT_FOUND)
                product.amount += item.amount
                session.add(product)

            session.delete(db_cart)
