import hashlib
import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from fastapi.exceptions import HTTPException
from psycopg import AsyncConnection
from starlette.status import HTTP_403_FORBIDDEN

from .db import models, query
from .db.ops import get_db_conn

logger = logging.getLogger(Path(__file__).name)


async def get_ip_addr(request: Request, db_conn: DBConn) -> str | None:
    if forwarded_for := request.headers.get("x-forwarded-for"):
        return forwarded_for.split(",", 1)[0].strip()

    ip: str | None = request.client and request.client.host
    if ip is None:
        return None

    banned_ips: dict[str, bool] = request.app.state.banned_ips_cache  # pyright: ignore[reportAny]

    if ip in banned_ips:
        if banned_ips[ip] == True:  # banned
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Your IP address has been banned.",
            )
    else:
        active_ban = await query.get_active_i_p_ban(db_conn, ip_address=ip)
        if active_ban:
            banned_ips[ip] = True
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Your IP address has been banned.",
            )
        else:
            banned_ips[ip] = False  # not banned (yet)

    return ip


DBConn = Annotated[AsyncConnection, Depends(get_db_conn)]
IPAddr = Annotated[str | None, Depends(get_ip_addr)]


async def get_current_user(
    request: Request,
    db_conn: DBConn,
) -> models.User | None:
    session_token = request.cookies.get("session")

    if session_token is None:
        return None

    token_hash = hashlib.sha256(session_token.encode()).hexdigest()

    user = await query.get_user_by_session_token_hash(
        db_conn,
        token_hash=token_hash,
    )

    return user


CurrentUser = Annotated[models.User | None, Depends(get_current_user)]
