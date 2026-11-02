from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.core.errors import AppError, AppException
from src.database.session import transaction
from src.models.coupon import Coupon
from src.schemas.coupon import CouponCreate


class CouponService:
    @staticmethod
    def create(session: Session, coupon_in: CouponCreate) -> Coupon:
        with transaction(session):
            statement = select(Coupon).where(Coupon.code == coupon_in.code)
            if session.exec(statement).first():
                raise AppException(AppError.COUPON_ALREADY_EXISTS)

            db_coupon = Coupon(
                code=coupon_in.code,
                discount=coupon_in.discount,
            )
            session.add(db_coupon)
            try:
                session.flush()
            except IntegrityError:
                raise AppException(AppError.COUPON_ALREADY_EXISTS) from None
            session.refresh(db_coupon)
        return db_coupon

    @staticmethod
    def get_by_code(session: Session, code: str) -> Coupon:
        statement = select(Coupon).where(Coupon.code == code.strip().upper())
        db_coupon = session.exec(statement).first()
        if not db_coupon:
            raise AppException(AppError.COUPON_NOT_FOUND)
        return db_coupon
