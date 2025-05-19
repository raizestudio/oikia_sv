from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet


class Client(Model):
    """Model for clients"""

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)

    def __str__(self):
        return self.name
