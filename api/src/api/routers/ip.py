import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from ..db import models, query
from ..dependencies import CurrentUser, DBConn, banned_ips_cache
from ..response_models import Message
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ip")


@router.get(
    "/{ip_addr}/activity",
    status_code=HTTP_200_OK,
    response_model=Sequence[query.ListIPActivityRow],
    responses={HTTP_403_FORBIDDEN: {"model": Message}},
)
async def list_ip_activity(
    ip_addr: str,
    page: Annotated[int, Query(gt=0)],
    take: Annotated[int, Query(lt=settings.APP_MAX_PAGE_TAKE, gt=0)],
    db_conn: DBConn,
    current_user: CurrentUser,
) -> Sequence[query.ListIPActivityRow]:
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            HTTP_403_FORBIDDEN,
            "You are not allowed to do that",
        )

    return await query.list_i_p_activity(
        db_conn,
        ip_address=ip_addr,
        limit=take,
        offset=(page - 1) * take,
    )


@router.get(
    "/{ip_addr}/bans/active",
    status_code=HTTP_200_OK,
    response_model=models.IpBan | None,
    responses={HTTP_403_FORBIDDEN: {"model": Message}},
)
async def get_active_ip_ban(
    ip_addr: str,
    db_conn: DBConn,
    current_user: CurrentUser,
) -> models.IpBan | None:
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            HTTP_403_FORBIDDEN,
            "You are not allowed to do that",
        )

    return await query.get_active_i_p_ban(db_conn, ip_address=ip_addr)


@router.post(
    "/{ip_addr}/ban",
    status_code=HTTP_200_OK,
    response_model=models.IpBan,
    responses={
        HTTP_403_FORBIDDEN: {"model": Message},
        HTTP_422_UNPROCESSABLE_CONTENT: {"model": Message},
    },
)
async def add_ip_ban(
    ip_addr: str,
    expires: Annotated[datetime | None, Body()],
    reason: Annotated[str | None, Body()],
    db_conn: DBConn,
    current_user: CurrentUser,
) -> models.IpBan:
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            HTTP_403_FORBIDDEN,
            "You are not allowed to do that",
        )

    async with db_conn.transaction():
        ban = await query.create_i_p_ban(
            db_conn,
            ip_address=ip_addr,
            expires=expires,
            reason=reason,
            added_by_user_id=current_user.id_,
        )

    if ban is None:
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR,
            "Server could not create the ban, please try again later",
        )

    active_ban = await query.get_active_i_p_ban(db_conn, ip_address=ip_addr)
    if active_ban:
        banned_ips_cache.add(ip_addr)

    return ban


@router.delete(
    "/bans/{ban_id}",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_403_FORBIDDEN: {"model": Message}},
)
async def revoke_ban(
    ban_id: int,
    reason: Annotated[str | None, Body()],
    db_conn: DBConn,
    current_user: CurrentUser,
):
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            HTTP_403_FORBIDDEN,
            "You are not allowed to do that",
        )

    async with db_conn.transaction():
        ip_addr = await query.revoke_i_p_ban(
            db_conn,
            id_=ban_id,
            revoked_by_user_id=current_user.id_,
            revocation_reason=reason,
        )

    if not ip_addr:
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR,
            "Server could not revoke the ban, please try again later",
        )

    active_ban = await query.get_active_i_p_ban(db_conn, ip_address=ip_addr)
    if not active_ban and ip_addr in banned_ips_cache:
        banned_ips_cache.remove(ip_addr)
