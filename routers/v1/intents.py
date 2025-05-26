from fastapi import APIRouter, Query, status

from models.intents import Intent, IntentAttributes, Recommendation
from schemas.intents import IntentCreate
from utils.tasks import process_user_intent

router = APIRouter()


@router.get("/")
async def get_intents():
    """
    Get a list of intents.
    """
    _intents = await Intent.all().prefetch_related("attributes", "recommendations")
    return _intents


@router.get("/{intent_id}")
async def get_intent(intent_id: str):
    """
    Get a specific intent by ID.
    """
    _intent = await Intent.get(id=intent_id).prefetch_related("attributes", "recommendations")
    return _intent


@router.post("/", response_model=IntentCreate, status_code=status.HTTP_201_CREATED)
async def create_intent(intent: IntentCreate):
    """
    Create a new intent.
    """
    _intent = await Intent.create(**intent.model_dump())
    process_user_intent.delay(_intent.id)
    return _intent
