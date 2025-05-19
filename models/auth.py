from datetime import datetime, timedelta, timezone
from enum import Enum

from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet


class IPTypeEnum(str, Enum):
    UNKNOWN = "unknown"
    PUBLIC = "public"
    PRIVATE = "private"


class IPClassEnum(str, Enum):
    UNKNOWN = "unknown"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


def default_expire_at():
    """Return a datetime 24 hours from now."""
    return datetime.now(timezone.utc) + timedelta(hours=24)


class TokenManager(Manager):
    """Manager for Token model."""


class TokenQuerySet(QuerySet):
    """QuerySet for Token model."""


class Token(Model):
    """Model for tokens."""

    token = fields.CharField(max_length=255, pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    user = fields.ForeignKeyField("models.User", related_name="tokens")

    def __str__(self):
        return self.token


class TokenBlacklist(Model):
    """Model for blacklisted tokens."""

    token = fields.CharField(max_length=255, pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.token


class Refresh(Model):
    """Model for refresh tokens"""

    token = fields.CharField(max_length=255, pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    expire_at = fields.DatetimeField(default=default_expire_at)

    user = fields.ForeignKeyField("models.User", related_name="refresh_tokens")

    def is_valid(self) -> bool:
        """
        Check if the refresh token is valid (i.e., not expired).
        :return: True if valid, False otherwise.
        """
        return datetime.now(timezone.utc) < self.expire_at

    def __str__(self):
        return self.token


class ApiKey(Model):
    """Model for API keys"""

    key = fields.CharField(pk=True, max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    client = fields.ForeignKeyField("models.Client", related_name="api_keys")

    def __str__(self):
        return self.key


class Session(Model):
    """Model for sessions"""

    id = fields.UUIDField(pk=True)
    ip_v4 = fields.CharField(max_length=15, null=True)
    ip_v6 = fields.CharField(max_length=64, null=True)
    ip_type = fields.CharEnumField(IPTypeEnum, default=IPTypeEnum.UNKNOWN)
    ip_class = fields.CharEnumField(IPClassEnum, default=IPClassEnum.UNKNOWN)
    isp = fields.CharField(max_length=255, null=True)
    os = fields.CharField(max_length=255, null=True)
    user_agent = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    token = fields.ForeignKeyField("models.Token", related_name="tokens", null=True)
    refresh = fields.ForeignKeyField("models.Refresh", related_name="refresh_tokens", null=True)
    user = fields.ForeignKeyField("models.User", related_name="users", null=True)

    def __str__(self):
        return str(self.id)


class Permission(Model):
    """Model for permissions"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)

    def __str__(self):
        return self.name
