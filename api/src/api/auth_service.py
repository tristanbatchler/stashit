from google_auth_oauthlib.flow import Flow

from .routers.google_auth import google_redirect_uri
from .settings import settings


def create_google_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [google_redirect_uri],
            }
        },
        scopes=["openid", "email", "profile"],
    )
