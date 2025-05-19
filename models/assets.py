from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet


class AssetType(Model):
    """Model for asset types."""

    code = fields.CharField(pk=True, max_length=50, unique=True)
    name = fields.CharField(max_length=255)

    def __str__(self):
        return self.name


class AssetPhotos(Model):
    """Model for asset photos."""

    id = fields.UUIDField(pk=True)
    image = fields.CharField(max_length=255)
    is_cover = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.image


class AssetManager(Manager):
    """Manager for Asset model."""


class AssetQuerySet(QuerySet):
    """QuerySet for Asset model."""


class Asset(Model):
    """Model for assets."""

    id = fields.UUIDField(pk=True)
    area = fields.FloatField()
    total_rooms = fields.IntField()
    latitude = fields.CharField(max_length=50)
    longitude = fields.CharField(max_length=50)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    asset_type = fields.ForeignKeyField("models.AssetType", related_name="asset_type")
    asset_photos = fields.ManyToManyField("models.AssetPhotos", related_name="asset_photos")
    address = fields.ForeignKeyField("models.Address", related_name="asset_address", null=True)

    def __str__(self):
        return self.name


class AssetTransactionType(Model):
    """Model for asset transaction types."""

    code = fields.CharField(pk=True, max_length=50, unique=True)
    name = fields.CharField(max_length=255)

    def __str__(self):
        return self.name


class AssetTransaction(Model):
    """Model for asset transaction history."""

    id = fields.UUIDField(pk=True)
    transaction_date = fields.DatetimeField(auto_now_add=True)
    transaction_amount = fields.FloatField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    transaction_type = fields.ForeignKeyField("models.AssetTransactionType", related_name="asset_transaction_type")
    asset = fields.ForeignKeyField("models.Asset", related_name="asset_transaction_history")

    def __str__(self):
        return self.transaction_type
