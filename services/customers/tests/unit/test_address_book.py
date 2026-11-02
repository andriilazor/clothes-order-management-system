from uuid import uuid4

import pytest
from customers.application.address_book import AddressBook
from customers.application.ports import AddressRepository
from customers.domain.address import AddressNotFound


@pytest.fixture
def book(addresses: AddressRepository) -> AddressBook:
    return AddressBook(addresses)


@pytest.mark.req("FR-CUS-04", "US-02")
async def test_a_new_default_address_unmarks_the_previous_default(book: AddressBook) -> None:
    user_id = uuid4()
    first = await book.add(user_id, "Main 1", "00-001", "Warsaw", is_default=True)
    second = await book.add(user_id, "Side 2", "30-001", "Krakow", is_default=True)

    defaults = [a.id for a in await book.list(user_id) if a.is_default]
    assert defaults == [second.id]
    assert first.id not in defaults


@pytest.mark.req("FR-CUS-04")
async def test_updates_an_address(book: AddressBook) -> None:
    user_id = uuid4()
    address = await book.add(user_id, "Main 1", "00-001", "Warsaw")

    await book.update(user_id, address.id, "Main 5", "00-002", "Warsaw", is_default=True)

    assert (await book.list(user_id))[0].street == "Main 5"
    assert (await book.list(user_id))[0].is_default


@pytest.mark.req("FR-CUS-04")
async def test_deletes_an_address(book: AddressBook) -> None:
    user_id = uuid4()
    address = await book.add(user_id, "Main 1", "00-001", "Warsaw")

    await book.delete(user_id, address.id)

    assert await book.list(user_id) == []


@pytest.mark.req("FR-CUS-05", "US-02")
async def test_a_customer_cannot_change_or_see_another_customers_address(
    book: AddressBook,
) -> None:
    owner, intruder = uuid4(), uuid4()
    address = await book.add(owner, "Main 1", "00-001", "Warsaw")

    with pytest.raises(AddressNotFound):
        await book.update(intruder, address.id, "Hacked", "00-001", "Warsaw", is_default=False)
    with pytest.raises(AddressNotFound):
        await book.delete(intruder, address.id)
    assert await book.list(intruder) == []
