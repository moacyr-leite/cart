from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from sqlmodel import Session, select

from src.core.errors import AppError, AppException
from src.models.cart import Cart, ItemCart
from src.models.product import Product
from src.schemas.cart import ItemCartCreate
from src.services.item_cart import ItemCartService


def create_product(client, amount=5):
    response = client.post(
        "/api/v1/products/",
        json={"name": "Produto", "price": "10.00", "amount": amount},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_cart(client):
    response = client.post("/api/v1/carts/")
    assert response.status_code == 201
    return response.json()["id"]


def create_coupon(client, code="CUPOM10", discount="0.10"):
    response = client.post(
        "/api/v1/coupons/",
        json={"code": code, "discount": discount},
    )
    assert response.status_code == 201


def test_cart_id_is_generated_by_the_server(client):
    first_cart = create_cart(client)
    second_cart = create_cart(client)

    assert first_cart > 0
    assert second_cart > first_cart


def test_list_carts_returns_only_the_current_test_database(client):
    first_cart = create_cart(client)
    second_cart = create_cart(client)

    response = client.get("/api/v1/carts/")

    assert response.status_code == 200
    assert {cart["id"] for cart in response.json()} == {first_cart, second_cart}


def test_cart_coupon_can_be_removed(client):
    create_coupon(client)
    cart_id = create_cart(client)

    applied = client.patch(
        f"/api/v1/carts/{cart_id}/coupon",
        params={"coupon_code": "CUPOM10"},
    )
    assert applied.status_code == 200
    assert applied.json()["coupon"]["code"] == "CUPOM10"

    removed = client.delete(f"/api/v1/carts/{cart_id}/coupon")

    assert removed.status_code == 200
    assert removed.json()["coupon"] is None
    assert removed.json()["coupon_id"] is None


def test_add_update_and_remove_reserve_and_release_stock(client):
    product_id = create_product(client)
    cart_id = create_cart(client)

    added = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": product_id, "amount": 3},
    )
    assert added.status_code == 201
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 2

    updated = client.put(f"/api/v1/carts/{cart_id}/items/{product_id}", params={"amount": 1})
    assert updated.status_code == 200
    assert updated.json()["amount"] == 1
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 4

    exceeds_stock = client.put(f"/api/v1/carts/{cart_id}/items/{product_id}", params={"amount": 6})
    assert exceeds_stock.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 4
    assert client.get(f"/api/v1/carts/{cart_id}").json()["itens"][0]["amount"] == 1

    removed = client.delete(f"/api/v1/carts/{cart_id}/items/{product_id}")
    assert removed.status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5


def test_requesting_more_than_available_reserves_nothing(client):
    product_id = create_product(client, amount=2)
    cart_id = create_cart(client)

    response = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": product_id, "amount": 3},
    )

    assert response.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 2
    assert client.get(f"/api/v1/carts/{cart_id}").json()["itens"] == []


def test_deleting_cart_releases_reserved_stock(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    assert (
        client.post(
            f"/api/v1/carts/{cart_id}/items",
            json={"product_id": product_id, "amount": 2},
        ).status_code
        == 201
    )

    response = client.delete(f"/api/v1/carts/{cart_id}")

    assert response.status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5


def test_reserved_product_cannot_be_deleted(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    assert (
        client.post(
            f"/api/v1/carts/{cart_id}/items",
            json={"product_id": product_id, "amount": 1},
        ).status_code
        == 201
    )

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
    cart_id = create_cart(client)

    response = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": product_id, "amount": amount},
    )

    assert response.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5


@pytest.mark.parametrize("amount", [0, -1])
def test_update_rejects_non_positive_item_quantity(client, amount):
    product_id = create_product(client)
    cart_id = create_cart(client)
    assert (
        client.post(
            f"/api/v1/carts/{cart_id}/items",
            json={"product_id": product_id, "amount": 1},
        ).status_code
        == 201
    )

    response = client.put(f"/api/v1/carts/{cart_id}/items/{product_id}", params={"amount": amount})

    assert response.status_code == 422
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 4
    assert client.get(f"/api/v1/carts/{cart_id}").json()["itens"][0]["amount"] == 1


def test_concurrent_carts_cannot_reserve_the_same_last_unit(engine):
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
            try:
                ItemCartService.add_item(
                    session,
                    cart_id,
                    ItemCartCreate(product_id=product_id, amount=1),
                )
                return True
            except AppException as exc:
                return exc.error

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(reserve, cart_ids))

    assert sum(result is True for result in results) == 1
    failed_result = next(result for result in results if result is not True)
    assert failed_result is AppError.OUT_OF_STOCK

    with Session(engine) as session:
        product = session.get(Product, product_id)
        items = session.exec(select(ItemCart)).all()
        assert product is not None
        assert product.amount == 0
        assert sum(item.amount for item in items) == 1
