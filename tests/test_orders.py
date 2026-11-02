def create_product(client, name="Caneca Python", price="50.00", amount=5):
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


def add_item(client, cart_id, product_id, amount=1):
    response = client.post(
        f"/api/v1/carts/{cart_id}/items",
        json={"product_id": product_id, "amount": amount},
    )
    assert response.status_code == 201
    return response.json()


def checkout(client, cart_id, headers=None, **params):
    return client.post(
        f"/api/v1/carts/{cart_id}/checkout",
        params={"payment_method": "pix", **params},
        headers=headers,
    )


def test_checkout_persists_order_and_order_can_be_read(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id)

    response = checkout(client, cart_id)

    assert response.status_code == 200
    receipt = response.json()
    assert receipt["order_id"] > 0

    stored = client.get(f"/api/v1/orders/{receipt['order_id']}")
    assert stored.status_code == 200
    assert stored.json() == receipt


def test_checkout_with_same_idempotency_key_returns_same_order(client):
    product_id = create_product(client, amount=2)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id)

    headers = {"Idempotency-Key": "order-301"}
    first = checkout(client, cart_id, headers=headers)
    second = checkout(client, cart_id, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 1
    assert client.get(f"/api/v1/carts/{cart_id}").json()["itens"] == []


def test_idempotency_key_cannot_be_reused_for_another_cart(client):
    product_id = create_product(client, amount=5)
    cart_one = create_cart(client)
    cart_two = create_cart(client)
    add_item(client, cart_one, product_id)
    add_item(client, cart_two, product_id)

    headers = {"Idempotency-Key": "shared-key"}
    first = checkout(client, cart_one, headers=headers)
    second = checkout(client, cart_two, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"] == "This idempotency key was already used by another cart."
    assert client.get(f"/api/v1/carts/{cart_two}").json()["itens"][0]["amount"] == 1


def test_order_not_found(client):
    response = client.get("/api/v1/orders/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found."


def test_order_stores_item_snapshot(client):
    product_id = create_product(client, price="50.00")
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id, amount=2)

    receipt = checkout(client, cart_id).json()

    assert receipt["items"] == [
        {
            "product_id": product_id,
            "product_name": "Caneca Python",
            "amount": 2,
            "unit_price": "50.00",
            "subtotal": "100.00",
        }
    ]


def test_checkout_marks_order_paid_and_payment_approved(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id)

    receipt = checkout(client, cart_id).json()

    assert receipt["status"] == "paid"
    assert receipt["payment_status"] == "approved"
    assert receipt["paid_at"] is not None
    assert receipt["cancelled_at"] is None


def test_cancelling_paid_order_restocks_and_refunds(client):
    product_id = create_product(client, amount=5)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id, amount=2)

    receipt = checkout(client, cart_id).json()
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 3

    cancelled = client.post(f"/api/v1/orders/{receipt['order_id']}/cancel")

    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["status"] == "cancelled"
    assert body["payment_status"] == "refunded"
    assert body["cancelled_at"] is not None
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5

    repeated = client.post(f"/api/v1/orders/{receipt['order_id']}/cancel")

    assert repeated.status_code == 200
    assert repeated.json() == body
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 5


def test_cancel_order_not_found(client):
    response = client.post("/api/v1/orders/999/cancel")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found."


def test_checkout_rejects_invalid_idempotency_key(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id)

    for header in ("invalid key!", "a" * 256):
        response = checkout(client, cart_id, headers={"Idempotency-Key": header})

        assert response.status_code == 422
        assert response.json()["detail"].startswith("Idempotency-Key must be")


def test_same_idempotency_key_with_different_payload_returns_conflict(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id)

    headers = {"Idempotency-Key": "checkout-conflict"}
    first = checkout(client, cart_id, headers=headers, payment_method="pix")
    second = checkout(client, cart_id, headers=headers, payment_method="credit_card")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"] == (
        "This idempotency key was already used with a different request."
    )
    assert (
        first.json()["order_id"]
        == client.get(f"/api/v1/orders/{first.json()['order_id']}").json()["order_id"]
    )


def test_same_idempotency_key_with_different_coupon_returns_conflict(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id)

    for code in ("PRIMEIRO", "SEGUNDO"):
        response = client.post(
            "/api/v1/coupons/",
            json={"code": code, "discount": "0.10"},
        )
        assert response.status_code == 201

    headers = {"Idempotency-Key": "coupon-conflict"}
    first = checkout(client, cart_id, headers=headers, coupon_code="PRIMEIRO")
    second = checkout(client, cart_id, headers=headers, coupon_code="SEGUNDO")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"] == (
        "This idempotency key was already used with a different request."
    )


def test_same_idempotency_key_with_normalized_coupon_returns_same_order(client):
    product_id = create_product(client)
    cart_id = create_cart(client)
    add_item(client, cart_id, product_id)
    assert (
        client.post(
            "/api/v1/coupons/",
            json={"code": "NORMALIZADO", "discount": "0.10"},
        ).status_code
        == 201
    )

    headers = {"Idempotency-Key": " normalized-key "}
    first = checkout(client, cart_id, headers=headers, coupon_code=" normalizado ")
    second = checkout(client, cart_id, headers=headers, coupon_code="NORMALIZADO")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
