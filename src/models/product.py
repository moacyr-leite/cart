from decimal import Decimal

from sqlalchemy import event
from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, min_length=1)
    name_key: str = Field(index=True, unique=True, min_length=1)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    amount: int = Field(default=0, ge=0)


@event.listens_for(Product, "before_insert")
@event.listens_for(Product, "before_update")
def _refresh_name_key(mapper, connection, target: Product) -> None:
    target.name_key = target.name.strip().lower()
