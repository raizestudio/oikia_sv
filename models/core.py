from tortoise import fields
from tortoise.exceptions import ValidationError
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet


class Menu(Model):
    """Model for menus"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    path = fields.CharField(max_length=255, null=True)
    icon = fields.CharField(max_length=255, null=True)
    description = fields.TextField(null=True)

    parent = fields.ForeignKeyField("models.Menu", related_name="children", null=True, on_delete=fields.SET_NULL)

    class Meta:
        unique_together = ("name", "parent")

    def __str__(self):
        return self.name

    async def save(self, *args, **kwargs):
        await super().save(*args, **kwargs)


class Category(Model):
    """Model for categories"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Tag(Model):
    """Model for tags"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
