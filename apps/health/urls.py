from django.urls import path

from .views import HealthView, HealthCheckLogListView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path( "health/logs/", HealthCheckLogListView.as_view(), name="health-logs" ),
]
