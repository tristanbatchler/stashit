import logging
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import aiofiles
from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from psycopg import AsyncConnection
from psycopg.errors import UniqueViolation
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_413_CONTENT_TOO_LARGE,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from ..db import models, query
from ..dependencies import CurrentUser, DBConn, IPAddr
from ..response_models import Message
from ..settings import settings
from ..slug_service import new_slug

logger = logging.getLogger(Path(__file__).name)


router = APIRouter(prefix="/stashes")


@router.get("/", status_code=HTTP_200_OK, response_model=Sequence[query.ListStashesRow])
async def list_stashes(
    page: Annotated[int, Query(gt=0)],
    take: Annotated[int, Query(lt=settings.APP_MAX_PAGE_TAKE, gt=0)],
    db_conn: DBConn,
) -> Sequence[query.ListStashesRow]:
    return await query.list_stashes(db_conn, limit=take, offset=(page - 1) * take)


MAX_SLUG_ATTEMPTS = 10


async def try_with_slug(
    operation: Callable[[int], Awaitable[None]],
    is_binary: bool,
    db_conn: AsyncConnection,
    ip_addr: str | None,
    user: models.User | None,
) -> query.CreateStashRow:
    if is_binary and user is None:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "You must be logged in to do that")
    elif ip_addr is None:
        raise HTTPException(
            HTTP_401_UNAUTHORIZED, "Server could not determine your IP address"
        )

    for _ in range(MAX_SLUG_ATTEMPTS):
        slug = new_slug()
        try:
            async with db_conn.transaction():
                stash = await query.create_stash(
                    db_conn,
                    is_binary=is_binary,
                    slug=slug,
                    added_by_ip=ip_addr,
                    added_by_user_id=user.id_ if user else None,
                )
                if stash is None:
                    raise RuntimeError("stash insert returned no row")
                await operation(stash.id_)
                return stash
        except UniqueViolation:
            continue

    raise HTTPException(
        HTTP_500_INTERNAL_SERVER_ERROR, "Could not generate a unique slug"
    )


@router.delete(
    "/{slug}",
    status_code=HTTP_204_NO_CONTENT,
    responses={
        HTTP_403_FORBIDDEN: {"model": Message},
        HTTP_404_NOT_FOUND: {"model": Message},
    },
)
async def revoke_stash(
    slug: str,
    current_user: CurrentUser,
    db_conn: DBConn,
) -> None:
    if not current_user or current_user.email.lower() not in settings.ADMIN_EMAILS:
        raise HTTPException(
            HTTP_403_FORBIDDEN,
            "You are not allowed to do that",
        )

    file_path: str | None = None

    async with db_conn.transaction():
        stash = await query.create_stash_revocation(
            db_conn,
            slug=slug,
            revoked_by_user_id=current_user.id_,
        )

        if stash is None:
            raise HTTPException(
                HTTP_404_NOT_FOUND,
                "Stash does not exist by that slug, or is already revoked",
            )

        if stash.is_binary:
            file_path = await query.delete_stash_binary_path(
                db_conn,
                stash_id=stash.id_,
            )
        else:
            await query.delete_stash_text_content(
                db_conn,
                stash_id=stash.id_,
            )

    if file_path is not None:
        path = Path(file_path)

        try:
            path.unlink(missing_ok=True)

            if path.parent.exists() and not any(path.parent.iterdir()):
                path.parent.rmdir()
        except OSError:
            logger.exception(
                "Failed to delete revoked stash file: %s",
                path,
            )


@router.post("/text", status_code=HTTP_201_CREATED, response_model=query.CreateStashRow)
async def add_text_stash(
    content: Annotated[str, Body()],
    db_conn: DBConn,
    ip_addr: IPAddr,
    current_user: CurrentUser,
) -> query.CreateStashRow:
    if ip_addr is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="The server could not determine your IP address",
        )

    async def operation(stash_id: int):
        await query.create_stash_text_content(
            db_conn, stash_id=stash_id, content=content
        )

    return await try_with_slug(
        operation, is_binary=False, db_conn=db_conn, ip_addr=ip_addr, user=current_user
    )


