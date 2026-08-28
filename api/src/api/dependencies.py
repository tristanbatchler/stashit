import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, cast

from fastapi import Depends, FastAPI, Request
from psycopg import AsyncConnection

from .db.ops import get_db_conn
from .settings import settings

logger = logging.getLogger(Path(__file__).name)


def get_ip_addr(request: Request) -> str | None:
    if forwarded_for := request.headers.get("x-forwarded-for"):
        return forwarded_for.split(",", 1)[0].strip()

    if request.client is not None:
        return request.client.host

    return None


def get_named_route_uri(request: Request) -> Callable[[str], str]:
    main_app = cast(FastAPI, request.app)

    def get_uri_for(name: str) -> str:
        return settings.API_BASE_URL + main_app.router.url_path_for(name)

    return get_uri_for


DBConn = Annotated[AsyncConnection, Depends(get_db_conn)]
IPAddr = Annotated[str | None, Depends(get_ip_addr)]
NamedRouteURIs = Annotated[Callable[[str], str], Depends(get_named_route_uri)]
