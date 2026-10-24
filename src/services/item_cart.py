from sqlmodel import Session, select
from sqlalchemy import update

from src.core.errors import AppError
from src.core.result import Result
from src.database.session import begin_write_transaction
from src.models.cart import Cart, ItemCart, ItemCartCreate
from src.models.product import Product


class ItemCartService:
    @staticmethod
    def add_item(session: Session, cart_id: int, item_in: ItemCartCreate) -> Result[ItemCart]:
        if item_in.amount <= 0:
            return Result.fail(AppError.INVALID_QUANTITY)

        begin_write_transaction(session)
        stock_update = session.exec(
            update(Product)
            .where(
                Product.id == item_in.product_id,
                Product.amount >= item_in.amount,
            )
            .values(amount=Product.amount - item_in.amount)
        )
        if stock_update.rowcount != 1:
            cart_exists = session.get(Cart, cart_id) is not None
            product_exists = session.get(Product, item_in.product_id) is not None
            session.rollback()
            if not cart_exists:
                return Result.fail(AppError.CART_NOT_FOUND)
            if not product_exists:
                return Result.fail(AppError.PRODUCT_NOT_FOUND)
            return Result.fail(AppError.OUT_OF_STOCK)

        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            session.rollback()
            return Result.fail(AppError.CART_NOT_FOUND)

        statement = select(ItemCart).where(
            ItemCart.cart_id == cart_id,
            ItemCart.product_id == item_in.product_id,
        )
        db_item = session.exec(statement).first()

        if db_item:
            db_item.amount += item_in.amount
        else:
            db_item = ItemCart(
                cart_id=cart_id,
                product_id=item_in.product_id,
                amount=item_in.amount,
            )
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return Result.success(db_item)

    @staticmethod
    def update_quantity(
        session: Session, cart_id: int, product_id: int, new_amount: int
    ) -> Result[ItemCart]:
        if new_amount <= 0:
            return Result.fail(AppError.INVALID_QUANTITY)

        begin_write_transaction(session)
        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            session.rollback()
            return Result.fail(AppError.CART_NOT_FOUND)

        statement = select(ItemCart).where(
            ItemCart.cart_id == cart_id,
            ItemCart.product_id == product_id,
        )
        db_item = session.exec(statement).first()
        if not db_item:
            session.rollback()
            return Result.fail(AppError.ITEM_NOT_FOUND_IN_CART)

        difference = new_amount - db_item.amount
        if difference > 0:
            stock_update = session.exec(
                update(Product)
                .where(Product.id == product_id, Product.amount >= difference)
                .values(amount=Product.amount - difference)
            )
            if stock_update.rowcount != 1:
                product_exists = session.get(Product, product_id) is not None
                session.rollback()
                if not product_exists:
                    return Result.fail(AppError.PRODUCT_NOT_FOUND)
                return Result.fail(AppError.OUT_OF_STOCK)
        elif difference < 0:
            stock_update = session.exec(
                update(Product)
                .where(Product.id == product_id)
                .values(amount=Product.amount - difference)
            )
            if stock_update.rowcount != 1:
                session.rollback()
                return Result.fail(AppError.PRODUCT_NOT_FOUND)

        db_item.amount = new_amount
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return Result.success(db_item)

    @staticmethod
    def remove_item(session: Session, cart_id: int, product_id: int) -> Result[None]:
        begin_write_transaction(session)
        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            session.rollback()
            return Result.fail(AppError.CART_NOT_FOUND)

        statement = select(ItemCart).where(
            ItemCart.cart_id == cart_id,
            ItemCart.product_id == product_id,
        )
        db_item = session.exec(statement).first()
        if not db_item:
            session.rollback()
            return Result.fail(AppError.ITEM_NOT_FOUND_IN_CART)

        stock_update = session.exec(
            update(Product)
            .where(Product.id == product_id)
            .values(amount=Product.amount + db_item.amount)
        )
        if stock_update.rowcount != 1:
            session.rollback()
            return Result.fail(AppError.PRODUCT_NOT_FOUND)

        session.delete(db_item)
        session.commit()
        return Result.success(None)
