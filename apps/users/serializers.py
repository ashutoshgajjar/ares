# from django.db import transaction
# from django.contrib.auth.password_validation import validate_password
# from rest_framework import serializers

# from apps.common.utils import (
#     deep_merge,
#     redact_sensitive,
#     validate_dynamic_payload,
# )
# from .models import User

# class DynamicUserSerializer(serializers.Serializer):
#     """
#     Handles the dynamic user document.

#     Root-level:
#         id

#     Dynamic sections:
#         metadata
#         personal
#         contact
#         location
#         professional
#         financial
#         network
#         preferences
#         assets
#     """

#     password = serializers.CharField(
#         write_only=True,
#         required=False,
#         min_length=12,
#     )

#     def parse_profile(self, data):
#         if not isinstance(data, dict):
#             raise serializers.ValidationError(
#                 "Request body must be a JSON object."
#             )

#         profile = {
#             key: value
#             for key, value in data.items()
#             if key not in {"id", "password"}
#         }

#         validate_dynamic_payload(profile)

#         return profile

#     def validate_profile(self, profile):
#         metadata = profile.get("metadata", {})
#         contact = profile.get("contact", {})

#         if not isinstance(metadata, dict):
#             raise serializers.ValidationError({
#                 "metadata": "metadata must be an object."
#             })

#         if not isinstance(contact, dict):
#             raise serializers.ValidationError({
#                 "contact": "contact must be an object."
#             })

#         return profile

#     def to_representation(self, instance):
#         profile = redact_sensitive(
#             dict(instance.profile or {})
#         )

#         metadata = dict(
#             profile.get("metadata") or {}
#         )

#         metadata.update({
#             "createdAt": instance.created_at.isoformat(),
#             "updatedAt": instance.updated_at.isoformat(),
#             "accountStatus": instance.account_status,
#             "role": instance.role,
#             "is_active": instance.is_active,
#             "schema_version": instance.schema_version,
#         })

#         metadata.setdefault(
#             "version",
#             instance.schema_version,
#         )

#         metadata.setdefault(
#             "accountTier",
#             "standard",
#         )

#         profile["metadata"] = metadata

#         contact = dict(
#             profile.get("contact") or {}
#         )

#         if instance.email:
#             contact["email"] = instance.email

#         if instance.username:
#             contact["username"] = instance.username

#         profile["contact"] = contact

#         return {
#             "id": str(instance.id),
#             **profile,
#         }

# class UserSerializer(DynamicUserSerializer):
#     """
#     Used for GET/PATCH user operations.
#     """

#     def update(self, instance, validated_data):
#         request = self.context.get("request")

#         is_admin = bool(
#             request
#             and request.user.is_authenticated
#             and (
#                 request.user.is_superuser
#                 or request.user.role == "admin"
#             )
#         )

#         incoming_profile = self.parse_profile(
#             validated_data
#         )

#         instance.profile = deep_merge(
#             instance.profile or {},
#             incoming_profile,
#         )

#         profile = instance.profile

#         metadata = profile.get("metadata") or {}
#         contact = profile.get("contact") or {}

#         if is_admin:
#             instance.role = metadata.get(
#                 "role",
#                 instance.role,
#             )

#             instance.account_status = metadata.get(
#                 "accountStatus",
#                 instance.account_status,
#             )

#             instance.schema_version = metadata.get(
#                 "schema_version",
#                 instance.schema_version,
#             )

#             if contact.get("email"):
#                 instance.email = contact["email"]

#             if contact.get("username"):
#                 instance.username = contact["username"]

#         else:
#             protected = {
#                 "role",
#                 "accountStatus",
#                 "accountTier",
#                 "is_active",
#                 "schema_version",
#             }

#             for key in protected:
#                 metadata.pop(key, None)

#             if (
#                 contact.get("email")
#                 and contact["email"] != instance.email
#             ):
#                 raise serializers.ValidationError({
#                     "contact": {
#                         "email": (
#                             "Email changes require "
#                             "administrator approval."
#                         )
#                     }
#                 })

#         password = validated_data.get("password")

