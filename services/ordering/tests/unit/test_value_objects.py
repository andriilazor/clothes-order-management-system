import pytest
from ordering.domain.errors import InvalidQuantity, InvalidSku, QuantityLimitExceeded
from ordering.domain.value_objects import Quantity, Sku


# "One SKU per product, size and colour": the code is stored upper-case.
def test_sku_parse_normalises_to_upper_case() -> None:
    # Act
    sku = Sku.parse("dress-red-m")

    # Assert
    assert sku == Sku("DRESS-RED-M")


# A SKU code must not be empty or contain spaces.
@pytest.mark.parametrize("raw", ["", "   ", "DRESS RED M"])
def test_sku_rejects_empty_or_spaced_code(raw: str) -> None:
    # Act & Assert
    with pytest.raises(InvalidSku):
        Sku.parse(raw)


# "Item rejected, quantity must be above zero" and "at most 5 units".
@pytest.mark.parametrize("value", [0, -1, 6])
def test_quantity_rejects_values_outside_one_to_five(value: int) -> None:
    # Act & Assert
    with pytest.raises(InvalidQuantity):
        Quantity(value)


# Adding quantities returns a new value; the operands stay unchanged.
def test_quantity_add_returns_new_quantity() -> None:
    # Arrange
    two = Quantity(2)

    # Act
    total = two.add(Quantity(3))

    # Assert
    assert total == Quantity(5)
    assert two == Quantity(2)


# "At most 5 units of one size and colour per order".
def test_quantity_add_rejects_sum_above_five() -> None:
    # Act & Assert
    with pytest.raises(QuantityLimitExceeded):
        Quantity(4).add(Quantity(2))
