from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from ordering.adapters.outbound.sql.seeder import DEMO_CART_ID, EMPTY_CART_ID
from ordering.bootstrap.app import create_app
from ordering.bootstrap.settings import Settings


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(Settings(environment="test"))) as client:
        yield client


@pytest.fixture
def seeded_client() -> Iterator[TestClient]:
    with TestClient(create_app(Settings(environment="development"))) as client:
        yield client


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
@pytest.mark.parametrize(
    ("sku", "quantity", "code"),
    [("SKU-1", 0, "InvalidQuantity"), ("SKU 1", 1, "InvalidSku")],
)
def test_add_item_with_invalid_value_returns_422(
    client: TestClient, sku: str, quantity: int, code: str
) -> None:
    # Act
    response = client.post(
        f"/api/v1/carts/{uuid4()}/items", json={"sku": sku, "quantity": quantity}
    )

    # Assert
    assert response.status_code == 422
    assert response.json()["code"] == code


# "Cart summary": a saved cart is read back.
def test_get_cart_returns_saved_cart(client: TestClient) -> None:
    # Arrange
    cart_id = str(uuid4())
    client.post(f"/api/v1/carts/{cart_id}/items", json={"sku": "SKU-1", "quantity": 2})

    # Act
    response = client.get(f"/api/v1/carts/{cart_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["items"] == [{"sku": "SKU-1", "quantity": 2}]


# An unknown cart maps to 404.
def test_get_unknown_cart_returns_404(client: TestClient) -> None:
    # Act
    response = client.get(f"/api/v1/carts/{uuid4()}")

    # Assert
    assert response.status_code == 404
    assert response.json()["code"] == "CartNotFound"


# "Item removed from cart": 200 and the cart without the item.
def test_remove_item_returns_cart_without_item(client: TestClient) -> None:
    # Arrange
    cart_id = str(uuid4())
    client.post(f"/api/v1/carts/{cart_id}/items", json={"sku": "SKU-1", "quantity": 2})

    # Act
    response = client.delete(f"/api/v1/carts/{cart_id}/items/SKU-1")

    # Assert
    assert response.status_code == 200
    assert response.json()["items"] == []


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


# "Order status for the customer": placed orders are listed.
def test_list_orders_returns_placed_order(client: TestClient) -> None:
    # Arrange
    cart_id = str(uuid4())
    client.post(f"/api/v1/carts/{cart_id}/items", json={"sku": "SKU-1", "quantity": 2})
    order = client.post("/api/v1/orders", json={"cart_id": cart_id}).json()

    # Act
    response = client.get("/api/v1/orders")

    # Assert
    assert response.status_code == 200
    assert response.json() == [order]


# Development start seeds a demo cart that is readable at once.
def test_development_start_seeds_demo_cart(seeded_client: TestClient) -> None:
    # Act
    response = seeded_client.get(f"/api/v1/carts/{DEMO_CART_ID}")

    # Assert
    assert response.status_code == 200
    assert response.json()["items"] == [
        {"sku": "DRESS-RED-M", "quantity": 4},
        {"sku": "JEANS-BLUE-32", "quantity": 1},
    ]


# The seeded edge cases are rejected with domain errors.
@pytest.mark.parametrize(
    ("path", "body", "code"),
    [
        (
            f"/api/v1/carts/{DEMO_CART_ID}/items",
            {"sku": "DRESS-RED-M", "quantity": 2},
            "QuantityLimitExceeded",
        ),
        ("/api/v1/orders", {"cart_id": str(EMPTY_CART_ID)}, "EmptyCart"),
    ],
)
def test_seeded_edge_cases_return_422(
    seeded_client: TestClient, path: str, body: dict[str, object], code: str
) -> None:
    # Act
    response = seeded_client.post(path, json=body)

    # Assert
    assert response.status_code == 422
    assert response.json()["code"] == code
