from dataclasses import replace
from uuid import UUID, uuid4

from customers.application.ports import AddressRepository
from customers.domain.address import Address, AddressNotFound


class AddressBook:
    def __init__(self, addresses: AddressRepository) -> None:
        self._addresses = addresses

    async def list(self, user_id: UUID) -> list[Address]:
        return await self._addresses.list(user_id)

    async def add(
        self, user_id: UUID, street: str, postal_code: str, city: str, is_default: bool = False
    ) -> Address:
        address = Address(uuid4(), user_id, street, postal_code, city, is_default)
        await self._save(address)
        return address

    async def update(
        self,
        user_id: UUID,
        address_id: UUID,
        street: str,
        postal_code: str,
        city: str,
        is_default: bool,
    ) -> Address:
        address = await self._find(address_id, user_id)
        address = replace(
            address, street=street, postal_code=postal_code, city=city, is_default=is_default
        )
        await self._save(address)
        return address

    async def delete(self, user_id: UUID, address_id: UUID) -> None:
        await self._find(address_id, user_id)
        await self._addresses.delete(address_id)

    async def _find(self, address_id: UUID, user_id: UUID) -> Address:
        address = await self._addresses.find(address_id, user_id)
        if address is None:
            raise AddressNotFound(address_id)
        return address

    async def _save(self, address: Address) -> None:
        if address.is_default:
            for other in await self._addresses.list(address.user_id):
                if other.is_default and other.id != address.id:
                    await self._addresses.save(replace(other, is_default=False))
        await self._addresses.save(address)
