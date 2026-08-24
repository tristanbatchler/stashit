import pathlib
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, cast

import aiosqlite
from fastapi import Body, Depends, FastAPI, Request
from starlette.status import HTTP_201_CREATED

from db import models, ops, query

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


def _new_slug() -> str:
    return secrets.token_urlsafe(6)


@app.post("/text-stash", status_code=HTTP_201_CREATED)
async def add_text_stash(content: Annotated[str, Body()], db: DB) -> models.Stash:
    try:
        stash = await query.create_stash(db, is_binary=False, slug=_new_slug())
        if stash is None:
            raise RuntimeError("stash insert returned no row")
        await query.create_stash_text_content(db, stash_id=stash.id_, content=content)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return stash


@app.post("/binary-stash", status_code=HTTP_201_CREATED)
async def add_binary_stash(filepath: Annotated[str, Body()], db: DB) -> models.Stash:
    try:
        stash = await query.create_stash(db, is_binary=True, slug=_new_slug())
        if stash is None:
            raise RuntimeError("stash insert returned no row")
        await query.create_stash_binary_path(db, stash_id=stash.id_, path=filepath)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return stash
