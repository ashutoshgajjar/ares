import logging
from time import perf_counter
from django.conf import settings
from django.utils import timezone

from django.middleware.csrf import get_token
from django.db import connection
from django.db.models import Q, Prefetch
from apps.files.models import StoredFile
from apps.files.storage import R2StorageError, get_r2_storage_service

from rest_framework.permissions import AllowAny
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication

from apps.common.utils import parse_json_object
from .utils import create_session_tokens, set_auth_cookies, clear_auth_cookies
from apps.common.pagination import (
    DynamicLimitOffsetPagination,
)

from .models import User, UserSession
from .permissions import IsAdminOrSelf, IsAdminRole
from .serializers import (
    LoginSerializer,
    MeSerializer,
    RegisterSerializer,
    UserSerializer,
    UserResponseSerializer,
)


logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def nested_json_lookups(prefix, payload):
    """
    Convert nested JSON filter objects into Django JSONField lookups.

    Example:

        {
            "personal": {
                "firstName": "John"
            }
        }

    becomes:

        profile__personal__firstName = "John"
    """

    lookups = {}

    for key, value in payload.items():
        path = f"{prefix}__{key}"

        if isinstance(value, dict):
            lookups.update(
                nested_json_lookups(path, value)
            )
        else:
            lookups[path] = value

    return lookups


# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------

# class LoginView(TokenObtainPairView):
#     """
#     POST /api/v1/auth/login/

#     Request:

#     {
#         "contact": {
#             "email": "user@example.com"
#         },
#         "password": "StrongPassword!123"
#     }

#     Response:

#     {
#         "refresh": "...",
#         "access": "..."
#     }
#     """

#     serializer_class = LoginSerializer
#     permission_classes = [permissions.AllowAny]
#     authentication_classes = []

class LoginView(generics.GenericAPIView):

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        session = UserSession.objects.create(
            user=user,
            user_agent=request.META.get(
                "HTTP_USER_AGENT",
                ""
            )[:1000],
            ip_address=self.get_client_ip(request),
        )

        access_token, refresh_token = (create_session_tokens(user,session))

        # refresh = RefreshToken.for_user(user)

        # refresh["role"] = user.role
        # refresh["account_status"] = user.account_status
        # refresh["session_id"] = str(session.id)

        # access = refresh.access_token

        # # Explicitly propagate session information to the access token.
        # access["role"] = user.role
        # access["account_status"] = user.account_status
        # access["session_id"] = str(session.id)

        response = Response({
            "message": "Login successful.",
            # "user": UserSerializer(
            #     user,
            #     context={
            #         "request": request
            #     },
            # ).data,
            "user": UserResponseSerializer(user, context={"request": request}).data,
            # "tokens": {
            #     "refresh": str(refresh),
            #     "access": str(access),
            # },
        })

        set_auth_cookies(
            response,
            access_token,
            refresh_token,
        )

        return response


        
    @staticmethod
    def get_client_ip(request):

        forwarded = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.META.get(
            "REMOTE_ADDR"
        )



# class RegisterView(generics.CreateAPIView):
#     """
#     POST /api/v1/auth/register/

#     Accepts the complete dynamic user document.

#     Authentication/security metadata is controlled by
#     the backend rather than the client.
#     """

