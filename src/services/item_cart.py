from sqlalchemy import update
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from src.core.errors import AppError, AppException
from src.database.session import transaction
from src.models.cart import Cart, ItemCart
from src.models.product import Product
from src.schemas.cart import ItemCartCreate


class ItemCartService:
    @staticmethod
    def _load(session: Session, cart_id: int, product_id: int) -> ItemCart:
        statement = (
            select(ItemCart)
            .where(
                ItemCart.cart_id == cart_id,
                ItemCart.product_id == product_id,
            )
            .options(selectinload(ItemCart.product))  # type: ignore[arg-type]
        )
        db_item = session.exec(statement).first()
        if not db_item:
            raise AppException(AppError.ITEM_NOT_FOUND_IN_CART)
        return db_item

    @staticmethod
    def add_item(session: Session, cart_id: int, item_in: ItemCartCreate) -> ItemCart:
        if item_in.amount <= 0:
            raise AppException(AppError.INVALID_QUANTITY)

        with transaction(session):
            if not session.get(Cart, cart_id):
                raise AppException(AppError.CART_NOT_FOUND)

            if not session.get(Product, item_in.product_id):
                raise AppException(AppError.PRODUCT_NOT_FOUND)

            stock_update = session.exec(
                update(Product)
                .where(
                    col(Product.id) == item_in.product_id,
                    col(Product.amount) >= item_in.amount,
                )
                .values(amount=Product.amount - item_in.amount)
            )
            if stock_update.rowcount != 1:
                raise AppException(AppError.OUT_OF_STOCK)

            db_item = session.get(ItemCart, (cart_id, item_in.product_id))
            if db_item:
                db_item.amount += item_in.amount
            else:
                db_item = ItemCart(
                    cart_id=cart_id,
                    product_id=item_in.product_id,
                    amount=item_in.amount,
                )
            session.add(db_item)
            session.flush()
        return ItemCartService._load(session, cart_id, item_in.product_id)

    @staticmethod
    def update_quantity(
        session: Session, cart_id: int, product_id: int, new_amount: int
    ) -> ItemCart:
        if new_amount <= 0:
            raise AppException(AppError.INVALID_QUANTITY)

        with transaction(session):
            if not session.get(Cart, cart_id):
                raise AppException(AppError.CART_NOT_FOUND)

            db_item = session.get(ItemCart, (cart_id, product_id))
            if not db_item:
                raise AppException(AppError.ITEM_NOT_FOUND_IN_CART)

            difference = new_amount - db_item.amount
            if difference > 0:
                stock_update = session.exec(
                    update(Product)
                    .where(col(Product.id) == product_id, col(Product.amount) >= difference)
                    .values(amount=Product.amount - difference)
                )
                if stock_update.rowcount != 1:
                    raise AppException(AppError.OUT_OF_STOCK)
            elif difference < 0:
                stock_update = session.exec(
                    update(Product)
                    .where(col(Product.id) == product_id)
                    .values(amount=Product.amount - difference)
                )
                if stock_update.rowcount != 1:
                    raise AppException(AppError.PRODUCT_NOT_FOUND)

            db_item.amount = new_amount
            session.add(db_item)
            session.flush()
        return ItemCartService._load(session, cart_id, product_id)

    @staticmethod
    def remove_item(session: Session, cart_id: int, product_id: int) -> None:
        with transaction(session):
            if not session.get(Cart, cart_id):
                raise AppException(AppError.CART_NOT_FOUND)

            db_item = session.get(ItemCart, (cart_id, product_id))
            if not db_item:
                raise AppException(AppError.ITEM_NOT_FOUND_IN_CART)

            stock_update = session.exec(
                update(Product)
                .where(col(Product.id) == product_id)
                .values(amount=Product.amount + db_item.amount)
            )
            if stock_update.rowcount != 1:
                raise AppException(AppError.PRODUCT_NOT_FOUND)

            session.delete(db_item)
