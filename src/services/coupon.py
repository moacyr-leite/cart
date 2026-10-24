from typing import List
from sqlmodel import Session, select
from src.models.coupon import Coupon, CouponCreate
from src.core.result import Result
from src.core.errors import AppError

class CouponService:

    @staticmethod
    def create(session: Session, coupon_in: CouponCreate) -> Result[Coupon]:
        """
        Cadastra um novo cupom. 
        Garante que o código seja único e padronizado em caixa alta.
        """
        # Como o CouponCreate tem o validador para maiúsculas, o código já vem tratado
        statement = select(Coupon).where(Coupon.code == coupon_in.code)
        if session.exec(statement).first():
            return Result.fail(AppError.COUPON_ALREADY_EXISTS)

        db_coupon = Coupon(
            code=coupon_in.code,
            discount=coupon_in.discount
        )
        session.add(db_coupon)
        session.commit()
        session.refresh(db_coupon)
        return Result.success(db_coupon)

    @staticmethod
    def get_by_code(session: Session, code: str) -> Result[Coupon]:
        """
        Busca um cupom ativo por seu código de texto.
        """
        statement = select(Coupon).where(Coupon.code == code.strip().upper())
        db_coupon = session.exec(statement).first()
        if not db_coupon:
            return Result.fail(AppError.COUPON_NOT_FOUND)
        return Result.success(db_coupon)
