import logging
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import aiofiles
from argon2 import PasswordHasher
from argon2.exceptions import HashingError, VerifyMismatchError
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
from pydantic import SecretStr
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_410_GONE,
    HTTP_413_CONTENT_TOO_LARGE,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from api.db.query import GetStashBySlugRow

from ..db import models, query
from ..dependencies import CurrentUser, DBConn, IPAddr
from ..response_models import Message
from ..settings import settings
from ..slug_service import new_slug

logger = logging.getLogger(Path(__file__).name)


router = APIRouter(prefix="/stashes")


@router.get(
    "/",
    status_code=HTTP_200_OK,
    response_model=Sequence[query.ListStashesRow],
    responses={HTTP_403_FORBIDDEN: {"model": Message}},
)
async def list_stashes(
    page: Annotated[int, Query(gt=0)],
    take: Annotated[int, Query(lt=settings.APP_MAX_PAGE_TAKE, gt=0)],
    db_conn: DBConn,
    current_user: CurrentUser,
    show_revoked: Annotated[bool, Query()] = False,
    show_expired: Annotated[bool, Query()] = False,
) -> Sequence[query.ListStashesRow]:
    if (show_revoked or show_expired) and (
        not current_user or not current_user.is_admin
    ):
        raise HTTPException(
            HTTP_403_FORBIDDEN, "You are not allowed to list expired or revoked stashes"
        )

    return await query.list_stashes(
        db_conn,
        limit=take,
        offset=(page - 1) * take,
        include_revoked=show_revoked,
        include_expired=show_expired,
    )


MAX_SLUG_ATTEMPTS = 10

password_hasher = PasswordHasher()


async def try_with_slug(
    operation: Callable[[int], Awaitable[None]],
    is_binary: bool,
    db_conn: AsyncConnection,
    ip_addr: str | None,
    user: models.User | None,
    expires_at: datetime | None = None,
    password: SecretStr | None = None,
) -> models.Stash:
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

                if expires_at is not None:
                    await query.create_stash_expiry(
                        db_conn, stash_id=stash.id_, expires_at=expires_at
                    )

                if password is not None:
                    try:
                        password_hash = password_hasher.hash(
                            password.get_secret_value()
                        )
                    except HashingError as e:
                        logger.error(e)
                        raise HTTPException(
                            HTTP_500_INTERNAL_SERVER_ERROR,
                            "Server could not generate password hash",
                        )
                    await query.create_stash_password_hash(
                        db_conn, stash_id=stash.id_, password_hash=password_hash
                    )

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
    if not current_user or not current_user.is_admin:
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


@router.post("/text", status_code=HTTP_201_CREATED, response_model=models.Stash)
async def add_text_stash(
    content: Annotated[str, Body()],
    db_conn: DBConn,
    ip_addr: IPAddr,
    current_user: CurrentUser,
    expires_at: datetime | None = None,
    password: Annotated[SecretStr | None, Body()] = None,
) -> models.Stash:
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
        operation,
        is_binary=False,
        db_conn=db_conn,
        ip_addr=ip_addr,
        user=current_user,
        expires_at=expires_at,
        password=password,
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
    response_model=models.Stash,
    responses={
        HTTP_422_UNPROCESSABLE_CONTENT: {"model": Message},
        HTTP_413_CONTENT_TOO_LARGE: {"model": Message},
    },
)
async def add_binary_stash(
    file: UploadFile,
    db_conn: DBConn,
    ip_addr: IPAddr,
    current_user: CurrentUser,
    expires_at: datetime | None = None,
    password: Annotated[SecretStr | None, Body()] = None,
) -> models.Stash:
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
                expires_at=expires_at,
                password=password,
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


async def raise_if_password_checks_fail(
    stash_id: int,
    password: SecretStr | None,
    db_conn: DBConn,
    ip_addr: str,
    current_user: CurrentUser,
):
    if not (current_user and current_user.is_admin):
        if password is None:
            raise HTTPException(HTTP_403_FORBIDDEN, "This stash is password protected")
        else:
            stored_hash = await query.get_stash_password_hash(
                db_conn, stash_id=stash_id
            )
            if stored_hash is None:
                raise HTTPException(
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    "Could not obtain stored hash for protected stash",
                )

            successful = False
            try:
                successful = password_hasher.verify(
                    stored_hash, password.get_secret_value()
                )
            except VerifyMismatchError:
                pass

            async with db_conn.transaction():
                await query.create_stash_password_attempt(
                    db_conn,
                    stash_id=stash_id,
                    ip_address=ip_addr,
                    successful=successful,
                )

            if not successful:
                raise HTTPException(HTTP_401_UNAUTHORIZED, "Incorrect password")


@router.post(
    "/file/{slug}/unlock",
    status_code=HTTP_200_OK,
    response_class=FileResponse,
    responses={
        HTTP_404_NOT_FOUND: {"model": Message},
        HTTP_400_BAD_REQUEST: {"model": Message},
        HTTP_200_OK: {"content": {"application/octet-stream": {}}},
        HTTP_410_GONE: {"model": Message},
        HTTP_401_UNAUTHORIZED: {"model": Message},
        HTTP_403_FORBIDDEN: {"model": Message},
    },
)
async def unlock_protected_file_stash(
    slug: str,
    password: Annotated[SecretStr, Body()],
    db_conn: DBConn,
    ip_addr: IPAddr,
    current_user: CurrentUser,
) -> FileResponse:
    if ip_addr is None:
        raise HTTPException(
            HTTP_401_UNAUTHORIZED, "Server could not determine your IP address"
        )

    stash = await get_stash_from_slug(slug, db_conn, current_user)

    await raise_if_password_checks_fail(
        stash.id_, password, db_conn, ip_addr, current_user
    )
    return await _get_file_stash_file_response(stash.id_, db_conn, ip_addr)


