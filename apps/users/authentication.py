# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework.exceptions import AuthenticationFailed

# from .models import UserSession


# class SessionJWTAuthentication(JWTAuthentication):

#     def authenticate(self, request):

#         result = super().authenticate(request)

#         if result is None:
#             return None

#         user, validated_token = result

#         session_id = validated_token.get(
#             "session_id"
#         )

#         if not session_id:
#             raise AuthenticationFailed(
#                 "Invalid authentication session."
#             )

#         try:
#             session = (
#                 UserSession.objects
#                 .select_related("user")
#                 .get(
#                     id=session_id,
#                     user=user,
#                     revoked_at__isnull=True,
#                 )
#             )

#         except UserSession.DoesNotExist:
#             raise AuthenticationFailed(
#                 "Session has been revoked."
#             )

#         return user, validated_token

from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import CSRFCheck

from .models import (
    RevokedAccessToken,
    UserSession,
)
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticate exclusively from the HttpOnly access-token cookie.

    The Authorization: Bearer header is intentionally not accepted
    for browser authentication.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get(
            settings.ACCESS_TOKEN_COOKIE
        )

        if not raw_token:
            return None

        validated_token = self.get_validated_token(
            raw_token
        )

        user = self.get_user(
            validated_token
        )

        if not user.is_active:
            raise AuthenticationFailed(
                "User account is inactive."
            )

        session_id = validated_token.get(
            "session_id"
        )

        if not session_id:
            raise AuthenticationFailed(
                "Invalid authentication session."
            )

        try:
            session = (
                UserSession.objects
                .select_related("user")
                .get(
                    id=session_id,
                    user=user,
                    revoked_at__isnull=True,
                )
            )
        except UserSession.DoesNotExist as exc:
            raise AuthenticationFailed(
                "Session has been revoked."
            ) from exc

        jti = validated_token.get("jti")

        if jti:
            revoked = (
                RevokedAccessToken.objects
                .filter(
                    jti=jti,
                    user=user,
                    expires_at__gt=timezone.now(),
                )
                .exists()
            )

            if revoked:
                raise AuthenticationFailed(
                    "Access token has been revoked."
                )

        # Cookie authentication requires CSRF validation
        # for state-changing requests.
        self.enforce_csrf(request)

        # session.last_used_at = timezone.now()
        # session.save(update_fields=["last_used_at"])
        now = timezone.now()
        update_before = now - timedelta(minutes=2)

        if session.last_used_at < update_before:
            UserSession.objects.filter(
                pk=session.pk,
                revoked_at__isnull=True,
                last_used_at__lt=update_before,
            ).update(last_used_at=now)
        

        return user, validated_token

    @staticmethod
    def enforce_csrf(request):
        csrf_check = CSRFCheck(
            lambda request: None
        )

        csrf_check.process_request(request)

        reason = csrf_check.process_view(
            request,
            lambda request: None,
            (),
            {},
        )

        if reason:
            raise AuthenticationFailed(
                f"CSRF validation failed: {reason}"
            )