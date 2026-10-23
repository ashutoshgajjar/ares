from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView

from .views import CSRFTokenView, CookieTokenRefreshView, LoginView, LogoutView, MeView, RegisterView, UserDetailView, UserListCreateView
# from rest_framework_simplejwt.views import TokenBlacklistView

urlpatterns = [
    # path("health/", HealthView.as_view(), name="health"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/register/",RegisterView.as_view(),name="register"),
    path("auth/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/csrf/", CSRFTokenView.as_view(),name="csrf_token"),
    # path("auth/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("users/", UserListCreateView.as_view(), name="user_list_create"),
    path("users/<uuid:pk>/", UserDetailView.as_view(), name="user_detail"),
]
