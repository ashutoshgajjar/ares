import copy
import json
from typing import Any

from django.core.exceptions import ValidationError

SENSITIVE_PATHS = {
    ("financial", "creditCard", "cvv"),
    ("financial", "creditCard", "pin"),
}


def deep_merge(original: dict, updates: dict) -> dict:
    result = copy.deepcopy(original)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def redact_sensitive(data: Any) -> Any:
    result = copy.deepcopy(data)
    for path in SENSITIVE_PATHS:
        cursor = result
        for key in path[:-1]:
            if not isinstance(cursor, dict) or key not in cursor:
                cursor = None
                break
            cursor = cursor[key]
        if isinstance(cursor, dict):
            cursor.pop(path[-1], None)
    return result


# def validate_dynamic_payload(payload: Any, max_depth: int = 8, max_keys: int = 500):
#     if not isinstance(payload, dict):
#         raise ValidationError("Dynamic payload must be a JSON object.")
#     total_keys = 0
#     stack = [(payload, 0)]
#     while stack:
#         current, depth = stack.pop()
#         if depth > max_depth:
#             raise ValidationError("Dynamic payload nesting is too deep.")
#         for key, value in current.items():
#             total_keys += 1
#             if total_keys > max_keys:
#                 raise ValidationError("Dynamic payload contains too many keys.")
#             if not isinstance(key, str) or len(key) > 128:
#                 raise ValidationError("Dynamic payload keys must be strings of at most 128 characters.")
#             if isinstance(value, dict):
#                 stack.append((value, depth + 1))
#             elif isinstance(value, list) and len(value) > 500:
#                 raise ValidationError("Dynamic payload arrays are limited to 500 items.")


# old payload validation function
# def validate_dynamic_payload(payload):

#     if not isinstance(payload, dict):
#         raise ValueError("Payload must be a JSON object.")

#     allowed_sections = {
#         "metadata",
#         "personal",
#         "contact",
#         "location",
#         "professional",
#         "financial",
#         "network",
#         "preferences",
#         "security",
#         "assets",
#         "activity",
#     }

#     for key in payload:
#         if key not in allowed_sections:
#             raise ValueError(f"Unknown top-level field: {key}")

#     for section in allowed_sections:
#         value = payload.get(section)

#         if value is not None and not isinstance(value, dict):
#             raise ValueError(f"{section} must be an object.")

def validate_dynamic_payload(
    payload: Any,
    max_depth: int = 8,
    max_keys: int = 500,
    max_array_items: int = 500,
) -> None:
    """
    Validate a flexible JSON object without imposing application-specific
    top-level section names.

    Use this for dynamic task data, file metadata, and similar JSONB fields.
    User-profile section validation belongs in the user serializer because
    that schema has application-specific rules.
    """
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be a JSON object.")

    total_keys = 0
    stack = [(payload, 0)]

    while stack:
        current, depth = stack.pop()

        if depth > max_depth:
            raise ValidationError(
                f"Payload nesting cannot exceed {max_depth} levels."
            )

        for key, value in current.items():
            total_keys += 1

            if total_keys > max_keys:
                raise ValidationError(
                    f"Payload cannot contain more than {max_keys} keys."
                )

            if not isinstance(key, str) or not key.strip():
                raise ValidationError("Payload object keys must be non-empty strings.")

            if len(key) > 128:
                raise ValidationError(
                    "Payload object keys cannot exceed 128 characters."
                )

            if isinstance(value, dict):
                stack.append((value, depth + 1))
            elif isinstance(value, list):
                if len(value) > max_array_items:
                    raise ValidationError(
                        f"Payload arrays cannot contain more than {max_array_items} items."
                    )

                for item in value:
                    if isinstance(item, dict):
                        stack.append((item, depth + 1))


def validate_user_profile_schema(payload: Any) -> None:
    """Validate the known top-level structure of the dynamic user profile."""
    validate_dynamic_payload(payload)

    allowed_sections = {
        "metadata",
        "personal",
        "contact",
        "location",
        "professional",
        "financial",
        "network",
        "preferences",
        "security",
        "assets",
        "activity",
    }

    for key in payload:
        if key not in allowed_sections:
            raise ValidationError(f"Unknown top-level field: {key}")

    for section in allowed_sections:
        value = payload.get(section)
        if value is not None and not isinstance(value, dict):
            raise ValidationError(f"{section} must be an object.")



def parse_json_object(raw: str, parameter: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{parameter} must be valid JSON.") from exc
    validate_dynamic_payload(value)
    return value
