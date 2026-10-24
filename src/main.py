from fastapi import FastAPI
from sqlmodel import SQLModel

from src.api.v1.api import api_router
from src.database.session import engine

# Inicializa o FastAPI
app = FastAPI(
    title="Cart API",
    description="Backend escalável estruturado com FastAPI e SQLModel",
    version="1.0.0"
)

SQLModel.metadata.create_all(engine)

# 🔌 Acopla o ecossistema de rotas versionadas da V1 (/api/v1/carts, /api/v1/products...)
app.include_router(api_router, prefix="/api/v1")
