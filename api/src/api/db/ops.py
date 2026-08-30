import logging
import pathlib
from collections.abc import AsyncGenerator
from typing import LiteralString, cast

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from ..settings import settings

file_path = pathlib.Path(__file__)

logger = logging.getLogger(file_path.name)

db_conn_string = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
db_conn_pool = AsyncConnectionPool(
    db_conn_string,
    open=False,
    min_size=5,  # Keep 5 connections ready
    max_size=20,  # Allow up to 20 connections
    timeout=30,  # 30s connection timeout
)


async def get_db_conn() -> AsyncGenerator[AsyncConnection]:
    async with db_conn_pool.connection() as conn:
        # Autocommit queries to run outside the usual `async with db_conn.transaction(): ...` block. This can be useful if
        # you are planning on throwing an exception later and don't want your query to roll back, e.g. in stashes password
        # attempt logging.
        await conn.set_autocommit(True)
        yield conn


async def create_tables() -> None:
    schema_sql = (file_path.parent / "schema.sql").read_text()

    async with await AsyncConnection.connect(db_conn_string) as conn:
        async with conn.cursor() as cursor:
            _ = await cursor.execute(cast(LiteralString, schema_sql))

        await conn.commit()
    logger.info("db tables ready")
