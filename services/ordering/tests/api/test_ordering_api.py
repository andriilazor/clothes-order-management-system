from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from ordering.bootstrap.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# "Add item to cart": 200 and the cart with the item.
def test_add_item_returns_200_with_cart(client: TestClient) -> None:
    # Arrange
    cart_id = str(uuid4())

    # Act
    response = client.post(f"/api/v1/carts/{cart_id}/items", json={"sku": "SKU-1", "quantity": 2})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"id": cart_id, "items": [{"sku": "SKU-1", "quantity": 2}]}


# A business rule violation maps to 422 with a stable code.
def test_add_item_with_invalid_quantity_returns_422(client: TestClient) -> None:
    # Act
    response = client.post(f"/api/v1/carts/{uuid4()}/items", json={"sku": "SKU-1", "quantity": 0})

    # Assert
    assert response.status_code == 422
    assert response.json()["code"] == "InvalidQuantity"


# "Place order": 201 and a placed order for the cart.
def test_place_order_returns_201(client: TestClient) -> None:
    # Arrange
    cart_id = str(uuid4())
    client.post(f"/api/v1/carts/{cart_id}/items", json={"sku": "SKU-1", "quantity": 2})

    # Act
    response = client.post("/api/v1/orders", json={"cart_id": cart_id})

    # Assert
    assert response.status_code == 201
    assert response.json()["cart_id"] == cart_id
    assert response.json()["status"] == "placed"


# "Duplicate order submission ignored": the second submission returns the same order.
def test_duplicate_order_submission_returns_same_order(client: TestClient) -> None:
    # Arrange
    cart_id = str(uuid4())
    client.post(f"/api/v1/carts/{cart_id}/items", json={"sku": "SKU-1", "quantity": 2})
    first = client.post("/api/v1/orders", json={"cart_id": cart_id})

    # Act
    second = client.post("/api/v1/orders", json={"cart_id": cart_id})

    # Assert
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


# An unknown cart maps to 404 with a stable code.
def test_place_order_for_unknown_cart_returns_404(client: TestClient) -> None:
    # Act
    response = client.post("/api/v1/orders", json={"cart_id": str(uuid4())})

    # Assert
    assert response.status_code == 404
    assert response.json()["code"] == "CartNotFound"
