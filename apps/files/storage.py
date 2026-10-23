import hashlib
import logging
import os
import re
import unicodedata
from functools import lru_cache
from datetime import datetime

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import get_valid_filename

logger = logging.getLogger(__name__)


class R2StorageError(Exception):
    """Safe storage-layer error exposed to the API layer."""


class R2StorageService:
    def __init__(self):
        account_id = os.getenv("R2_ACCOUNT_ID", "").strip()
        endpoint = os.getenv("R2_ENDPOINT_URL", "").strip()
        if not endpoint and account_id:
            endpoint = f"https://{account_id}.r2.cloudflarestorage.com"

        self.bucket = os.getenv("R2_BUCKET_NAME", "").strip()
        self.endpoint = endpoint
        self.max_size = int(os.getenv("R2_MAX_UPLOAD_SIZE", str(100 * 1024 * 1024)))
        self.url_expiry = int(os.getenv("R2_PRESIGNED_URL_EXPIRY", "900"))

        access_key = os.getenv("R2_ACCESS_KEY_ID", "").strip()
        secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()

        if not self.bucket or not self.endpoint or not access_key or not secret_key:
            raise R2StorageError(
                "Cloudflare R2 storage is not configured. Set R2_BUCKET_NAME, "
                "R2_ACCOUNT_ID or R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY."
            )

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    # def check_health(self) -> None:
    #         """Verify that the configured R2 bucket is reachable and accessible."""
    #         try:
    #             self.client.head_bucket(Bucket=self.bucket)
    #         except (BotoCoreError, ClientError) as exc:
    #             logger.warning(
    #                 "Cloudflare R2 health check failed (%s)",
    #                 type(exc).__name__,
    #             )
    #             raise R2StorageError(
    #                 "Cloudflare R2 connectivity check failed."
    #             ) from exc

    # def check_health(self) -> None:
    #         """Check access to a configured, known object in the R2 bucket."""
    #         healthcheck_key = os.getenv("R2_HEALTHCHECK_KEY", "").strip()
    #         if not healthcheck_key:
    #             raise R2StorageError(
    #                 "R2 health check is not configured. Set R2_HEALTHCHECK_KEY to an existing object key."
    #             )
    
    #         try:
    #             self.client.head_object(Bucket=self.bucket, Key=healthcheck_key)
    #         except ClientError as exc:
    #             error = exc.response.get("Error", {})
    #             metadata = exc.response.get("ResponseMetadata", {})
    #             logger.warning(
    #                 "R2 health check failed: code=%s http_status=%s request_id=%s",
    #                 error.get("Code", "unknown"),
    #                 metadata.get("HTTPStatusCode", "unknown"),
    #                 metadata.get("RequestId", "unknown"),
    #             )
    #             raise R2StorageError("Cloudflare R2 object health check failed.") from exc
    #         except BotoCoreError as exc:
    #             logger.warning(
    #                 "R2 connectivity check failed: error_type=%s error=%s",
    #                 type(exc).__name__, str(exc)[:500],
    #             )
    #             raise R2StorageError("Cloudflare R2 connectivity check failed.") from exc
            
    def check_health(self, object_key: str) -> None:
            """Check R2 access by inspecting a configured, existing object."""
            object_key = (object_key or "").strip()
            if not object_key:
                raise R2StorageError("R2 health-check object key is not configured.")
    
            try:
                self.client.head_object(Bucket=self.bucket, Key=object_key)
            except ClientError as exc:
                response = exc.response
                error_code = response.get("Error", {}).get("Code", "unknown")
                http_status = response.get("ResponseMetadata", {}).get("HTTPStatusCode", "unknown")
                logger.warning(
                    "R2 health probe failed: error_code=%s http_status=%s",
                    error_code,
                    http_status,
                )
                raise R2StorageError("Cloudflare R2 object health check failed.") from exc
            except BotoCoreError as exc:
                logger.warning(
                    "R2 connectivity check failed: error_type=%s",
                    type(exc).__name__,
                )
                raise R2StorageError("Cloudflare R2 connectivity check failed.") from exc
            
    @staticmethod
    def safe_filename(name: str) -> str:
        name = unicodedata.normalize("NFKC", os.path.basename(name or "file"))
        name = name.replace("\\", "_").replace("/", "_")
        name = re.sub(r"[\x00-\x1f\x7f]", "_", name)
        name = get_valid_filename(name) or "file"
        return name[:240]

    @staticmethod
    def checksum(uploaded_file: UploadedFile) -> str:
        digest = hashlib.sha256()
        uploaded_file.seek(0)
        for chunk in uploaded_file.chunks():
            digest.update(chunk)
        uploaded_file.seek(0)
        return digest.hexdigest()

    def validate_size(self, size: int):
        if size <= 0:
            raise R2StorageError("Empty files are not allowed.")
        if size > self.max_size:
            raise R2StorageError(
                f"File exceeds the configured maximum size of {self.max_size} bytes."
            )

    def upload(self, uploaded_file: UploadedFile, storage_key: str) -> tuple[str, str]:
        size = int(uploaded_file.size or 0)
        self.validate_size(size)
        checksum = self.checksum(uploaded_file)
        content_type = uploaded_file.content_type or "application/octet-stream"

        try:
            from boto3.s3.transfer import TransferConfig

            uploaded_file.seek(0)
            response = self.client.upload_fileobj(
                uploaded_file,
                self.bucket,
                storage_key,
                ExtraArgs={"ContentType": content_type, "Metadata": {"sha256": checksum}},
                Config=TransferConfig(
                    multipart_threshold=8 * 1024 * 1024,
                    multipart_chunksize=8 * 1024 * 1024,
                    max_concurrency=4,
                    use_threads=True,
                ),
            )
            return checksum, str(response or "")
        except (BotoCoreError, ClientError, OSError) as exc:
            logger.exception("R2 upload failed", extra={"storage_key": storage_key})
            raise R2StorageError("File upload to object storage failed.") from exc

    def delete(self, storage_key: str):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=storage_key)
        except (BotoCoreError, ClientError) as exc:
            logger.exception("R2 object deletion failed", extra={"storage_key": storage_key})
            raise R2StorageError("File deletion from object storage failed.") from exc

    def presigned_download_url(
        self,
        storage_key: str,
        filename: str,
        content_type: str,
        expires_in: int | None = None,
    ) -> str:
        expiry = expires_in if expires_in is not None else self.url_expiry
        expiry = max(1, min(int(expiry), 604800))
        safe_name = self.safe_filename(filename)
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": storage_key,
                    "ResponseContentType": content_type,
                    "ResponseContentDisposition": f'attachment; filename="{safe_name}"',
                },
                ExpiresIn=expiry,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("R2 presigned URL generation failed", extra={"storage_key": storage_key})
            raise R2StorageError("Unable to generate the file download URL.") from exc

    def delete_many(self, keys: list[str]):
        failures = []
        for key in keys:
            try:
                self.delete(key)
            except R2StorageError:
                failures.append(key)
        if failures:
            raise R2StorageError("Some file objects could not be deleted from object storage.")


def build_storage_key(target_id: str, scope: str, file_id: str, version: int, filename: str) -> str:
    if scope not in {"user", "task"}:
        raise ValueError("Invalid file storage scope.")
    safe_name = R2StorageService.safe_filename(filename)
    return f"   /{target_id}/{scope}/{file_id}/v{version}/{safe_name}"


@lru_cache(maxsize=1)
def get_r2_storage_service() -> R2StorageService:
    """Return one thread-safe boto3 client per application process."""
    return R2StorageService()
