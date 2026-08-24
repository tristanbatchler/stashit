import pathlib
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, cast

import aiosqlite
from fastapi import Body, Depends, FastAPI, Request
from starlette.status import HTTP_201_CREATED

from db import models, ops, query
from slug_service import new_slug

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


async def get_unique_slug(db: aiosqlite.Connection) -> str:
    MAX_SLUG_ATTEMPTS = 10
    for _ in range(MAX_SLUG_ATTEMPTS):
        proposed = new_slug()
        exists = await query.check_slug_exists(db, slug=proposed)
        if exists is None:
            raise RuntimeError("slug check returned no row")

        if not exists:
            return proposed

    raise RuntimeError(
        f"could not generate a unique slug after {MAX_SLUG_ATTEMPTS} attempts"
    )


@app.get("/")
async def read_root(db: DB):
    return await query.list_stashes(db, limit=5, offset=0)


@app.post("/text-stash", status_code=HTTP_201_CREATED)
async def add_text_stash(content: Annotated[str, Body()], db: DB) -> models.Stash:
    slug = await get_unique_slug(db)
    try:
        stash = await query.create_stash(db, is_binary=False, slug=slug)
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
    slug = await get_unique_slug(db)
    try:
        stash = await query.create_stash(db, is_binary=True, slug=slug)
        if stash is None:
            raise RuntimeError("stash insert returned no row")
        await query.create_stash_binary_path(db, stash_id=stash.id_, path=filepath)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return stash