#         if password:
#             validate_password(
#                 password,
#                 instance,
#             )
#             instance.set_password(password)

#         instance.save()

#         return instance

# class RegisterSerializer(DynamicUserSerializer):
#     """
#     Public registration.

#     Accepts the complete dynamic user document,
#     but authentication/security metadata is controlled
#     by the backend.
#     """

#     def validate(self, attrs):
#         raw_data = self.initial_data

#         profile = self.parse_profile(raw_data)

#         self.validate_profile(profile)

#         contact = profile.get("contact") or {}
#         email = contact.get("email")
#         username = contact.get("username")

#         if not email:
#             raise serializers.ValidationError({
#                 "contact": {
#                     "email": "Email is required."
#                 }
#             })

#         if User.objects.filter(
#             email__iexact=email
#         ).exists():
#             raise serializers.ValidationError({
#                 "contact": {
#                     "email": "A user with this email already exists."
#                 }
#             })

#         if username and User.objects.filter(
#             username__iexact=username
#         ).exists():
#             raise serializers.ValidationError({
#                 "contact": {
#                     "username": (
#                         "This username is already in use."
#                     )
#                 }
#             })

#         password = raw_data.get("password")

#         if not password:
#             raise serializers.ValidationError({
#                 "password": "Password is required."
#             })

#         validate_password(password)

#         return {
#             "profile": profile,
#             "password": password,
#         }

#     @transaction.atomic
#     def create(self, validated_data):
#         profile = validated_data["profile"]
#         password = validated_data["password"]

#         contact = profile.get("contact") or {}
#         metadata = profile.get("metadata") or {}

#         email = contact.get("email")
#         username = contact.get("username")

#         # Backend-controlled authentication metadata.
#         metadata["accountStatus"] = "active"
#         metadata["accountTier"] = "standard"
#         metadata["role"] = "user"
#         metadata["is_active"] = True

#         metadata.setdefault(
#             "schema_version",
#             "1.0.0",
#         )

#         profile["metadata"] = metadata

#         return User.objects.create_user(
#             email=email,
#             username=username,
#             password=password,
#             role="user",
#             account_status="active",
#             schema_version=metadata["schema_version"],
#             profile=profile,
#         )

# from rest_framework_simplejwt.tokens import RefreshToken

# class LoginSerializer(serializers.Serializer):
#     contact = serializers.DictField()
#     password = serializers.CharField(
#         write_only=True
#     )

#     def validate(self, attrs):
#         contact = attrs.get("contact") or {}
#         email = contact.get("email")
#         password = attrs.get("password")

#         if not email:
#             raise serializers.ValidationError({
#                 "contact": {
#                     "email": "Email is required."
#                 }
#             })

#         user = (
#             User.objects
#             .filter(email__iexact=email)
#             .first()
#         )

#         if not user:
#             raise serializers.ValidationError({
#                 "detail": "Invalid email or password."
#             })

#         if not user.is_active:
#             raise serializers.ValidationError({
#                 "detail": "User account is inactive."
#             })

#         if not user.check_password(password):
#             raise serializers.ValidationError({
#                 "detail": "Invalid email or password."
#             })

#         refresh = RefreshToken.for_user(user)

#         refresh["role"] = user.role
#         refresh["account_status"] = user.account_status

#         return {
#             "refresh": str(refresh),
#             "access": str(refresh.access_token),
#         }

# class MeSerializer(UserSerializer):
#     """
#     Same flattened representation as UserSerializer.

#     The current authenticated user's ID is the only root-level
#     system field.
#     """

#     pass

# apps/users/serializers.py

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from apps.files.serializers import FileSummarySerializer
from apps.common.utils import (
    deep_merge,
    redact_sensitive,
    validate_dynamic_payload,
)

from .models import User

