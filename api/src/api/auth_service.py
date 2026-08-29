from google_auth_oauthlib.flow import Flow  # pyright: ignore[reportMissingTypeStubs]

from .settings import settings

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

callback_uri = settings.WEB_BASE_URL + "/auth/google/callback"


def create_google_flow() -> Flow:
    return Flow.from_client_config(  # pyright: ignore[reportUnknownMemberType]
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [callback_uri],
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=callback_uri,
        autogenerate_code_verifier=True,
    )
