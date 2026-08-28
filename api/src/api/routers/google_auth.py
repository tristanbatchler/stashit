from fastapi import APIRouter

from ..settings import settings

router = APIRouter(prefix="/auth/google")

# @google_auth_router.get("", ...)
# def ...

GOOGLE_CALLBACK_NAME = "google_callback"


@router.get("/callback", name=GOOGLE_CALLBACK_NAME)
async def google_callback():
    return {"status": "ok"}


google_redirect_uri: str = settings.APP_BASE_URL + router.url_path_for(
    GOOGLE_CALLBACK_NAME
)
