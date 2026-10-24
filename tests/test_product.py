def test_create_product_success(client):
    response = client.post("/api/v1/products/", json={
        "name": "Teclado Mecânico",
        "price": 299.90,
        "amount": 10
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Teclado Mecânico"
    assert "id" in data

def test_create_product_duplicate_name_fails(client):
    # Cadastra o primeiro
    client.post("/api/v1/products/", json={"name": "Mouse Gamer", "price": 150.0, "amount": 5})
    
    # Tenta cadastrar outro igual
    response = client.post("/api/v1/products/", json={"name": "Mouse Gamer", "price": 180.0, "amount": 2})
    
    assert response.status_code == 400
    assert response.json()["detail"] == "A product with this name is already registered."

def test_get_product_not_found(client):
    response = client.get("/api/v1/products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."
