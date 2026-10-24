from fastapi import APIRouter, HTTPException, status

from src.database.session import SessionDep
from src.models.coupon import CouponCreate, CouponPublic
from src.services.coupon import CouponService

router = APIRouter()


@router.post("/", response_model=CouponPublic, status_code=status.HTTP_201_CREATED)
def create_coupon(coupon_in: CouponCreate, session: SessionDep):
    result = CouponService.create(session, coupon_in)
    if not result.is_success:
        raise HTTPException(
            status_code=result.error.status_code,
            detail=result.error.detail,
        )
    return result.value
