import pathlib
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import aiosqlite
from db import ops
from fastapi import FastAPI, Request

DB_PATH = pathlib.Path(__file__).parent / "stash.db"


async def _init_db() -> aiosqlite.Connection:
    """Create/open the database and run schema."""
    aiosqlite.register_adapter(
        datetime,
        lambda val: val.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
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
    return request.app.state.db
