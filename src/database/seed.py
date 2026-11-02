from decimal import Decimal
from typing import TypedDict

from sqlmodel import Session, select

from src.database.session import engine, transaction
from src.models.coupon import Coupon
from src.models.product import Product


class ProductSeed(TypedDict):
    name: str
    price: Decimal
    amount: int


class CouponSeed(TypedDict):
    code: str
    discount: Decimal


PRODUCTS: list[ProductSeed] = [
    {"name": "Mouse sem fio", "price": Decimal("79.90"), "amount": 5},
    {"name": "Teclado mecânico", "price": Decimal("249.90"), "amount": 2},
    {"name": "Fone de ouvido bluetooth", "price": Decimal("159.90"), "amount": 3},
    {"name": "Webcam Full HD", "price": Decimal("199.90"), "amount": 1},
    {"name": "Carregador USB-C", "price": Decimal("119.90"), "amount": 3},
]

COUPONS: list[CouponSeed] = [
    {"code": "OFERTA5", "discount": Decimal("0.05")},
    {"code": "PROMO10", "discount": Decimal("0.10")},
]


def seed(session: Session) -> None:
    with transaction(session):
        for data in PRODUCTS:
            name_key = data["name"].strip().lower()
            existing_product = session.exec(
                select(Product).where(Product.name_key == name_key)
            ).first()
            if not existing_product:
                session.add(Product(name_key=name_key, **data))

        for coupon_data in COUPONS:
            existing_coupon = session.exec(
                select(Coupon).where(Coupon.code == coupon_data["code"])
            ).first()
            if not existing_coupon:
                session.add(Coupon(**coupon_data))


def main() -> None:
    with Session(engine, expire_on_commit=False) as session:
        seed(session)


if __name__ == "__main__":
    main()
