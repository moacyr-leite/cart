from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy.engine import URL
from sqlmodel import Session, SQLModel, create_engine, select

from src.core.errors import AppError
from src.models.cart import Cart, ItemCart, ItemCartCreate
from src.models.product import Product
from src.services.item_cart import ItemCartService


def create_product(client, amount=5):
    response = client.post(
        "/api/v1/products/",
        json={"name": "Produto", "price": "10.00", "amount": amount},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_cart(client, cart_id=1):
    response = client.post("/api/v1/carts/", json={"id": cart_id})
    assert response.status_code == 201


def test_add_update_and_remove_reserve_and_release_stock(client):
    product_id = create_product(client)
    create_cart(client)

    added = client.post(
        "/api/v1/carts/1/items",
        json={"product_id": product_id, "amount": 3},
    )
    assert added.status_code == 201
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 2

    updated = client.put(
        f"/api/v1/carts/1/items/{product_id}", params={"amount": 1}
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == 1
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 4

    exceeds_stock = client.put(
        f"/api/v1/carts/1/items/{product_id}", params={"amount": 6}
    )
    assert exceeds_stock.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 4
    assert client.get("/api/v1/carts/1").json()["itens"][0]["amount"] == 1

    removed = client.delete(f"/api/v1/carts/1/items/{product_id}")
    assert removed.status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5


def test_requesting_more_than_available_reserves_nothing(client):
    product_id = create_product(client, amount=2)
    create_cart(client)

    response = client.post(
        "/api/v1/carts/1/items",
        json={"product_id": product_id, "amount": 3},
    )

    assert response.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 2
    assert client.get("/api/v1/carts/1").json()["itens"] == []


def test_deleting_cart_releases_reserved_stock(client):
    product_id = create_product(client)
    create_cart(client)
    assert client.post(
        "/api/v1/carts/1/items",
        json={"product_id": product_id, "amount": 2},
    ).status_code == 201

    response = client.delete("/api/v1/carts/1")

    assert response.status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5


def test_reserved_product_cannot_be_deleted(client):
    product_id = create_product(client)
    create_cart(client)
    assert client.post(
        "/api/v1/carts/1/items",
        json={"product_id": product_id, "amount": 1},
    ).status_code == 201

    response = client.delete(f"/api/v1/products/{product_id}")

    assert response.status_code == 409
    assert client.get(f"/api/v1/products/{product_id}").status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Produto", "price": "0.00", "amount": 1},
        {"name": "Produto", "price": "-1.00", "amount": 1},
        {"name": "Produto", "price": "1.00", "amount": -1},
        {"name": "   ", "price": "1.00", "amount": 1},
    ],
)
def test_product_rejects_invalid_values(client, payload):
    response = client.post("/api/v1/products/", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("amount", [0, -1])
def test_cart_rejects_non_positive_item_quantity(client, amount):
    product_id = create_product(client)
    create_cart(client)

    response = client.post(
        "/api/v1/carts/1/items",
        json={"product_id": product_id, "amount": amount},
    )

    assert response.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5


@pytest.mark.parametrize("amount", [0, -1])
def test_update_rejects_non_positive_item_quantity(client, amount):
    product_id = create_product(client)
    create_cart(client)
    assert client.post(
        "/api/v1/carts/1/items",
        json={"product_id": product_id, "amount": 1},
    ).status_code == 201

    response = client.put(
        f"/api/v1/carts/1/items/{product_id}", params={"amount": amount}
    )

    assert response.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 4
    assert client.get("/api/v1/carts/1").json()["itens"][0]["amount"] == 1


def test_concurrent_carts_cannot_reserve_the_same_last_unit(tmp_path):
    database_path = tmp_path / "concurrency.db"
    engine = create_engine(
        URL.create("sqlite", database=str(database_path)),
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        product = Product(name="Última unidade", price=Decimal("10.00"), amount=1)
        cart_one = Cart()
        cart_two = Cart()
        session.add_all([product, cart_one, cart_two])
        session.commit()
        session.refresh(product)
        session.refresh(cart_one)
        session.refresh(cart_two)
        product_id = product.id
        cart_ids = [cart_one.id, cart_two.id]

    barrier = Barrier(2)

    def reserve(cart_id: int):
        with Session(engine) as session:
            barrier.wait()
            return ItemCartService.add_item(
                session,
                cart_id,
                ItemCartCreate(product_id=product_id, amount=1),
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(reserve, cart_ids))

    assert sum(result.is_success for result in results) == 1
    failed_result = next(result for result in results if not result.is_success)
    assert failed_result.error is AppError.OUT_OF_STOCK

    with Session(engine) as session:
        product = session.get(Product, product_id)
        items = session.exec(select(ItemCart)).all()
        assert product is not None
        assert product.amount == 0
        assert sum(item.amount for item in items) == 1

    engine.dispose()
