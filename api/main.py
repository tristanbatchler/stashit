import logging
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
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
    Request,
    UploadFile,
)

# jsonable_encoder removed; FastAPI will serialize pydantic models automatically
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from psycopg import AsyncConnection
from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel
from starlette.middleware.body_limit import RequestBodyLimitMiddleware
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_413_CONTENT_TOO_LARGE,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from db import models, ops, query
from slug_service import new_slug

logger = logging.getLogger(Path(__file__).name)

@dataclass
class ConfigItem:
    key: str
    int_range: tuple[int | None, int | None] = (None, None)

class ConfigKey(Enum):
    DB_DATABASE = ConfigItem("DB_DATABASE")
    DB_USERNAME = ConfigItem("DB_USERNAME")
    DB_PASSWORD = ConfigItem("DB_PASSWORD")
    DB_HOST = ConfigItem("DB_HOST")
    DB_PORT = ConfigItem("DB_PORT", (0, 0xFFFF))
    APP_BASE_URL = ConfigItem("APP_BASE_URL")
    APP_MAX_UPLOAD_BYTES = ConfigItem("APP_MAX_UPLOAD_BYTES", (1, None))


config: dict[ConfigKey, str] = {}

_ = load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

for config_key in ConfigKey:
    config_item = config_key.value
    value = getenv(config_item.key)
    if value is None:
        logger.fatal("Missing configuration key %s", config_key)
        exit(1)

    _min, _max = config_item.int_range
    if None not in (_min, _max):
        try:
            n = int(value)
            if (_min and n < _min) or (_max and n > _max):
                raise ValueError
        except ValueError:
            logger.fatal("Invalid integer value %s for config item: %s", value, config_key)


    config[config_key] = value


db_conn_string = f"postgresql://{config[ConfigKey.DB_USERNAME]}:{config[ConfigKey.DB_PASSWORD]}@{config[ConfigKey.DB_HOST]}:{config[ConfigKey.DB_PORT]}/{config[ConfigKey.DB_DATABASE]}"
db_conn_pool = AsyncConnectionPool(
    db_conn_string,
    open=False,
    min_size=5,        # Keep 5 connections ready
    max_size=20,       # Allow up to 20 connections
    timeout=30,        # 30s connection timeout
)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    await ops.create_tables(db_conn_string)
    await db_conn_pool.open()
    yield
    await db_conn_pool.close()


app: FastAPI = FastAPI(lifespan=lifespan)

async def get_ip_addr(request: Request) -> str | None:
    if forwarded_for := request.headers.get("x-forwarded-for"):
        return forwarded_for.split(",", 1)[0].strip()

    if request.client is not None:
        return request.client.host

    return None

async def get_db_conn() -> AsyncGenerator[AsyncConnection]:
    async with db_conn_pool.connection() as conn:
	    yield conn

DBConn = Annotated[AsyncConnection, Depends(get_db_conn)]
IPAddr = Annotated[str | None, Depends(get_ip_addr)]

# Allow the SvelteKit dev server (and built site) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        config[ConfigKey.APP_BASE_URL]
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RequestBodyLimitMiddleware,
    max_body_size=int(config[ConfigKey.APP_MAX_UPLOAD_BYTES]) + 1_048_576,
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
async def try_with_slug(operation: Callable[[int], Awaitable[None]], is_binary: bool, db_conn: AsyncConnection, ip_addr: str) -> models.Stash:
    for _ in range(MAX_SLUG_ATTEMPTS):
        slug = new_slug()
        try:
            async with db_conn.transaction():
                stash = await query.create_stash(db_conn, is_binary=is_binary, slug=slug, added_by_ip=ip_addr)
                if stash is None:
                    raise RuntimeError("stash insert returned no row")
                await operation(stash.id_)
                return stash
        except UniqueViolation:
            continue
    
    
    raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Could not generate a unique slug")


@stashes_router.post("/text", status_code=HTTP_201_CREATED, response_model=models.Stash)
async def add_text_stash(content: Annotated[str, Body()], db_conn: DBConn, ip_addr: IPAddr) -> models.Stash:    
    if ip_addr is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="The server could not determine your IP address")

    async def operation(stash_id: int):
        await query.create_stash_text_content(db_conn, stash_id=stash_id, content=content)

    return await try_with_slug(operation, is_binary=False, db_conn=db_conn, ip_addr=ip_addr)
    


