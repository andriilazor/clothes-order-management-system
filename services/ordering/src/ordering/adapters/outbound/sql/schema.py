import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine

from ordering.adapters.outbound.sql.tables import metadata

MIGRATIONS = Path(__file__).parent / "migrations"


async def prepare_schema(engine: AsyncEngine) -> None:
    if engine.dialect.name == "sqlite":
        async with engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        return
    database_url = engine.url.render_as_string(hide_password=False)
    await asyncio.to_thread(_upgrade_to_head, database_url)


def _upgrade_to_head(database_url: str) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")
