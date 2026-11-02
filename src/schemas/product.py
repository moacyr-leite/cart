from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(min_length=1)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(ProductBase):
    amount: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Product name must not be empty.")
        return normalized


class ProductPublic(ProductBase):
    id: int
    amount: int
