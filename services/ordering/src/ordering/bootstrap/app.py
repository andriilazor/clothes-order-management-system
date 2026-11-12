import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from ordering.adapters.inbound.errors import handle_domain_error
from ordering.adapters.inbound.http import create_router
from ordering.adapters.outbound.sql.database import create_engine
from ordering.adapters.outbound.sql.repositories import SqlCartRepository, SqlOrderRepository
from ordering.adapters.outbound.sql.schema import prepare_schema
from ordering.adapters.outbound.sql.seeder import seed_demo_carts
from ordering.application.ports import Repositories
from ordering.bootstrap.settings import Settings
from ordering.domain.errors import DomainError


def create_app(settings: Settings | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    settings = settings or Settings.from_environment()
    engine = create_engine(settings.database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def repositories() -> AsyncIterator[Repositories]:
        async with sessions() as session:
            yield Repositories(SqlCartRepository(session), SqlOrderRepository(session))

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await prepare_schema(engine)
        if settings.seeds_demo_data:
            async with sessions() as session:
                await seed_demo_carts(session)
        yield
        await engine.dispose()

    app = FastAPI(title="Ordering", lifespan=lifespan)
    app.include_router(create_router(repositories))
    app.add_exception_handler(DomainError, handle_domain_error)
    return app
