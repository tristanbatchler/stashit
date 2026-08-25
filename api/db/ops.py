import logging
import pathlib
from typing import LiteralString, cast

import psycopg

file_path = pathlib.Path(__file__)

logger = logging.getLogger(file_path.name)

async def create_tables(db_conn_string: str) -> None: 
    schema_sql = (file_path.parent / "schema.sql").read_text()

    async with await psycopg.AsyncConnection.connect(db_conn_string) as conn:
        async with conn.cursor() as cursor:
            _ = await cursor.execute(cast(LiteralString, schema_sql))

        await conn.commit()
    logger.info("db tables ready")
