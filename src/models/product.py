from decimal import Decimal
from typing import Optional
from pydantic import field_validator
from sqlmodel import Field, SQLModel


# ==========================================
# 1. PRODUCT BASE
# Campos comuns que todo produto possui.
# ==========================================
class ProductBase(SQLModel):
    name: str = Field(index=True, min_length=1)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


# ==========================================
# 2. PRODUCT (Tabela do Banco de Dados)
# Único com `table=True`. Representa a estrutura física no banco.
# ==========================================
class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: int = Field(default=0, ge=0)


# ==========================================
# 3. PRODUCT CREATE (Schema de Entrada)
# O que a API recebe ao cadastrar um novo produto.
# ==========================================
class ProductCreate(ProductBase):
    amount: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Product name must not be empty.")
        return normalized


# ==========================================
# 4. PRODUCT PUBLIC (Schema de Saída)
# O que a API devolve para o front-end de forma segura.
# Perfeito para alimentar o `ItemCartPublic` que fizemos antes.
# ==========================================
class ProductPublic(ProductBase):
    id: int
    amount: int
