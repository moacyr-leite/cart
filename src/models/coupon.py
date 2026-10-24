from typing import Optional
from decimal import Decimal
from sqlmodel import Field, SQLModel
from pydantic import field_validator


# ==========================================
# 1. COUPON BASE
# Campos que são comuns e públicos para todos os schemas.
# ==========================================
class CouponBase(SQLModel):
    code: str = Field(index=True, unique=True, min_length=1)
    discount: Decimal = Field(ge=0, le=1, max_digits=5, decimal_places=4)


# ==========================================
# 2. COUPON (Tabela do Banco de Dados)
# Único com `table=True`. Representa a linha física no banco.
# ==========================================
class Coupon(CouponBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


# ==========================================
# 3. COUPON CREATE (Schema de Entrada)
# O que a API espera receber ao criar um novo cupom.
# Inclui um validador para padronizar o código do cupom em caixa alta.
# ==========================================
class CouponCreate(CouponBase):
    
    @field_validator("code")
    @classmethod
    def force_uppercase(cls, v: str) -> str:
        normalized = v.strip().upper()
        if not normalized:
            raise ValueError("Coupon code must not be empty.")
        return normalized


# ==========================================
# 4. COUPON PUBLIC (Schema de Saída)
# O que a API devolve de forma segura.
# (Perfeito para aninhar dentro do CartPublic que fizemos antes!)
# ==========================================
class CouponPublic(CouponBase):
    id: int
