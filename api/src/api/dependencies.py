import hashlib
import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from psycopg import AsyncConnection

from .db import models, query
from .db.ops import get_db_conn

logger = logging.getLogger(Path(__file__).name)


def get_ip_addr(request: Request) -> str | None:
    if forwarded_for := request.headers.get("x-forwarded-for"):
        return forwarded_for.split(",", 1)[0].strip()

    if request.client is not None:
        return request.client.host

    return None


# def get_named_route_uri(request: Request) -> Callable[[str], str]:
#     main_app = cast(FastAPI, request.app)
#     return main_app.router.url_path_for


DBConn = Annotated[AsyncConnection, Depends(get_db_conn)]
IPAddr = Annotated[str | None, Depends(get_ip_addr)]
# NamedRouteURIs = Annotated[Callable[[str], str], Depends(get_named_route_uri)]


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