#     serializer_class = RegisterSerializer
#     permission_classes = [permissions.AllowAny]
#     authentication_classes = []

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(
#             data=request.data
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         user = serializer.save()

#         # Generate tokens immediately after registration.
#         refresh = RefreshToken.for_user(user)

#         refresh["role"] = user.role
#         refresh["account_status"] = user.account_status

#         return Response(
#             {
#                 "message": "User registered successfully.",
#                 "user": UserSerializer(
#                     user,
#                     context={
#                         "request": request,
#                     },
#                 ).data,
#                 "tokens": {
#                     "refresh": str(refresh),
#                     "access": str(
#                         refresh.access_token
#                     ),
#                 },
#             },
#             status=status.HTTP_201_CREATED,
#         )

class RegisterView(generics.CreateAPIView):

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        # refresh = RefreshToken.for_user(user)

        # refresh["role"] = user.role
        # refresh["account_status"] = user.account_status
        session = UserSession.objects.create(
        user=user,
        user_agent=request.META.get(
            "HTTP_USER_AGENT",
            ""
        )[:1000],
        ip_address=LoginView.get_client_ip(
            request
        ),
        )
        access_token, refresh_token = (create_session_tokens(user,session,))

        # refresh = RefreshToken.for_user(user)

        # refresh["role"] = user.role
        # refresh["account_status"] = user.account_status
        # refresh["session_id"] = str(session.id)

        # access = refresh.access_token

        # # Explicitly propagate session information to the access token.
        # access["role"] = user.role
        # access["account_status"] = user.account_status
        # access["session_id"] = str(session.id)

        response = Response(
            {
                "message": "User registered successfully.",
                # "user": UserSerializer(
                #     user,
                #     context={
                #         "request": request
                #     },
                # ).data,
                "user": UserResponseSerializer(user, context={"request": request}).data,
                # "tokens": {
                #     "refresh": str(refresh),
                #     "access": str(
                #         refresh.access_token
                #     ),
                # },
            },
            status=status.HTTP_201_CREATED,
        )

        set_auth_cookies(
            response,
            access_token,
            refresh_token,
        )

        return response


# ----------------------------------------------------------------------
# User administration
# ----------------------------------------------------------------------

class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/users/
    POST /api/v1/users/

    Administrator only.
    """

    serializer_class = UserSerializer
    pagination_class = DynamicLimitOffsetPagination
    permission_classes = [IsAdminRole]

    queryset = (
        User.objects
        .all()
        .prefetch_related(
            Prefetch(
                "files",
                queryset=(
                    StoredFile.objects
                    .filter(
                        is_deleted=False
                    )
                    .order_by("-created_at")
                ),
                to_attr="prefetched_files",
            )
        )
        .order_by("-created_at")
    )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return UserResponseSerializer

        return UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        

        q = self.request.query_params.get("q")
        role = self.request.query_params.get("role")
        account_status = (
            self.request.query_params.get(
                "account_status"
            )
        )

        raw_filter = (
            self.request.query_params.get("filter")
        )

        # --------------------------------------------------------------
        # Search
        # --------------------------------------------------------------

        if q:
            queryset = queryset.filter(
                Q(email__icontains=q)
                |
                Q(username__icontains=q)
            )

        # --------------------------------------------------------------
        # Relational filters
        # --------------------------------------------------------------

        if role:
            queryset = queryset.filter(
                role=role
            )

        if account_status:
            queryset = queryset.filter(
                account_status=account_status
            )

        # --------------------------------------------------------------
        # Dynamic JSON filtering
        # --------------------------------------------------------------

        if raw_filter:
            filter_data = parse_json_object(
                raw_filter,
                "filter",
            )

            queryset = queryset.filter(
                **nested_json_lookups(
                    "profile",
                    filter_data,
                )
            )

        return queryset


class UserDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    GET    /api/v1/users/{id}/
    PATCH  /api/v1/users/{id}/
    PUT    /api/v1/users/{id}/
    DELETE /api/v1/users/{id}/
    """

    serializer_class = UserSerializer
    # queryset = User.objects.all()
    queryset = (User.objects.all().prefetch_related( Prefetch( "files", queryset=( StoredFile.objects .filter( is_deleted=False ) .order_by("-created_at") ), to_attr="prefetched_files", ) ))
    permission_classes = [IsAdminOrSelf]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return UserResponseSerializer

        return UserSerializer

    def perform_destroy(self, instance):
        user = self.request.user

        if (
            user.is_superuser
            or user.role == "admin"
        ):
            instance.delete()
            return

        raise PermissionDenied(
            "Only administrators can delete users."
        )


# ----------------------------------------------------------------------
# Current authenticated user
# ----------------------------------------------------------------------

# class MeView(generics.RetrieveUpdateAPIView):
#     """
#     GET   /api/v1/auth/me/
#     PATCH /api/v1/auth/me/
#     """

#     serializer_class = MeSerializer
#     permission_classes = [
#         permissions.IsAuthenticated
#     ]

#     def get_object(self):
#         return self.request.user

# class MeView(generics.RetrieveUpdateAPIView):

#     serializer_class = UserSerializer

#     def retrieve(self, request, *args, **kwargs):

#         user = request.user

#         return Response(
#             UserResponseSerializer(user).data
#         )

class MeView(
    generics.RetrieveUpdateAPIView
):
    serializer_class = UserSerializer

    def retrieve(self,request,*args,**kwargs):
        user = (User.objects.prefetch_related(Prefetch("files",queryset=(StoredFile.objects.filter(is_deleted=False).order_by("-created_at")),to_attr="prefetched_files",)).get(pk=request.user.pk))

        return Response(
            UserResponseSerializer(
                user,
                context={
                    "request": request
                },
            ).data
        )
        
# class LogoutView(APIView):
#     """
#     POST /api/v1/auth/logout/

#     Logout the currently authenticated user by revoking
#     the supplied refresh token.

#     Access token:
#         Authorization: Bearer <access-token>

#     Request:
#     {
#         "refresh": "<refresh-token>"
#     }
#     """

#     permission_classes = [IsAuthenticated]
#     authentication_classes = [SessionJWTAuthentication]

#     def post(self, request, *args, **kwargs):
#         refresh_token = request.data.get("refresh")

#         if not refresh_token:
#             return Response(
#                 {
#                     "message": "Refresh token is required."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         try:
#             refresh = RefreshToken(refresh_token)

#             # Make sure the refresh token belongs to
#             # the currently authenticated user.
#             token_user_id = str(refresh.get("user_id"))
#             token_session_id = refresh.get("session_id")

#             if token_user_id != str(request.user.id):
#                 return Response(
#                     {
#                         "message": "Invalid refresh token."
#                     },
#                     status=status.HTTP_401_UNAUTHORIZED,
#                 )

#             # refresh.blacklist()
#             if not token_session_id:
#                 return Response(
#                     {
#                         "message": (
#                             "Invalid authentication session."
#                         )
#                     },
#                     status=status.HTTP_401_UNAUTHORIZED,
#                 )
            
#             try:
#                 session = UserSession.objects.get(
#                     id=token_session_id,
#                     user=request.user,
#                 )

#             except UserSession.DoesNotExist:
#                 return Response(
#                     {
#                         "message": (
#                             "Session already revoked."
#                         )
#                     },
#                     status=status.HTTP_401_UNAUTHORIZED,
#                 )

#             session.revoke()

#             # Also blacklist the refresh token.
#             refresh.blacklist()



#             return Response(
#                 {
#                     "message": "Logout successful."
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except TokenError:
#             return Response(
#                 {
#                     "message": "Invalid or expired refresh token."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    authentication_classes = [CookieJWTAuthentication]

    def post(self, request, *args, **kwargs):
        session_id = (request.auth.get("session_id"))

        if session_id:
            UserSession.objects.filter(id=session_id,user=request.user,revoked_at__isnull=True,).update(revoked_at=timezone.now())

        response = Response({"message": "Logout successful."},
            status=status.HTTP_200_OK,
        )

        clear_auth_cookies(response)

        return response
    
class CookieTokenRefreshView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(
            settings.REFRESH_TOKEN_COOKIE
        )

        if not refresh_token:
            raise AuthenticationFailed(
                "Refresh token is missing."
            )

        try:
            refresh = RefreshToken(
                refresh_token
            )

            user_id = refresh.get(
                "user_id"
            )

            session_id = refresh.get(
                "session_id"
            )

            if not user_id or not session_id:
                raise AuthenticationFailed(
                    "Invalid refresh token."
                )

            session = (
                UserSession.objects
                .select_related("user")
                .get(
                    id=session_id,
                    user_id=user_id,
                    revoked_at__isnull=True,
                )
            )

            user = session.user

            if not user.is_active:
                raise AuthenticationFailed(
                    "User account is inactive."
                )

            # Revoke old session/token context before rotation.
            session.revoke()

            new_session = UserSession.objects.create(
                user=user,
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                )[:1000],
                ip_address=LoginView.get_client_ip(
                    request
                ),
            )

            access_token, new_refresh_token = (
                create_session_tokens(
                    user,
                    new_session,
                )
            )

            response = Response({
                "message": "Token refreshed.",
            })

            set_auth_cookies(
                response,
                access_token,
                new_refresh_token,
            )

            return response

        except (
            TokenError,
            UserSession.DoesNotExist,
        ) as exc:
            raise AuthenticationFailed(
                "Invalid or expired refresh token."
            ) from exc

class CSRFTokenView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            "csrfToken": get_token(request),
        })