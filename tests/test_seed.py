from sqlmodel import Session, select

from src.database.seed import COUPONS, PRODUCTS, seed
from src.models.coupon import Coupon
from src.models.product import Product


def test_seed_is_idempotent(session: Session):
    seed(session)
    seed(session)

    products = session.exec(select(Product)).all()
    coupons = session.exec(select(Coupon)).all()

    assert len(products) == len(PRODUCTS)
    assert len(coupons) == len(COUPONS)
    assert all(product.name_key == product.name.strip().lower() for product in products)
