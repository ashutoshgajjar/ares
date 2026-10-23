from django.conf import settings
from django.utils import timezone

from rest_framework_simplejwt.tokens import RefreshToken


def create_session_tokens(user, session):
    refresh = RefreshToken.for_user(user)

    refresh["role"] = user.role
    refresh["account_status"] = user.account_status
    refresh["session_id"] = str(session.id)

    access = refresh.access_token

    access["role"] = user.role
    access["account_status"] = user.account_status
    access["session_id"] = str(session.id)

    return str(access), str(refresh)


def set_auth_cookies(
    response,
    access_token,
    refresh_token,
):
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_COOKIE_MAX_AGE,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )

    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/api/v1/auth/",
    )


def clear_auth_cookies(response):
    response.delete_cookie(
        settings.ACCESS_TOKEN_COOKIE,
        path="/",
    )

    response.delete_cookie(
        settings.REFRESH_TOKEN_COOKIE,
        path="/api/v1/auth/",
    )

    return response