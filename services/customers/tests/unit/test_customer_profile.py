from uuid import uuid4

import pytest
from customers.application.customer_profile import CustomerProfile
from customers.application.ports import ProfileRepository


@pytest.mark.req("FR-CUS-03")
async def test_a_new_customer_has_an_empty_profile(profiles: ProfileRepository) -> None:
    user_id = uuid4()

    profile = await CustomerProfile(profiles).get(user_id)

    assert (profile.user_id, profile.name, profile.phone) == (user_id, None, None)


@pytest.mark.req("FR-CUS-03")
async def test_updates_the_name_and_phone(profiles: ProfileRepository) -> None:
    user_id = uuid4()
    customer_profile = CustomerProfile(profiles)

    await customer_profile.update(user_id, "Anna Kowalska", "+48 600 100 200")

    profile = await customer_profile.get(user_id)
    assert (profile.name, profile.phone) == ("Anna Kowalska", "+48 600 100 200")
