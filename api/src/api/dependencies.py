from typing import Annotated

from fastapi import Depends, Request
from psycopg import AsyncConnection

from .db.ops import get_db_conn


def get_ip_addr(request: Request) -> str | None:
    if forwarded_for := request.headers.get("x-forwarded-for"):
        return forwarded_for.split(",", 1)[0].strip()

    if request.client is not None:
        return request.client.host

    return None


DBConn = Annotated[AsyncConnection, Depends(get_db_conn)]
IPAddr = Annotated[str | None, Depends(get_ip_addr)]
