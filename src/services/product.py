from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.core.errors import AppError, AppException
from src.database.session import transaction
from src.models.cart import ItemCart
from src.models.product import Product
from src.schemas.product import ProductCreate


class ProductService:
    @staticmethod
    def create(session: Session, product_in: ProductCreate) -> Product:
        normalized_name = product_in.name.strip()
        name_key = normalized_name.lower()

        with transaction(session):
            statement = select(Product).where(Product.name_key == name_key)
            if session.exec(statement).first():
                raise AppException(AppError.PRODUCT_ALREADY_EXISTS)

            db_product = Product(
                name=normalized_name,
                name_key=name_key,
                price=product_in.price,
                amount=product_in.amount,
            )
            session.add(db_product)
            try:
                session.flush()
            except IntegrityError:
                raise AppException(AppError.PRODUCT_ALREADY_EXISTS) from None
            session.refresh(db_product)
        return db_product

    @staticmethod
    def get(session: Session, product_id: int) -> Product:
        db_product = session.get(Product, product_id)
        if not db_product:
            raise AppException(AppError.PRODUCT_NOT_FOUND)
        return db_product

    @staticmethod
    def gets(session: Session, skip: int = 0, limit: int = 100) -> list[Product]:
        return list(session.exec(select(Product).offset(skip).limit(limit)).all())

    @staticmethod
    def delete(session: Session, product_id: int) -> None:
        with transaction(session):
            db_product = session.get(Product, product_id)
            if not db_product:
                raise AppException(AppError.PRODUCT_NOT_FOUND)

            reserved_item = session.exec(
                select(ItemCart).where(ItemCart.product_id == product_id)
            ).first()
            if reserved_item:
                raise AppException(AppError.PRODUCT_IN_CART)

            session.delete(db_product)
