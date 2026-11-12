import os
from dataclasses import dataclass
from typing import Self

IN_MEMORY_DATABASE = "sqlite+aiosqlite://"


@dataclass(frozen=True)
class Settings:
    database_url: str = IN_MEMORY_DATABASE
    environment: str = "development"

    @classmethod
    def from_environment(cls) -> Self:
        return cls(
            database_url=os.environ.get("ORDERING_DATABASE_URL", IN_MEMORY_DATABASE),
            environment=os.environ.get("ORDERING_ENVIRONMENT", "development"),
        )

    @property
    def seeds_demo_data(self) -> bool:
        return self.environment == "development"
