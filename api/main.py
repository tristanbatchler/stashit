import pathlib
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, cast

import aiosqlite
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_501_NOT_IMPLEMENTED,
)

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

# Allow the SvelteKit dev server (and built site) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")
stashes_router = APIRouter(prefix="/stashes")

api_router.include_router(stashes_router)
app.include_router(api_router)


def get_db(request: Request) -> aiosqlite.Connection:
    app = cast(FastAPI, request.app)
    return cast(aiosqlite.Connection, app.state.db)


DB = Annotated[aiosqlite.Connection, Depends(get_db)]


async def get_unique_slug(db: DB) -> str:
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


@stashes_router.get("/")
async def read_root(db: DB):
    return await query.list_stashes(db, limit=5, offset=0)


@stashes_router.post("/text", status_code=HTTP_201_CREATED)
async def add_text_stash(content: str, db: DB) -> models.Stash:
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


@stashes_router.post("/file", status_code=HTTP_201_CREATED)
async def add_binary_stash(filepath: str, db: DB) -> models.Stash:
    slug = await get_unique_slug(db)
    try:
        stash = await query.create_stash(db, is_binary=True, slug=slug)
        if stash is None:
            raise RuntimeError("stash insert returned no row")
        await query.create_stash_binary_path(db, stash_id=stash.id_, file_path=filepath)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return stash


@stashes_router.get("/{slug}", status_code=HTTP_200_OK)
async def get_stash(slug: str, db: DB) -> str:
    stash = await query.get_stash_by_slug(db, slug=slug)
    if stash is None:
        raise HTTPException(HTTP_404_NOT_FOUND, "Stash does not exist by that slug")
    if stash.is_binary:
        raise HTTPException(
            HTTP_501_NOT_IMPLEMENTED,
            "This is a valid stash, but we don't know how to show it to you yet.",
        )
    content = await query.get_stash_text_content(db, stash_id=stash.id_)
    if content is None:
        raise RuntimeError("stash text content select returned no row")
    return content
