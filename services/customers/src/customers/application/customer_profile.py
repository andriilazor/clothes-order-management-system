from uuid import UUID

from customers.application.ports import ProfileRepository
from customers.domain.profile import Profile


class CustomerProfile:
    def __init__(self, profiles: ProfileRepository) -> None:
        self._profiles = profiles

    async def get(self, user_id: UUID) -> Profile:
        return await self._profiles.find(user_id) or Profile(user_id)

    async def update(self, user_id: UUID, name: str | None, phone: str | None) -> Profile:
        profile = Profile(user_id, name, phone)
        await self._profiles.save(profile)
        return profile
