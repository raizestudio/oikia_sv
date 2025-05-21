from enum import Enum

from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet


class StatusEnum(str, Enum):
    ACTIVE = "active"


class RoleEnum(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    PATRON = "patron"
    OPERATOR = "operator"


class UserManager(Manager):
    """Manager for User model."""

    async def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a permission."""
        user = await self.get(id=user_id)
        return await user.permissions.filter(name=permission).exists()


class UserQuerySet(QuerySet):
    """QuerySet for User model."""

    def active(self):
        """Filter users that are active."""
        return self.filter(is_active=True)

    def inactive(self):
        """Filter users that are inactive."""
        return self.filter(is_active=False)


class User(Model):
    """Model for users."""

    id = fields.UUIDField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    password = fields.CharField(max_length=128)
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    is_active = fields.BooleanField(default=True)
    avatar = fields.CharField(max_length=255, null=True)
    # role = fields.CharEnumField(RoleEnum, default=RoleEnum.PATRON)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    phone_number = fields.ForeignKeyField("models.PhoneNumber", related_name="user_phone_numbers", null=True)
    email = fields.ForeignKeyField("models.Email", related_name="user_emails", null=True)
    # assets = fields.ManyToManyField("models.Asset", related_name="user_assets")
    # service_requests = fields.ManyToManyField("models.ServiceRequest", related_name="user_service_requests")
    permissions = fields.ManyToManyField("models.Permission", related_name="user_permissions")

    is_admin = fields.BooleanField(default=False)
    is_superuser = fields.BooleanField(default=False)
    
    all_objects = UserManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.username


class UserPreferences(Model):
    """Model for user preferences."""

    id = fields.IntField(pk=True)
    language = fields.ForeignKeyField("models.Language", related_name="user_language", null=True)
    currency = fields.ForeignKeyField("models.Currency", related_name="user_currency", null=True)
    timezone = fields.CharField(max_length=50, null=True)

    user = fields.OneToOneField("models.User", related_name="preferences")

    def __str__(self):
        return self.user.username


class UserSecurity(Model):
    """Model for user security."""

    id = fields.IntField(pk=True)
    is_mail_verified = fields.BooleanField(default=False)
    is_phone_verified = fields.BooleanField(default=False)
    anti_phishing_code = fields.CharField(max_length=50, null=True)

    user = fields.OneToOneField("models.User", related_name="security")

    def __str__(self):
        return self.user.username


class Profile(Model):
    """Model for user profile."""

    id = fields.IntField(pk=True)
    bio = fields.TextField(null=True)
    location = fields.CharField(max_length=100, null=True)
    birth_date = fields.DateField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    user = fields.OneToOneField("models.User", related_name="profile")

    def __str__(self):
        return self.user.username
