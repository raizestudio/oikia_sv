from uuid import uuid4

from tortoise import fields
from tortoise.manager import Manager
from tortoise.models import Model
from tortoise.queryset import QuerySet


class Intent(Model):
    """Model for intents."""

    id = fields.UUIDField(pk=True)
    raw_input = fields.TextField()
    processed = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)

    attributes: fields.ReverseRelation["IntentAttributes"]
    recommendations: fields.ReverseRelation["Recommendation"]


class IntentAttributes(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    climate = fields.CharField(max_length=100, null=True)
    population_density = fields.CharField(max_length=100, null=True)
    proximity = fields.CharField(max_length=100, null=True)
    budget = fields.IntField(null=True)
    lifestyle = fields.JSONField(null=True)
    preferred_region = fields.CharField(max_length=100, null=True)

    intent = fields.OneToOneField("models.Intent", related_name="attributes")

    def __str__(self):
        return f"Attributes({self.intent_id})"


class Recommendation(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    score = fields.FloatField()
    reason = fields.TextField(null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)

    intent = fields.ForeignKeyField("models.Intent", related_name="recommendations")
    address = fields.ForeignKeyField("models.Address", related_name="recommendations")

    def __str__(self):
        return f"Recommendation({self.id})"
