from fastapi import APIRouter, status

from src.database.session import SessionDep
from src.schemas.coupon import CouponCreate, CouponPublic
from src.services.coupon import CouponService

router = APIRouter()


@router.post("/", response_model=CouponPublic, status_code=status.HTTP_201_CREATED)
def create_coupon(coupon_in: CouponCreate, session: SessionDep):
    return CouponService.create(session, coupon_in)