@router.post(
    "/text/{slug}/unlock",
    status_code=HTTP_200_OK,
    response_model=str,
    responses={
        HTTP_404_NOT_FOUND: {"model": Message},
        HTTP_400_BAD_REQUEST: {"model": Message},
        HTTP_200_OK: {"content": {"application/octet-stream": {}}},
        HTTP_410_GONE: {"model": Message},
        HTTP_401_UNAUTHORIZED: {"model": Message},
        HTTP_403_FORBIDDEN: {"model": Message},
    },
)
async def unlock_protected_text_stash(
    slug: str,
    password: Annotated[SecretStr, Body()],
    db_conn: DBConn,
    ip_addr: IPAddr,
    current_user: CurrentUser,
) -> str:
    if ip_addr is None:
        raise HTTPException(
            HTTP_401_UNAUTHORIZED, "Server could not determine your IP address"
        )

    stash = await get_stash_from_slug(slug, db_conn, current_user)

    await raise_if_password_checks_fail(
        stash.id_, password, db_conn, ip_addr, current_user
    )
    return await _get_text_stash_text_response(stash.id_, db_conn, ip_addr)


async def get_stash_from_slug(
    slug: str, db_conn: DBConn, current_user: CurrentUser
) -> GetStashBySlugRow:
    stash = await query.get_stash_by_slug(db_conn, slug=slug)

    if stash is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Stash does not exist by that slug"
        )

    if (
        stash.expires_at
        and stash.expires_at <= datetime.now(UTC)
        and not (current_user and current_user.is_admin)
    ):
        raise HTTPException(
            status_code=HTTP_410_GONE,
            detail="Stash has expired and is no longer available",
        )

    return stash


@router.get(
    "/file/{slug}",
    status_code=HTTP_200_OK,
    response_class=FileResponse,
    responses={
        HTTP_404_NOT_FOUND: {"model": Message},
        HTTP_400_BAD_REQUEST: {"model": Message},
        HTTP_200_OK: {"content": {"application/octet-stream": {}}},
        HTTP_410_GONE: {"model": Message},
        HTTP_401_UNAUTHORIZED: {"model": Message},
        HTTP_403_FORBIDDEN: {"model": Message},
    },
)
async def get_file_stash(
    slug: str,
    db_conn: DBConn,
    ip_addr: IPAddr,
    current_user: CurrentUser,
) -> FileResponse:
    if ip_addr is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="The server could not determine your IP address",
        )

    stash = await get_stash_from_slug(slug, db_conn, current_user)

    if not stash.is_binary:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="This is a text stash"
        )

    if stash.is_protected and not (current_user and current_user.is_admin):
        raise HTTPException(HTTP_401_UNAUTHORIZED, "This stash requires a password")

    return await _get_file_stash_file_response(stash.id_, db_conn, ip_addr)


async def _get_file_stash_file_response(
    stash_id: int, db_conn: DBConn, ip_addr: str
) -> FileResponse:
    file_path = await query.get_stash_binary_path(db_conn, stash_id=stash_id)
    if file_path is None:
        raise HTTPException(
            HTTP_404_NOT_FOUND, "Stash content does not exist (is likely revoked)"
        )

    path = Path(file_path)
    if not path.is_file():
        logger.error("Missing file on disk for stash %d: %s", stash_id, path)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored file is missing",
        )

    async with db_conn.transaction():
        await query.create_stash_view(db_conn, stash_id=stash_id, ip_address=ip_addr)

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
        HTTP_410_GONE: {"model": Message},
        HTTP_401_UNAUTHORIZED: {"model": Message},
        HTTP_403_FORBIDDEN: {"model": Message},
    },
)
async def get_text_stash(
    slug: str,
    db_conn: DBConn,
    ip_addr: IPAddr,
    current_user: CurrentUser,
) -> str:
    if ip_addr is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="The server could not determine your IP address",
        )

    stash = await get_stash_from_slug(slug, db_conn, current_user)

    if stash.is_binary:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="This is a file stash"
        )

    if stash.is_protected and not (current_user and current_user.is_admin):
        raise HTTPException(HTTP_401_UNAUTHORIZED, "This stash requires a password")

    return await _get_text_stash_text_response(stash.id_, db_conn, ip_addr)


async def _get_text_stash_text_response(
    stash_id: int, db_conn: DBConn, ip_addr: str
) -> str:
    content = await query.get_stash_text_content(db_conn, stash_id=stash_id)
    if content is None:
        raise HTTPException(
            HTTP_404_NOT_FOUND, "Stash content does not exist (is likely revoked)"
        )

    async with db_conn.transaction():
        await query.create_stash_view(db_conn, stash_id=stash_id, ip_address=ip_addr)

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
