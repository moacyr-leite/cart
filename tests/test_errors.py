from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.order import Order
from src.schemas.order import OrderStatus, PaymentStatus


def create_product(client, name="Produto", price="10.00", amount=5):
    response = client.post(
        "/api/v1/products/",
        json={"name": name, "price": price, "amount": amount},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_cart(client):
    response = client.post("/api/v1/carts/")
    assert response.status_code == 201
    return response.json()["id"]


def create_coupon(client, code="ERRO10", discount=Decimal("0.10")):
    response = client.post(
        "/api/v1/coupons/",
        json={"code": code, "discount": str(discount)},
    )
    assert response.status_code == 201


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/api/v1/carts/999", {}),
        ("delete", "/api/v1/carts/999", {}),
        ("patch", "/api/v1/carts/999/coupon", {"params": {"coupon_code": "ERRO10"}}),
        ("delete", "/api/v1/carts/999/coupon", {}),
        ("post", "/api/v1/carts/999/checkout", {"params": {"payment_method": "pix"}}),
        ("post", "/api/v1/carts/999/items", {"json": {"product_id": 1, "amount": 1}}),
        ("put", "/api/v1/carts/999/items/1", {"params": {"amount": 1}}),
        ("delete", "/api/v1/carts/999/items/1", {}),
    ],
)
def test_missing_cart_returns_404(client, method, path, kwargs):
    response = client.request(method, path, **kwargs)

    assert response.status_code == 404
    assert response.json() == {"detail": "Cart not found."}


def test_missing_product_returns_404(client):
    read_response = client.get("/api/v1/products/999")
    delete_response = client.delete("/api/v1/products/999")

    assert read_response.status_code == 404
    assert read_response.json() == {"detail": "Product not found."}
    assert delete_response.status_code == 404
    assert delete_response.json() == {"detail": "Product not found."}


def test_adding_missing_product_to_cart_returns_404(client):
    cart_id = create_cart(client)

    response = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": 999, "amount": 1},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found."}


def test_updating_or_removing_missing_item_returns_404(client):
    product_id = create_product(client)
    cart_id = create_cart(client)

    update_response = client.put(
        f"/api/v1/carts/{cart_id}/items/{product_id}",
        params={"amount": 1},
    )
    remove_response = client.delete(f"/api/v1/carts/{cart_id}/items/{product_id}")

    expected = {"detail": "This product is not present in the specified cart."}
    assert update_response.status_code == 404
    assert update_response.json() == expected
    assert remove_response.status_code == 404
    assert remove_response.json() == expected


def test_adding_missing_coupon_to_cart_returns_400(client):
    cart_id = create_cart(client)

    response = client.patch(
        f"/api/v1/carts/{cart_id}/coupon",
        params={"coupon_code": "NAOEXISTE"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid or expired coupon."}


def test_pending_order_cannot_be_cancelled(client, session: Session):
    order = Order(
        cart_id=None,
        subtotal=Decimal("10.00"),
        total=Decimal("10.00"),
        payment_method="pix",
        status=OrderStatus.PENDING.value,
        payment_status=PaymentStatus.PENDING.value,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    assert order.id is not None

    response = client.post(f"/api/v1/orders/{order.id}/cancel")

    assert response.status_code == 409
    assert response.json() == {"detail": "Only paid orders can be cancelled."}


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"payment_method": "boleto"},
    ],
)
def test_checkout_rejects_missing_or_invalid_payment_method(client, params):
    cart_id = create_cart(client)

    response = client.post(f"/api/v1/carts/{cart_id}/checkout", params=params)

    assert response.status_code == 422
