from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Profile:
    user_id: UUID
    name: str | None = None
    phone: str | None = None
