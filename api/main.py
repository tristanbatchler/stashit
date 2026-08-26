import logging
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from enum import StrEnum
from os import getenv
from pathlib import Path
from sys import exit
from typing import Annotated
from uuid import uuid4

import aiofiles
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Body,
    Depends,
    FastAPI,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from psycopg import AsyncConnection
from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from db import models, ops, query
from db.query import GetStashBySlugRow
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

class Message(BaseModel):
    detail: str


api_router = APIRouter(prefix="/api/v1", responses={HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}})
stashes_router = APIRouter(prefix="/stashes")

api_router.include_router(stashes_router)
app.include_router(api_router)


@stashes_router.get("/", status_code=HTTP_200_OK, response_model=Sequence[models.Stash])
async def list_stashes(page: int, take: int, db_conn: DBConn) -> Sequence[models.Stash]:
    return await query.list_stashes(db_conn, limit=take, offset=(page-1) * take)

MAX_SLUG_ATTEMPTS = 10
async def try_with_slug(operation: Callable[[int], Awaitable[None]], is_binary: bool, db_conn: DBConn) -> models.Stash:
    for _ in range(MAX_SLUG_ATTEMPTS):
        slug = new_slug()
        try:
            async with db_conn.transaction():
                stash = await query.create_stash(db_conn, is_binary=is_binary, slug=slug)
                if stash is None:
                    raise RuntimeError("stash insert returned no row")
                await operation(stash.id_)
                return stash
        except UniqueViolation:
            continue
    
    
    raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Could not generate a unique slug")


@stashes_router.post("/text", status_code=HTTP_201_CREATED, response_model=models.Stash)
async def add_text_stash(content: Annotated[str, Body()], db_conn: DBConn) -> models.Stash:
    async def operation(stash_id: int):
        await query.create_stash_text_content(db_conn, stash_id=stash_id, content=content)
    return await try_with_slug(operation, is_binary=False, db_conn=db_conn)
    


@stashes_router.post("/file", status_code=HTTP_201_CREATED, response_model=models.Stash, responses={HTTP_422_UNPROCESSABLE_CONTENT: {"model": Message}})
async def add_binary_stash(file: UploadFile, db_conn: DBConn) -> models.Stash:

    try:
        uploads_dir = Path(__file__).parent / "uploads"
        uploads_dir.mkdir(exist_ok=True)

        if file.filename is None:
            raise HTTPException(HTTP_422_UNPROCESSABLE_CONTENT, "The uploaded file must have a valid filename")

        if file.size in (None, 0):
            raise HTTPException(HTTP_422_UNPROCESSABLE_CONTENT, "The uploaded file is empty or corrupted")


        uuid = uuid4().hex
        unique_folder = uploads_dir / uuid
        unique_folder.mkdir(parents=True, exist_ok=True)
        
        sanitized_filename = Path(file.filename).name
        destination = unique_folder / sanitized_filename

        bytes_written = 0
        async with aiofiles.open(destination, "wb") as buffer:
            while chunk := await file.read(1024 * 64):
                _ = await buffer.write(chunk)
                bytes_written += len(chunk)
                #progress = (bytes_written / file.size) * 100
                # TODO: It'd be nice to stream the progress back to the client...

        async def operation(stash_id: int):
            await query.create_stash_binary_path(db_conn, stash_id=stash_id, file_path=str(destination))
        return await try_with_slug(operation, is_binary=True, db_conn=db_conn)

    finally:
        await file.close()

@stashes_router.get("/file/{slug}", status_code=HTTP_200_OK, response_class=FileResponse, responses={HTTP_404_NOT_FOUND: {"model": Message}, HTTP_200_OK: {"content": {"application/octet-stream": {}}}})
async def get_file_stash(slug: str, db_conn: DBConn) -> FileResponse:
    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug")

    if not stash.is_binary:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This is a text stash")

    file_path = await query.get_stash_binary_path(db_conn, stash_id=stash.id_)
    if file_path is None:
        raise RuntimeError("Stash binary path select returned no rows")

    path = Path(file_path)
    if not path.is_file():
        logger.error("Missing file on disk for stash %s: %s", slug, path)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored file is missing",
        )

    return FileResponse(
        path,
        filename=path.name,
    )


@stashes_router.get("/text/{slug}", status_code=HTTP_200_OK, response_model=str, responses={HTTP_404_NOT_FOUND: {"model": Message}})
async def get_text_stash(slug: str, db_conn: DBConn) -> str:
    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug")

    if stash.is_binary:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This is a binary stash")

    content = await query.get_stash_text_content(db_conn, stash_id=stash.id_)
    if content is None:
        raise RuntimeError("Stash content select returned no rows")
    return content


@stashes_router.get("/metadata/{slug}", status_code=HTTP_200_OK, response_model=GetStashBySlugRow, responses={HTTP_404_NOT_FOUND: {"model": Message}})
async def get_stash_metadata(slug: str, db_conn: DBConn) -> GetStashBySlugRow:
    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug")
    
    return stash