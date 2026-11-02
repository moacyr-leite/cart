import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, select

from src.database.session import build_engine, get_session
from src.main import app
from src.models.cart import Cart, ItemCart
from src.models.coupon import Coupon
from src.models.order import Order, OrderItem
from src.models.product import Product

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def _truncate_postgres_tables(engine: Engine) -> None:
    tables = ", ".join(f'"{table.name}"' for table in SQLModel.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.exec_driver_sql(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE")


@pytest.fixture(name="engine")
def engine_fixture(tmp_path: Path) -> Iterator[Engine]:
    if TEST_DATABASE_URL:
        engine = build_engine(TEST_DATABASE_URL, pool_pre_ping=True)
        SQLModel.metadata.create_all(engine)
        _truncate_postgres_tables(engine)
        try:
            yield engine
        finally:
            _truncate_postgres_tables(engine)
            engine.dispose()
        return

    database_path = tmp_path / "test.db"
    engine = build_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    SQLModel.metadata.create_all(engine)

    try:
        yield engine
    finally:
        SQLModel.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(autouse=True)
def empty_database(engine: Engine) -> None:
    with Session(engine) as session:
        for model in (Product, Coupon, Cart, ItemCart, Order, OrderItem):
            assert session.exec(select(model)).first() is None, (
                f"{model.__name__} leaked from another test."
            )


@pytest.fixture(name="session")
def session_fixture(engine: Engine) -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine: Engine) -> Iterator[TestClient]:
    def get_session_override() -> Iterator[Session]:
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)
