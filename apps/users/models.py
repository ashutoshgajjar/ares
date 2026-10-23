# apps/users/models.py

import uuid
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.contenttypes.fields import GenericRelation

class UserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields,)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("account_status", "active")
        extra_fields.setdefault("is_active", True)

        return self.create_user(email=email,password=password,**extra_fields,)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,)
    username = models.CharField(max_length=150,unique=True,null=True,blank=True,db_index=True,)
    email = models.EmailField(unique=True,null=True,blank=True,db_index=True,)
    role = models.CharField(max_length=64,default="guest",db_index=True,)
    account_status = models.CharField(max_length=64,default="active",db_index=True,)
    profile = models.JSONField(default=dict,blank=True,)
    schema_version = models.CharField(max_length=32,default="1.0.0",)
    is_active = models.BooleanField(default=True,db_index=True,)
    is_staff = models.BooleanField(default=False, )
    created_at = models.DateTimeField(auto_now_add=True, )
    updated_at = models.DateTimeField(auto_now=True, )
    
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users_user"
        indexes = [GinIndex(fields=["profile"]),        ]

    def save(self, *args, **kwargs):
        self.is_active = self.account_status not in {"banned","suspended","archived",}
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or str(self.id)

class UserSession(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    last_used_at = models.DateTimeField(
        default=timezone.now,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
        default="",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "users_user_session"
        indexes = [
            models.Index(
                fields=["user", "revoked_at"],
            ),
            models.Index(
                fields=["created_at"],
            ),
        ]

    @property
    def is_active(self):
        return self.revoked_at is None

    def revoke(self):
        if self.revoked_at is None:
            self.revoked_at = timezone.now()
            self.save(
                update_fields=["revoked_at"]
            )   

class RevokedAccessToken(models.Model):
    """Database-backed denylist for access-token JTIs.

    A database-backed denylist works across horizontally scaled API instances.
    Expired rows can be removed periodically with a maintenance job.
    """

    id = models.BigAutoField(primary_key=True)
    jti = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="revoked_access_tokens")
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_revoked_access_token"
        indexes = [
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["expires_at"]),
        ]