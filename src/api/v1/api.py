from fastapi import APIRouter
from src.api.v1.routers import carts, coupons, products

api_router = APIRouter()

# Registra os grupos de rotas com seus respectivos prefixos e tags (para o Swagger)
api_router.include_router(carts.router, prefix="/carts", tags=["Carts"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["Coupons"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
