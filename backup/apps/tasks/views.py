import logging

from django.conf import settings
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.common.utils import parse_json_object
from .models import Task
from .permissions import IsOwnerOrAdmin
from .serializers import TaskSerializer

logger = logging.getLogger(__name__)


def nested_json_lookups(prefix, payload):
    lookups = {}
    for key, value in payload.items():
        path = f"{prefix}__{key}"
        if isinstance(value, dict):
            lookups.update(nested_json_lookups(path, value))
        else:
            lookups[path] = value
    return lookups


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.select_related("owner").all()
        if not (user.is_superuser or user.role == "admin"):
            qs = qs.filter(owner=user)
        status_value = self.request.query_params.get("status")
        q = self.request.query_params.get("q")
        owner_id = self.request.query_params.get("owner_id")
        raw_filter = self.request.query_params.get("filter")
        if status_value:
            qs = qs.filter(status=status_value)
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if owner_id and (user.is_superuser or user.role == "admin"):
            qs = qs.filter(owner_id=owner_id)
        if raw_filter:
            qs = qs.filter(**nested_json_lookups("data", parse_json_object(raw_filter, "filter")))
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    queryset = Task.objects.select_related("owner").all()
    permission_classes = [IsOwnerOrAdmin]
