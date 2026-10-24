from decimal import Decimal


def create_product(client, name="Caneca Python", price="50.00", amount=5):
    response = client.post(
        "/api/v1/products/",
        json={"name": name, "price": price, "amount": amount},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_coupon(client, code="QUERO10", discount=Decimal("0.10")):
    response = client.post(
        "/api/v1/coupons/",
        json={"code": code, "discount": str(discount)},
    )
    assert response.status_code == 201


def create_cart(client, cart_id=200):
    response = client.post("/api/v1/carts/", json={"id": cart_id})
    assert response.status_code == 201
    return cart_id


def test_full_shopping_cart_and_checkout_with_pix_discount(client):
    product_id = create_product(client)
    create_coupon(client)
    create_cart(client)

    add_response = client.post(
        "/api/v1/carts/200/items",
        json={"product_id": product_id, "amount": 1},
    )
    assert add_response.status_code == 201

    coupon_response = client.patch(
        "/api/v1/carts/200/coupon", params={"coupon_code": "QUERO10"}
    )
    assert coupon_response.status_code == 200

    checkout_response = client.post(
        "/api/v1/carts/200/checkout", params={"payment_method": "pix"}
    )
    assert checkout_response.status_code == 200

    receipt = checkout_response.json()
    assert receipt["subtotal"] == "50.00"
    assert receipt["coupon_code"] == "QUERO10"
    assert receipt["coupon_discount"] == "5.00"
    assert receipt["payment_discount"] == "2.25"
    assert receipt["total"] == "42.75"
    assert receipt["payment_method"] == "pix"
    assert receipt["items"][0]["amount"] == 1
    assert receipt["items"][0]["unit_price"] == "50.00"
    assert receipt["items"][0]["subtotal"] == "50.00"

    product = client.get(f"/api/v1/products/{product_id}").json()
    assert product["amount"] == 4
    cart = client.get("/api/v1/carts/200").json()
    assert cart["itens"] == []


def test_checkout_with_coupon_and_credit_card(client):
    product_id = create_product(client)
    create_coupon(client)
    create_cart(client)
    assert client.post(
        "/api/v1/carts/200/items",
        json={"product_id": product_id, "amount": 1},
    ).status_code == 201

    response = client.post(
        "/api/v1/carts/200/checkout",
        params={"payment_method": "credit_card", "coupon_code": " quero10 "},
    )

    assert response.status_code == 200
    receipt = response.json()
    assert receipt["coupon_code"] == "QUERO10"
    assert receipt["coupon_discount"] == "5.00"
    assert receipt["payment_discount"] == "0.00"
    assert receipt["total"] == "45.00"


def test_repeated_adds_are_combined_and_card_without_coupon_has_no_discount(client):
    product_id = create_product(client, amount=3)
    create_cart(client)

    for _ in range(2):
        response = client.post(
            "/api/v1/carts/200/items",
            json={"product_id": product_id, "amount": 1},
        )
        assert response.status_code == 201

    cart = client.get("/api/v1/carts/200").json()
    assert len(cart["itens"]) == 1
    assert cart["itens"][0]["amount"] == 2
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 1

    checkout = client.post(
        "/api/v1/carts/200/checkout",
        params={"payment_method": "credit_card"},
    )

    assert checkout.status_code == 200
    receipt = checkout.json()
    assert receipt["coupon_code"] is None
    assert receipt["coupon_discount"] == "0.00"
    assert receipt["payment_discount"] == "0.00"
    assert receipt["total"] == "100.00"
    assert len(receipt["items"]) == 1
    assert receipt["items"][0]["amount"] == 2
    assert receipt["items"][0]["subtotal"] == "100.00"


def test_invalid_coupon_does_not_complete_checkout(client):
    product_id = create_product(client, amount=2)
    create_cart(client)
    assert client.post(
        "/api/v1/carts/200/items",
        json={"product_id": product_id, "amount": 1},
    ).status_code == 201

    response = client.post(
        "/api/v1/carts/200/checkout",
        params={"payment_method": "pix", "coupon_code": "INVALID"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired coupon."
    assert client.get(f"/api/v1/products/{product_id}").json()["amount"] == 1
    assert len(client.get("/api/v1/carts/200").json()["itens"]) == 1


def test_checkout_rejects_empty_cart(client):
    create_cart(client)

    response = client.post(
        "/api/v1/carts/200/checkout", params={"payment_method": "pix"}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Cannot checkout an empty cart."


def test_checkout_rounds_discount_amounts_to_cents(client):
    product_id = create_product(client, price="0.05", amount=1)
    create_coupon(client, discount=Decimal("0.10"))
    create_cart(client)
    assert client.post(
        "/api/v1/carts/200/items",
        json={"product_id": product_id, "amount": 1},
    ).status_code == 201

    response = client.post(
        "/api/v1/carts/200/checkout",
        params={"payment_method": "credit_card", "coupon_code": "QUERO10"},
    )

    assert response.status_code == 200
    receipt = response.json()
    assert receipt["items"][0]["subtotal"] == "0.05"
    assert receipt["coupon_discount"] == "0.01"
    assert receipt["payment_discount"] == "0.00"
    assert receipt["total"] == "0.04"
    assert (
        Decimal(receipt["subtotal"])
        - Decimal(receipt["coupon_discount"])
        - Decimal(receipt["payment_discount"])
        == Decimal(receipt["total"])
    )


def test_coupon_codes_are_normalized_and_duplicates_are_rejected(client):
    created = client.post(
        "/api/v1/coupons/",
        json={"code": " promo10 ", "discount": "0.10"},
    )
    duplicate = client.post(
        "/api/v1/coupons/",
        json={"code": "PROMO10", "discount": "0.20"},
    )

    assert created.status_code == 201
    assert created.json()["code"] == "PROMO10"
    assert duplicate.status_code == 400


def test_coupon_discount_must_be_between_zero_and_one(client):
    for discount in ("-0.01", "1.01"):
        response = client.post(
            "/api/v1/coupons/",
            json={"code": "INVALID", "discount": discount},
        )
        assert response.status_code == 422