def extract_credentials(data):
    """
    Accept both:

    1. {
        "contact": {
            "email": "user@example.com"
        },
        "security": {
            "password": "password"
        }
    }

    2. {
        "email": "user@example.com",
        "password": "password"
    }
    """

    if not isinstance(data, dict):
        raise serializers.ValidationError(
            "Request body must be a JSON object."
        )

    contact = data.get("contact") or {}
    security = data.get("security") or {}

    if not isinstance(contact, dict):
        raise serializers.ValidationError({
            "contact": "contact must be an object."
        })

    if not isinstance(security, dict):
        raise serializers.ValidationError({
            "security": "security must be an object."
        })

    email = (
        contact.get("email")
        or data.get("email")
    )

    password = (
        security.get("password")
        or data.get("password")
    )

    return email, password

class DynamicUserSerializer(serializers.Serializer):

    def parse_profile(self, data):

        if not isinstance(data, dict):
            raise serializers.ValidationError(
                "User data must be a JSON object."
            )

        profile = {
            key: value
            for key, value in data.items()
            if key not in {
                "id",
                "email",
                "password",
            }
        }

        contact = profile.get("contact")

        if contact is None:
            contact = {}

        contact = dict(contact)

        # Root email is also supported.
        if data.get("email"):
            contact["email"] = data["email"]

        profile["contact"] = contact

        security = dict(
            profile.get("security") or {}
        )

        # Never keep plaintext password in profile.
        security.pop("password", None)

        profile["security"] = security

        validate_dynamic_payload(profile)

        return profile

    def validate(self, attrs):

        data = self.initial_data

        if not isinstance(data, dict):
            raise serializers.ValidationError(
                "User data must be a JSON object."
            )

        profile = self.parse_profile(data)

        metadata = profile.get("metadata", {})
        contact = profile.get("contact", {})

        if not isinstance(metadata, dict):
            raise serializers.ValidationError({
                "metadata": "metadata must be an object."
            })

        if not isinstance(contact, dict):
            raise serializers.ValidationError({
                "contact": "contact must be an object."
            })

        email, password = extract_credentials(data)

        if email:
            attrs["_email"] = email.lower()

        attrs["_username"] = contact.get("username")

        if password:
            attrs["_password"] = password

        attrs["_profile"] = profile

        return attrs

class UserResponseSerializer(serializers.Serializer):
    """
    Returns the complete dynamic user document.
    """

    files = serializers.SerializerMethodField()

    def get_files(self, instance):
        """
        Return active files belonging to this user.

        Uses prefetched files when available to avoid
        N+1 database queries.
        """

        files = getattr(
            instance,
            "prefetched_files",
            None,
        )

        if files is None:
            files = (
                instance.files
                .filter(
                    is_deleted=False
                )
                .order_by("-created_at")
            )

        return FileSummarySerializer(
            files,
            many=True,
            context=self.context,
        ).data


    def to_representation(self, instance):

        profile = dict(instance.profile or {})

        # Never expose plaintext password or other secrets.
        security = dict(
            profile.get("security") or {}
        )

        security.pop("password", None)
        security.pop("pin", None)
        security.pop("cvv", None)

        profile["security"] = security

        # Protect financial secrets.
        financial = dict(
            profile.get("financial") or {}
        )

        credit_card = dict(
            financial.get("creditCard") or {}
        )

        credit_card.pop("cvv", None)
        credit_card.pop("pin", None)

        financial["creditCard"] = credit_card
        profile["financial"] = financial

        # Metadata
        metadata = dict(
            profile.get("metadata") or {}
        )

        metadata.update({
            "createdAt": instance.created_at.isoformat(),
            "updatedAt": instance.updated_at.isoformat(),
            "accountStatus": instance.account_status,
            "role": instance.role,
            "is_active": instance.is_active,
            "schema_version": instance.schema_version,
        })

        metadata.setdefault(
            "version",
            instance.schema_version,
        )

        metadata.setdefault(
            "accountTier",
            "standard",
        )

        profile["metadata"] = metadata

        # Contact
        contact = dict(
            profile.get("contact") or {}
        )

        if instance.email:
            contact["email"] = instance.email

        if instance.username:
            contact["username"] = instance.username

        profile["contact"] = contact

        profile["files"] = self.get_files(instance)

        return {
            "id": str(instance.id),
            **profile,
        }

