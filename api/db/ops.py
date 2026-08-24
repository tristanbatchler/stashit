import logging
import pathlib

import aiosqlite

log = logging.getLogger(pathlib.Path(__file__).name)

_DIR = pathlib.Path(__file__).parent


async def create_tables(db_path: pathlib.Path) -> None:
    schema_sql = (_DIR / "schema.sql").read_text()
    async with aiosqlite.connect(db_path) as conn:
        _ = await conn.executescript(schema_sql)
        await conn.commit()
    log.info(f"db tables ready: {db_path}")
