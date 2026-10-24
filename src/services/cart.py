from typing import List
from sqlmodel import Session, select
from src.models.cart import Cart, CartCreate
from src.models.coupon import Coupon
from src.core.result import Result
from src.core.errors import AppError
from src.database.session import begin_write_transaction
from src.models.product import Product

class CartService:

    @staticmethod
    def create(session: Session, cart_in: CartCreate) -> Result[Cart]:
        # Se o ID foi fornecido, verifica duplicidade
        if cart_in.id:
            statement = select(Cart).where(Cart.id == cart_in.id)
            if session.exec(statement).first():
                return Result.fail(AppError.CART_ALREADY_EXISTS)

        db_cart = Cart(id=cart_in.id) if cart_in.id else Cart()
        session.add(db_cart)
        session.commit()
        session.refresh(db_cart)
        return Result.success(db_cart)

    @staticmethod
    def get(session: Session, cart_id: int) -> Result[Cart]:
        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            return Result.fail(AppError.CART_NOT_FOUND)
        return Result.success(db_cart)
        
    @staticmethod
    def gets(session: Session, skip: int = 0, limit: int = 100) -> List[Cart]:
        # Listagens não costumam falhar com regras de negócio, retornam vazio [] se nada houver
        return session.exec(select(Cart).offset(skip).limit(limit)).all()

    @staticmethod
    def add_coupon(session: Session, cart_id: int, coupon_code: str) -> Result[Cart]:
        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            return Result.fail(AppError.CART_NOT_FOUND)
            
        statement = select(Coupon).where(Coupon.code == coupon_code.strip().upper())
        db_coupon = session.exec(statement).first()
        if not db_coupon:
            return Result.fail(AppError.COUPON_NOT_FOUND)
            
        db_cart.coupon_id = db_coupon.id
        session.add(db_cart)
        session.commit()
        session.refresh(db_cart)
        return Result.success(db_cart)

    @staticmethod
    def remove_coupon(session: Session, cart_id: int) -> Result[Cart]:
        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            return Result.fail(AppError.CART_NOT_FOUND)
            
        db_cart.coupon_id = None
        session.add(db_cart)
        session.commit()
        session.refresh(db_cart)
        return Result.success(db_cart)

    @staticmethod
    def delete(session: Session, cart_id: int) -> Result[None]:
        begin_write_transaction(session)
        db_cart = session.get(Cart, cart_id)
        if not db_cart:
            session.rollback()
            return Result.fail(AppError.CART_NOT_FOUND)

        for item in list(db_cart.itens):
            product = session.get(Product, item.product_id)
            if not product:
                session.rollback()
                return Result.fail(AppError.PRODUCT_NOT_FOUND)
            product.amount += item.amount
            session.add(product)

        session.delete(db_cart)
        session.commit()
        return Result.success(None)
