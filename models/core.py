from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet


class Menu(Model):
    """Model for menus"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    parent = fields.IntField(null=True)

    def __str__(self):
        return self.name


class Category(Model):
    """Model for categories"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Tag(Model):
    """Model for tags"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
