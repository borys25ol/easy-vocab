"""Double-submit CSRF protection.

The session cookie alone authenticates a request, so a form or fetch on a
hostile page can act as the signed-in user. SameSite=lax blocks most of
that, but it is a browser default the deployment can override, and it is
not a defence the server controls.

The server therefore hands out a random token in a cookie that scripts can
read, and requires the same value back in a header or a form field. A
cross-site page can make the browser send cookies, but the same-origin
policy stops it reading them, so it cannot produce the echo.
"""

import hmac
import secrets

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings


CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"

# Methods that must not change state, so they need no token. HEAD and
# OPTIONS join them because browsers issue both without user intent.
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


class CSRFTokenMiddleware(BaseHTTPMiddleware):
    """Give every response a CSRF cookie and expose the token to templates.

    Validation lives in the verify_csrf dependency rather than here. Reading
    a form body inside BaseHTTPMiddleware consumes the request stream, and
    the endpoint then receives an empty body.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        existing = request.cookies.get(CSRF_COOKIE_NAME)
        token = existing or secrets.token_urlsafe(32)
        request.state.csrf_token = token

        response = await call_next(request)

        if not existing:
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=token,
                # Readable on purpose: the page script has to echo it back.
                httponly=False,
                samesite=settings.COOKIE_SAMESITE,
                secure=settings.SESSION_COOKIE_SECURE,
                path=settings.COOKIE_PATH,
                domain=settings.COOKIE_DOMAIN,
            )
        return response


async def verify_csrf(request: Request) -> None:
    """Reject a state-changing request whose token is absent or wrong."""
    if request.method in SAFE_METHODS:
        return

    expected = request.cookies.get(CSRF_COOKIE_NAME)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing CSRF cookie",
        )

    submitted = request.headers.get(CSRF_HEADER_NAME)
    if not submitted:
        # FastAPI caches the parsed form on the request, so the endpoint's
        # own Form parameters still see the body after this read.
        content_type = request.headers.get("content-type", "")
        if content_type.startswith(
            ("application/x-www-form-urlencoded", "multipart/form-data")
        ):
            form = await request.form()
            field = form.get(CSRF_FORM_FIELD)
            submitted = field if isinstance(field, str) else None

    if not submitted or not hmac.compare_digest(submitted, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch",
        )
