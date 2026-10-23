import logging
import uuid

from django.http import Http404
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from apps.common.pagination import DynamicLimitOffsetPagination
from apps.common.utils import parse_json_object
from apps.tasks.models import Task
from apps.users.models import User
from .exceptions import FileStorageAPIException, FileNotFound
from .models import FileVersion, StoredFile
from .permissions import IsFileOwnerOrAdmin
from .serializers import (
    FileCreateSerializer,
    FileMetadataUpdateSerializer,
    FileReplaceSerializer,
    FileVersionSerializer,
    StoredFileSerializer,
)
from .storage import R2StorageError, build_storage_key, get_r2_storage_service

logger = logging.getLogger(__name__)

SORT_FIELDS = {
    "name": "name",
    "file_type": "content_type",
    "content_type": "content_type",
    "size": "size",
    "created_at": "created_at",
    "updated_at": "updated_at",
    "version": "current_version",
}


def nested_json_lookups(prefix, payload):
    lookups = {}
    for key, value in payload.items():
        path = f"{prefix}__{key}"
        if isinstance(value, dict):
            lookups.update(nested_json_lookups(path, value))
        else:
            lookups[path] = value
    return lookups


def raise_storage_error(exc):
    raise FileStorageAPIException(detail=str(exc)) from exc


class FileListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicLimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        return FileCreateSerializer if self.request.method == "POST" else StoredFileSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            StoredFile.objects
            .filter(is_deleted=False)
            .select_related("user", "task")
            .prefetch_related(
                Prefetch(
                    "versions",
                    queryset=FileVersion.objects.order_by("-version"),
                    to_attr="prefetched_versions",
                )
            )
        )

        if not (user.is_superuser or user.role == "admin"):
            queryset = queryset.filter(user=user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        task_id = self.request.query_params.get("task_id")
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        q = self.request.query_params.get("q")
        name = self.request.query_params.get("name")
        file_type = self.request.query_params.get("file_type")
        min_size = self.request.query_params.get("min_size")
        max_size = self.request.query_params.get("max_size")
        created_from = self.request.query_params.get("created_from")
        created_to = self.request.query_params.get("created_to")
        raw_filter = self.request.query_params.get("filter")

        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(content_type__icontains=q))
        if name:
            queryset = queryset.filter(name__icontains=name)
        if file_type:
            queryset = queryset.filter(content_type__iexact=file_type)
        if min_size is not None:
            try:
                queryset = queryset.filter(size__gte=max(0, int(min_size)))
            except ValueError:
                raise ValidationError({"min_size": "Must be an integer."})
        if max_size is not None:
            try:
                queryset = queryset.filter(size__lte=max(0, int(max_size)))
            except ValueError:
                raise ValidationError({"max_size": "Must be an integer."})
        if created_from:
            parsed = parse_datetime(created_from)
            if not parsed:
                raise ValidationError({"created_from": "Must be a valid ISO-8601 datetime."})
            queryset = queryset.filter(created_at__gte=parsed)
        if created_to:
            parsed = parse_datetime(created_to)
            if not parsed:
                raise ValidationError({"created_to": "Must be a valid ISO-8601 datetime."})
            queryset = queryset.filter(created_at__lte=parsed)
        if raw_filter:
            try:
                filter_data = parse_json_object(raw_filter, "filter")
            except Exception as exc:
                raise ValidationError({"filter": str(exc)}) from exc
            queryset = queryset.filter(**nested_json_lookups("metadata", filter_data))

        sort_by = self.request.query_params.get("sort_by", "created_at")
        sort_order = self.request.query_params.get("sort_order", "desc").lower()
        if sort_by not in SORT_FIELDS:
            supported = ", ".join(SORT_FIELDS)
            raise ValidationError({"sort_by": f"Unsupported value. Supported values: {supported}."})
        if sort_order not in {"asc", "desc"}:
            raise ValidationError({"sort_order": "Must be 'asc' or 'desc'."})
        order_field = SORT_FIELDS[sort_by]
        if sort_order == "desc":
            order_field = f"-{order_field}"
        return queryset.order_by(order_field, "-id")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        uploaded = data["file"]
        target_user = data["target_user"]
        task = data["task"]
        file_id = uuid.uuid4()
        version = 1
        name = data.get("name") or uploaded.name
        content_type = uploaded.content_type or "application/octet-stream"
        metadata = data.get("metadata") or {}
        scope = "task" if task else "user"
        target_id = task.id if task else target_user.id
        storage = get_r2_storage_service()
        storage_key = build_storage_key(target_id, scope, str(file_id), version, name)

        try:
            checksum, _ = storage.upload(uploaded, storage_key)
            with transaction.atomic():
                stored_file = StoredFile.objects.create(
                    id=file_id,
                    user=target_user,
                    task=task,
                    name=name,
                    content_type=content_type,
                    size=int(uploaded.size),
                    current_version=version,
                    metadata=metadata,
                )
                FileVersion.objects.create(
                    file=stored_file,
                    version=version,
                    storage_key=storage_key,
                    original_name=name,
                    content_type=content_type,
                    size=int(uploaded.size),
                    checksum_sha256=checksum,
                    created_by=request.user,
                    metadata=metadata,
                )
        except R2StorageError as exc:
            raise_storage_error(exc)
        except Exception:
            try:
                storage.delete(storage_key)
            except R2StorageError:
                logger.exception("Unable to clean up orphaned R2 object", extra={"storage_key": storage_key})
            logger.exception("File database create failed", extra={"file_id": str(file_id)})
            raise

        response_serializer = StoredFileSerializer(
            stored_file,
            context={"request": request, "include_download_url": True},
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class FileDetailView(generics.GenericAPIView):
    permission_classes = [IsFileOwnerOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = StoredFile.objects.filter(is_deleted=False).select_related("user", "task")

    def get_object(self):
        try:
            obj = generics.get_object_or_404(
                self.get_queryset(),
                id=self.kwargs["pk"],
            )
        except Http404 as exc:
            raise FileNotFound() from exc

        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(StoredFileSerializer(obj, context={"request": request, "include_download_url": True}).data)

    def patch(self, request, *args, **kwargs):
        return self._update(request, require_file=False)

    def put(self, request, *args, **kwargs):
        return self._update(request, require_file=True)

    def _update(self, request, require_file):
        obj = self.get_object()
        has_file = "file" in request.FILES

        if require_file and not has_file:
            return Response({"error": {"code": "file_required", "message": "PUT requires a file."}}, status=400)

        if has_file:
            serializer = FileReplaceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            uploaded = data["file"]
            if uploaded.size > int(getattr(settings, "R2_MAX_UPLOAD_SIZE", 100 * 1024 * 1024)):
                return Response({"error": {"code": "file_too_large", "message": "File exceeds the configured maximum size."}}, status=413)

            new_version = obj.current_version + 1
            name = data.get("name") or uploaded.name
            content_type = uploaded.content_type or "application/octet-stream"
            metadata = data.get("metadata", obj.metadata)
            target_id = obj.task_id or obj.user_id
            scope = "task" if obj.task_id else "user"
            storage = get_r2_storage_service()
            storage_key = build_storage_key(target_id, scope, str(obj.id), new_version, name)

            try:
                checksum, _ = storage.upload(uploaded, storage_key)
                with transaction.atomic():
                    FileVersion.objects.create(
                        file=obj,
                        version=new_version,
                        storage_key=storage_key,
                        original_name=name,
                        content_type=content_type,
                        size=int(uploaded.size),
                        checksum_sha256=checksum,
                        created_by=request.user,
                        metadata=metadata,
                    )
                    obj.name = name
                    obj.content_type = content_type
                    obj.size = int(uploaded.size)
                    obj.current_version = new_version
                    obj.metadata = metadata
                    obj.save(update_fields=["name", "content_type", "size", "current_version", "metadata", "updated_at"])
            except R2StorageError as exc:
                raise_storage_error(exc)
            except Exception:
                try:
                    storage.delete(storage_key)
                except R2StorageError:
                    logger.exception("Unable to clean up orphaned replacement object", extra={"storage_key": storage_key})
                raise
        else:
            serializer = FileMetadataUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            if "name" in data:
                obj.name = data["name"]
            if "metadata" in data:
                obj.metadata = data["metadata"]
            if data:
                obj.save(update_fields=["name", "metadata", "updated_at"])

        obj.refresh_from_db()
        return Response(StoredFileSerializer(obj, context={"request": request, "include_download_url": True}).data)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        versions = list(obj.versions.values_list("storage_key", flat=True))
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

        try:
            get_r2_storage_service().delete_many(versions)
        except R2StorageError:
            # The DB record is already inaccessible through the normal API. A cleanup job can retry failed R2 deletes.
            logger.exception("R2 cleanup failed after file deletion", extra={"file_id": str(obj.id)})

        return Response(status=status.HTTP_204_NO_CONTENT)


class FileHistoryView(generics.ListAPIView):
    permission_classes = [IsFileOwnerOrAdmin]
    serializer_class = FileVersionSerializer
    pagination_class = DynamicLimitOffsetPagination

    def get_queryset(self):
        try:
            obj = generics.get_object_or_404(StoredFile.objects.all(),id=self.kwargs["pk"],)
        except Http404 as exc:
            raise FileNotFound() from exc

        self.check_object_permissions(self.request, obj)

        return (obj.versions.select_related("created_by").order_by("-version"))


class FileDownloadURLView(APIView):
    permission_classes = [IsFileOwnerOrAdmin]

    def get(self, request, pk):
        try:
            obj = generics.get_object_or_404(StoredFile.objects.filter(is_deleted=False),id=pk,)
        except Http404 as exc:
            raise FileNotFound() from exc

        self.check_object_permissions(request, obj)

        version_number = request.query_params.get("version")

        if version_number:
            try:
                version = obj.versions.get(version=int(version_number))
            except (ValueError, FileVersion.DoesNotExist) as exc:
                raise FileNotFound(
                    detail="Requested file version was not found.",
                ) from exc
        else:
            try:
                version = obj.versions.get(
                    version=obj.current_version
                )
            except FileVersion.DoesNotExist as exc:
                raise FileNotFound(
                    detail="Current file version was not found.",
                ) from exc

        try:
            url = get_r2_storage_service().presigned_download_url(version.storage_key,version.original_name,version.content_type,)
        except R2StorageError as exc:
            raise_storage_error(exc)

        return Response({"file_id": str(obj.id),"version": version.version,"expires_in": int(getattr(settings,"R2_PRESIGNED_URL_EXPIRY",900,)),"url": url})