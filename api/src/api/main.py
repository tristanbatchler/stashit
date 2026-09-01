import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import (
    APIRouter,
    FastAPI,
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.body_limit import RequestBodyLimitMiddleware
from starlette.status import (
    HTTP_200_OK,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from .db import ops
from .response_models import Message
from .routers.google_auth import router as google_auth_router
from .routers.ip import router as ip_router
from .routers.stashes import router as stashes_router
from .settings import settings

logger = logging.getLogger(Path(__file__).name)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    settings.APP_UPLOADS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    await ops.create_tables()
    await ops.db_conn_pool.open()
    yield
    await ops.db_conn_pool.close()


app: FastAPI = FastAPI(lifespan=lifespan)


# Allow the SvelteKit dev server (and built site) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.WEB_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RequestBodyLimitMiddleware,
    max_body_size=settings.APP_MAX_UPLOAD_BYTES + settings.APP_NON_UPLOAD_MAX_BODY_SIZE,
)


main_router = APIRouter(
    prefix="/api/v1", responses={HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message}}
)

main_router.include_router(stashes_router)
main_router.include_router(google_auth_router)
main_router.include_router(ip_router)
app.include_router(main_router)


@main_router.get(
    "/config/max-upload-bytes", status_code=HTTP_200_OK, response_model=int
)
async def get_config() -> int:
    return settings.APP_MAX_UPLOAD_BYTES