@stashes_router.post("/file", status_code=HTTP_201_CREATED, response_model=models.Stash, responses={HTTP_422_UNPROCESSABLE_CONTENT: {"model": Message}, HTTP_413_CONTENT_TOO_LARGE: {"model": Message}})
async def add_binary_stash(file: UploadFile, db_conn: DBConn, ip_addr: IPAddr) -> models.Stash:
    if ip_addr is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="The server could not determine your IP address",
        )

    try:
        uploads_dir = Path(__file__).parent / "uploads"
        uploads_dir.mkdir(exist_ok=True)

        if file.filename is None:
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_CONTENT,
                "The uploaded file must have a valid filename",
            )

        if file.size in (None, 0):
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_CONTENT,
                "The uploaded file is empty or corrupted",
            )

        uuid_str = uuid4().hex
        unique_folder = uploads_dir / uuid_str
        unique_folder.mkdir(parents=True, exist_ok=True)

        sanitized_filename = Path(file.filename).name
        destination = unique_folder / sanitized_filename

        async with aiofiles.open(destination, "wb") as buffer:
            while chunk := await file.read(1024 * 64):
                _ = await buffer.write(chunk)

        async def operation(stash_id: int):
            await query.create_stash_binary_path(
                db_conn,
                stash_id=stash_id,
                file_path=str(destination),
            )

        try:
            return await try_with_slug(
                operation,
                is_binary=True,
                db_conn=db_conn,
                ip_addr=ip_addr,
            )
        except Exception:
            try:
                if destination.exists():
                    destination.unlink()

                if unique_folder.exists() and not any(unique_folder.iterdir()):
                    unique_folder.rmdir()
            except Exception:
                logger.exception(
                    "Failed to cleanup uploaded file after DB error: %s",
                    destination,
                )

            raise

    finally:
        await file.close()

@stashes_router.get("/file/{slug}", status_code=HTTP_200_OK, response_class=FileResponse, responses={HTTP_404_NOT_FOUND: {"model": Message}, HTTP_200_OK: {"content": {"application/octet-stream": {}}}})
async def get_file_stash(slug: str, db_conn: DBConn, ip_addr: IPAddr) -> FileResponse:
    if ip_addr is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="The server could not determine your IP address")

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

    async with db_conn.transaction():
        await query.create_stash_view(db_conn, stash_id=stash.id_, ip_address=ip_addr)

    return FileResponse(
        path,
        filename=path.name,
    )


@stashes_router.get("/text/{slug}", status_code=HTTP_200_OK, response_model=str, responses={HTTP_404_NOT_FOUND: {"model": Message}})
async def get_text_stash(slug: str, db_conn: DBConn, ip_addr: IPAddr) -> str:
    if ip_addr is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="The server could not determine your IP address")

    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug")

    if stash.is_binary:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This is a binary stash")

    content = await query.get_stash_text_content(db_conn, stash_id=stash.id_)
    if content is None:
        raise RuntimeError("Stash content select returned no rows")

    async with db_conn.transaction():
        await query.create_stash_view(db_conn, stash_id=stash.id_, ip_address=ip_addr)

    return content


@stashes_router.get("/metadata/{slug}", status_code=HTTP_200_OK, response_model=query.GetStashBySlugRow, responses={HTTP_404_NOT_FOUND: {"model": Message}})
async def get_stash_metadata(slug: str, db_conn: DBConn) -> query.GetStashBySlugRow:
    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug")
    
    return stash

@stashes_router.get("/views/{slug}", status_code=HTTP_200_OK, response_model=int)
async def get_stash_views(slug: str, unique: bool, db_conn: DBConn) -> int:
    views: int | None = None
    if unique:
        views = await query.get_stash_unique_views_by_slug(db_conn, slug=slug)
    else:
        views = await query.get_stash_views_by_slug(db_conn, slug=slug)
    
    if views is None:
        raise RuntimeError(f"Could not get views for slug {slug}")
    
    return views

@api_router.get("/config/max-upload-bytes", status_code=HTTP_200_OK, response_model=int)
async def get_config() -> int:
    return int(config[ConfigKey.APP_MAX_UPLOAD_BYTES])