class UserSerializer(DynamicUserSerializer):
    """
    Used for GET/PATCH user operations.
    """

    def create(self, validated_data):
        profile = validated_data.pop("_profile", {})
        password = validated_data.pop("password", None)

        email = validated_data.pop(
            "_email",
            None,
        )

        username = validated_data.pop(
            "_username",
            None,
        )

        metadata = dict(profile.get("metadata") or {})

        account_status = metadata.get(
            "accountStatus",
            "active",
        )

        role = metadata.get(
            "role",
            "user",
        )

        schema_version = metadata.get(
            "schema_version",
            metadata.get(
                "version",
                "1.0.0",
            ),
        )

        user = User(
            email=email,
            username=username,
            role=role,
            account_status=account_status,
            schema_version=schema_version,
            profile=profile,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

        return user

    @transaction.atomic
    def update(self, instance, validated_data):

        profile_update = validated_data.pop(
            "_profile",
            {},
        )

        password = validated_data.pop(
            "password",
            None,
        )

        current_profile = dict(instance.profile or {})

        merged_profile = deep_merge(
            current_profile,
            profile_update,
        )

        metadata = dict(merged_profile.get("metadata") or {})

        contact = dict(merged_profile.get("contact") or {})

        if "email" in contact:
            instance.email = contact["email"].lower()

        if "username" in contact:
            instance.username = contact["username"]

        if "accountStatus" in metadata:
            instance.account_status = metadata["accountStatus"]

        # if "role" in metadata:
        #     instance.role = metadata["role"]

        if "schema_version" in metadata:
            instance.schema_version = metadata["schema_version"]
        elif "version" in metadata:
            instance.schema_version = metadata["version"]

        if password:
            validate_password(
                password,
                instance,
            )
            instance.set_password(password)

        instance.profile = merged_profile
        instance.save()

        return instance


class RegisterSerializer(DynamicUserSerializer):

    def validate(self, attrs):

        attrs = super().validate(attrs)

        email = attrs.get("_email")
        password = attrs.get("_password")

        if not email:
            raise serializers.ValidationError({
                "contact": {
                    "email": "Email is required."
                }
            })

        if not password:
            raise serializers.ValidationError({
                "security": {
                    "password": "Password is required."
                }
            })

        validate_password(password)

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise serializers.ValidationError({
                "contact": {
                    "email": (
                        "A user with this email "
                        "already exists."
                    )
                }
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        profile = dict(
            validated_data.pop("_profile", {})
        )

        password = validated_data.pop("_password")
        email = validated_data.pop("_email")
        username = validated_data.pop(
            "_username",
            None,
        )

        metadata = dict(
            profile.get("metadata") or {}
        )

        # Public registration controls these.
        metadata["accountStatus"] = "active"
        metadata["accountTier"] = "standard"
        metadata["role"] = "user"
        metadata["is_active"] = True

        schema_version = metadata.get(
            "schema_version",
            metadata.get(
                "version",
                "1.0.0",
            ),
        )

        metadata["schema_version"] = schema_version
        profile["metadata"] = metadata

        contact = dict(
            profile.get("contact") or {}
        )

        contact["email"] = email

        if username:
            contact["username"] = username

        profile["contact"] = contact

        # Never store plaintext password.
        security = dict(
            profile.get("security") or {}
        )

        security.pop("password", None)

        profile["security"] = security

        user = User(
            email=email,
            username=username,
            role="user",
            account_status="active",
            schema_version=schema_version,
            profile=profile,
        )

        user.set_password(password)
        user.save()

        return user


class LoginSerializer(serializers.Serializer):

    def validate(self, attrs):

        data = self.initial_data

        email, password = extract_credentials(data)

        if not email:
            raise serializers.ValidationError({
                "contact": {
                    "email": "Email is required."
                }
            })

        if not password:
            raise serializers.ValidationError({
                "security": {
                    "password": "Password is required."
                }
            })

        user = (
            User.objects
            .filter(email__iexact=email)
            .first()
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is not active."
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        attrs["user"] = user

        return attrs


class MeSerializer(UserSerializer):
    """
    Same flattened representation as UserSerializer.

    The current authenticated user's ID is the only root-level
    system field.
    """

    pass
