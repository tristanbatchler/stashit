import pathlib
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, cast

import aiosqlite
from fastapi import Depends, FastAPI, Request

from db import ops, query

DB_PATH = pathlib.Path(__file__).parent / "stash.db"


async def _init_db() -> aiosqlite.Connection:
    """Create/open the database and run schema."""
    aiosqlite.register_adapter(
        datetime,
        lambda val: val.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
    )
    await ops.create_tables(DB_PATH)
    return await aiosqlite.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await _init_db()
    app.state.db = db
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)


def get_db(request: Request) -> aiosqlite.Connection:
    app = cast(FastAPI, request.app)
    return cast(aiosqlite.Connection, app.state.db)


DB = Annotated[aiosqlite.Connection, Depends(get_db)]


@app.get("/")
async def read_root(db: DB):
    return await query.list_stashes(db, limit=5, offset=0)
