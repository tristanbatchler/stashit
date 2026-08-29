import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google.oauth2 import id_token
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_303_SEE_OTHER,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from ..auth_service import create_google_flow
from ..db import models, query
from ..dependencies import CurrentUser, DBConn, IPAddr, NamedRouteURIs
from ..response_models import GoogleLoginLocation, Message
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/google")

GOOGLE_CALLBACK_ROUTE_ID = "google_callback"


@router.get(
    "",
    response_model=GoogleLoginLocation,
    status_code=HTTP_200_OK,
    responses={
        HTTP_401_UNAUTHORIZED: {"model": Message},
        HTTP_200_OK: {"model": GoogleLoginLocation},
    },
)
async def google_login(
    db_conn: DBConn,
    ip_addr: IPAddr,
    named_route_uris: NamedRouteURIs,
) -> GoogleLoginLocation:
    if ip_addr is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="The server could not determine your IP address",
        )

    redirect_uri = named_route_uris(GOOGLE_CALLBACK_ROUTE_ID)

    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    flow = create_google_flow(redirect_uri)

    authorization_url, _ = cast(
        tuple[str, str],
        flow.authorization_url(  # pyright: ignore[reportUnknownMemberType]
            state=state,
            prompt="select_account",
        ),
    )

    if not isinstance(flow.code_verifier, str):  # pyright: ignore[reportUnknownMemberType]
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR,
            "Could not get code verifier from Google OAuth flow",
        )

    async with db_conn.transaction():
        await query.create_o_auth_state(
            db_conn,
            state=state,
            code_verifier=flow.code_verifier,
            expires=expires_at,
            ip_address=ip_addr,
        )

    return GoogleLoginLocation(url=authorization_url)


@router.get(
    "/callback",
    name=GOOGLE_CALLBACK_ROUTE_ID,
    status_code=HTTP_303_SEE_OTHER,
    responses={HTTP_400_BAD_REQUEST: {"model": Message}},
)
async def google_callback(
    code: str,
    state: str,
    db_conn: DBConn,
    named_route_uris: NamedRouteURIs,
) -> RedirectResponse:
    redirect_uri = named_route_uris(GOOGLE_CALLBACK_ROUTE_ID)

    oauth_state = await query.get_o_auth_state(
        db_conn,
        state=state,
    )

    if oauth_state is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state",
        )

    flow = create_google_flow(redirect_uri)
    flow.fetch_token(  # pyright: ignore[reportUnknownMemberType]
        code=code,
        code_verifier=oauth_state.code_verifier,
    )

    credentials = flow.credentials

    cred_id_token = cast(str | bytes | None, credentials.id_token)  # pyright: ignore[reportAttributeAccessIssue]

    if not cred_id_token:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Google did not return an ID token",
        )

    google_identity = id_token.verify_oauth2_token(  # pyright: ignore[reportUnknownMemberType]
        cred_id_token,
        requests.Request(),
        settings.GOOGLE_CLIENT_ID,
    )

    sub = google_identity.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Google identity does not contain sub",
        )

    email = google_identity.get("email")
    if not isinstance(email, str):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Google identity does not contain email",
        )

    name = google_identity.get("name")
    if not isinstance(name, str):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Google identity does not contain name",
        )

    logger.info(
        "Google OAuth successful: sub=%s email=%s name=%s picture=%s",
        sub,
        email,
        name,
        google_identity.get("picture"),
    )

    session_token = secrets.token_urlsafe(32)
    session_token_hash = hashlib.sha256(session_token.encode()).hexdigest()
    session_expires = datetime.now(UTC) + timedelta(
        days=settings.APP_SESSION_DURATION_DAYS
    )

    async with db_conn.transaction():
        _ = await query.delete_o_auth_state(
            db_conn,
            state=state,
        )

        user = await query.upsert_user(db_conn, google_sub=sub, email=email, name=name)

        if user is None:
            raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, "Error upserting user")

        await query.create_session(
            db_conn,
            user_id=user.id_,
            token_hash=session_token_hash,
            expires=session_expires,
        )

    redirect = RedirectResponse(
        settings.WEB_BASE_URL,
        status_code=HTTP_303_SEE_OTHER,
    )

    redirect.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=settings.APP_SESSION_COOKIE_SECURE,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.APP_SESSION_DURATION_DAYS,
    )

    return redirect


@router.get("/me", response_model=models.User | None, status_code=HTTP_200_OK)
async def get_me(current_user: CurrentUser) -> models.User | None:
    return current_user


@router.post("/logout", status_code=HTTP_204_NO_CONTENT)
async def google_logout(
    request: Request,
    db_conn: DBConn,
) -> Response:
    session_token = request.cookies.get("session")

    if session_token is not None:
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()

        async with db_conn.transaction():
            await query.delete_session(
                db_conn,
                token_hash=token_hash,
            )

    response = Response(status_code=HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key="session",
        httponly=True,
        secure=settings.APP_SESSION_COOKIE_SECURE,
        samesite="lax",
    )

    return response
