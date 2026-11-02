import pytest


def test_create_product_success(client):
    response = client.post(
        "/api/v1/products/", json={"name": "Teclado Mecânico", "price": 299.90, "amount": 10}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Teclado Mecânico"
    assert "id" in data


def test_create_product_duplicate_name_fails(client):
    # Cadastra o primeiro
    client.post("/api/v1/products/", json={"name": "Mouse Gamer", "price": 150.0, "amount": 5})

    # Tenta cadastrar outro igual
    response = client.post(
        "/api/v1/products/", json={"name": "Mouse Gamer", "price": 180.0, "amount": 2}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "A product with this name is already registered."


def test_get_product_not_found(client):
    response = client.get("/api/v1/products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


def test_product_name_is_case_insensitive_unique(client):
    first = client.post(
        "/api/v1/products/",
        json={"name": "Mouse Gamer", "price": 150.0, "amount": 5},
    )
    duplicate = client.post(
        "/api/v1/products/",
        json={"name": "  mouse gamer  ", "price": 180.0, "amount": 2},
    )

    assert first.status_code == 201
    assert first.json()["name"] == "Mouse Gamer"
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "A product with this name is already registered."


def test_list_products_returns_only_the_current_test_database(client):
    first = client.post(
        "/api/v1/products/",
        json={"name": "Produto A", "price": 10.0, "amount": 1},
    )
    second = client.post(
        "/api/v1/products/",
        json={"name": "Produto B", "price": 20.0, "amount": 2},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get("/api/v1/products/")

    assert response.status_code == 200
    assert {product["id"] for product in response.json()} == {
        first.json()["id"],
        second.json()["id"],
    }


def test_delete_unreserved_product(client):
    created = client.post(
        "/api/v1/products/",
        json={"name": "Produto descartável", "price": 10.0, "amount": 1},
    )
    assert created.status_code == 201
    product_id = created.json()["id"]

    response = client.delete(f"/api/v1/products/{product_id}")

    assert response.status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").status_code == 404


def test_sqlite_foreign_keys_are_enabled(session):
    if session.get_bind().dialect.name != "sqlite":
        pytest.skip("SQLite-specific behavior")

    assert session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
