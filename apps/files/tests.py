from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase


class FileAPIShapeTests(APITestCase):
    def test_storage_key_shape(self):
        from .storage import build_storage_key
        self.assertEqual(
            build_storage_key("abc", "user", "file-id", 2, "report.pdf"),
            "pyfiles/abc/user/file-id/v2/report.pdf",
        )
        self.assertEqual(
            build_storage_key("task-id", "task", "file-id", 1, "report.pdf"),
            "pyfiles/task-id/task/file-id/v1/report.pdf",
        )
