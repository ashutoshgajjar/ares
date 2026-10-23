from rest_framework.exceptions import APIException, NotFound


class FileStorageAPIException(APIException):
    status_code = 502
    default_code = "file_storage_error"
    default_detail = "The file storage service could not complete the request."


class FileNotFound(NotFound):
    status_code = 404
    default_code = "file_not_found"
    default_detail = "The requested file was not found."