import logging
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from enum import StrEnum
from os import getenv
from pathlib import Path
from sys import exit
from typing import Annotated

from dotenv import load_dotenv
from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg import AsyncConnection
from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_501_NOT_IMPLEMENTED,
)

from db import models, ops, query
from slug_service import new_slug

logger = logging.getLogger(Path(__file__).name)


class ConfigKey(StrEnum):
    DB_DATABASE = "DB_DATABASE"
    DB_USERNAME = "DB_USERNAME"
    DB_PASSWORD = "DB_PASSWORD"
    DB_HOST = "DB_HOST"
    DB_PORT = "DB_PORT"

config: dict[ConfigKey, str] = {}

_ = load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

for config_key in ConfigKey:
    value = getenv(config_key)
    if value is None:
        logger.fatal("Missing configuration key %s", config_key)
        exit(1)

    config[config_key] = value


db_conn_string = f"postgresql://{config[ConfigKey.DB_USERNAME]}:{config[ConfigKey.DB_PASSWORD]}@{config[ConfigKey.DB_HOST]}:{config[ConfigKey.DB_PORT]}/{config[ConfigKey.DB_DATABASE]}"
db_conn_pool = AsyncConnectionPool(db_conn_string, open=False)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    await ops.create_tables(db_conn_string)
    await db_conn_pool.open()
    yield
    await db_conn_pool.close()


app: FastAPI = FastAPI(lifespan=lifespan)

async def get_db_conn() -> AsyncGenerator[AsyncConnection]:
    async with db_conn_pool.connection() as conn:
	    yield conn


DBConn = Annotated[AsyncConnection, Depends(get_db_conn)]

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


@stashes_router.get("/")
async def list_stashes(db_conn: DBConn) -> Sequence[models.Stash]:
    return await query.list_stashes(db_conn, limit=5, offset=0)

MAX_SLUG_ATTEMPTS = 10
async def try_with_slug(operation: Callable[[int], Awaitable[None]], is_binary: bool, db_conn: DBConn) -> models.Stash:
    for _ in range(MAX_SLUG_ATTEMPTS):
            slug = new_slug()
            try:
                stash = await query.create_stash(db_conn, is_binary=is_binary, slug=slug)
                if stash is None:
                    raise RuntimeError("stash insert returned no row")
                await operation(stash.id_)
                await db_conn.commit()
                return stash
            except UniqueViolation:
                await db_conn.rollback()
                continue
            except Exception:
                await db_conn.rollback()
                raise
    
    
    raise RuntimeError("too many slug collisions")


@stashes_router.post("/text", status_code=HTTP_201_CREATED)
async def add_text_stash(content: Annotated[str, Body()], db_conn: DBConn) -> models.Stash:
    async def operation(stash_id: int):
        await query.create_stash_text_content(db_conn, stash_id=stash_id, content=content)
    return await try_with_slug(operation, is_binary=False, db_conn=db_conn)
    


@stashes_router.post("/file", status_code=HTTP_201_CREATED)
async def add_binary_stash(filepath: str, db_conn: DBConn) -> models.Stash:
    async def operation(stash_id: int):
        await query.create_stash_binary_path(db_conn, stash_id=stash_id, file_path=filepath)
    return await try_with_slug(operation, is_binary=True, db_conn=db_conn)



@stashes_router.get(path="/{slug}", status_code=HTTP_200_OK)
async def get_stash(slug: str, db_conn: DBConn) -> str:
    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug")
        
    if stash.is_binary:
        raise HTTPException(HTTP_501_NOT_IMPLEMENTED, detail="We don't know how to show it to you yet")
        
    content = await query.get_stash_text_content(db_conn, stash_id=stash.id_)
    if content is None:
        raise RuntimeError("Stash content select returned no rows")
    return content