def maybe_raise_content_too_large_exception(current_bytes: int):
    max_bytes = settings.APP_MAX_UPLOAD_BYTES
    if current_bytes > max_bytes:
        raise HTTPException(
            HTTP_413_CONTENT_TOO_LARGE,
            f"Uploaded file exceeds the maximum allowed size ({max_bytes}B)",
        )


@router.post(
    "/file",
    status_code=HTTP_201_CREATED,
    response_model=query.CreateStashRow,
    responses={
        HTTP_422_UNPROCESSABLE_CONTENT: {"model": Message},
        HTTP_413_CONTENT_TOO_LARGE: {"model": Message},
    },
)
async def add_binary_stash(
    file: UploadFile, db_conn: DBConn, ip_addr: IPAddr, current_user: CurrentUser
) -> query.CreateStashRow:
    if current_user is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="You must log in first (or your session is expired/invalid)",
        )

    try:
        app_directory = Path(__file__).parent.parent
        uploads_dir = app_directory / "uploads"
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

        maybe_raise_content_too_large_exception(file.size)

        uuid_str = uuid4().hex
        unique_folder = uploads_dir / uuid_str
        unique_folder.mkdir(parents=True, exist_ok=True)

        sanitized_filename = Path(file.filename).name
        destination = unique_folder / sanitized_filename

        try:
            written = 0
            async with aiofiles.open(destination, "wb") as buffer:
                while chunk := await file.read(
                    settings.APP_UPLOADS_STREAMING_CHUNK_SIZE
                ):
                    maybe_raise_content_too_large_exception(written + len(chunk))
                    written += await buffer.write(chunk)

            async def operation(stash_id: int):
                await query.create_stash_binary_path(
                    db_conn,
                    stash_id=stash_id,
                    file_path=str(destination),
                )

            return await try_with_slug(
                operation,
                is_binary=True,
                db_conn=db_conn,
                user=current_user,
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
                    "Failed to cleanup uploaded file error: %s",
                    destination,
                )

            raise

    finally:
        await file.close()


@router.get(
    "/file/{slug}",
    status_code=HTTP_200_OK,
    response_class=FileResponse,
    responses={
        HTTP_404_NOT_FOUND: {"model": Message},
        HTTP_400_BAD_REQUEST: {"model": Message},
        HTTP_200_OK: {"content": {"application/octet-stream": {}}},
    },
)
async def get_file_stash(slug: str, db_conn: DBConn, ip_addr: IPAddr) -> FileResponse:
    if ip_addr is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="The server could not determine your IP address",
        )

    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug"
        )

    if not stash.is_binary:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="This is a text stash"
        )

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


@router.get(
    "/text/{slug}",
    status_code=HTTP_200_OK,
    response_model=str,
    responses={
        HTTP_404_NOT_FOUND: {"model": Message},
        HTTP_400_BAD_REQUEST: {"model": Message},
    },
)
async def get_text_stash(slug: str, db_conn: DBConn, ip_addr: IPAddr) -> str:
    if ip_addr is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="The server could not determine your IP address",
        )

    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug"
        )

    if stash.is_binary:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="This is a binary stash"
        )

    content = await query.get_stash_text_content(db_conn, stash_id=stash.id_)
    if content is None:
        raise RuntimeError("Stash content select returned no rows")

    async with db_conn.transaction():
        await query.create_stash_view(db_conn, stash_id=stash.id_, ip_address=ip_addr)

    return content


@router.get(
    "/metadata/{slug}",
    status_code=HTTP_200_OK,
    response_model=query.GetStashBySlugRow,
    responses={HTTP_404_NOT_FOUND: {"model": Message}},
)
async def get_stash_metadata(slug: str, db_conn: DBConn) -> query.GetStashBySlugRow:
    stash = await query.get_stash_by_slug(db_conn, slug=slug)
    if stash is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug"
        )

    return stash


@router.get("/views/{slug}", status_code=HTTP_200_OK, response_model=int)
async def get_stash_views(slug: str, unique: bool, db_conn: DBConn) -> int:
    views: int | None = None
    if unique:
        views = await query.get_stash_unique_views_by_slug(db_conn, slug=slug)
    else:
        views = await query.get_stash_views_by_slug(db_conn, slug=slug)

    if views is None:
        raise RuntimeError(f"Could not get views for slug {slug}")

    return views
