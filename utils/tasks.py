import asyncio

from tortoise import Tortoise

from config import Settings
from models.intents import Intent
from utils.worker import celery_app

settings = Settings()


@celery_app.task
def process_user_intent(intent_id: str):
    print(f"Processing intent {intent_id}")
    return asyncio.run(_process_intent(intent_id))


async def _process_intent(intent_id: str):
    await Tortoise.init(
        db_url=settings.db_url,
        modules={
            "models": [
                "models.geo",
                "models.intents",
            ]
        },
    )
    _intent = await Intent.get(id=intent_id)
    _intent.processed = True
    await _intent.save()
    return {"status": "done", "id": intent_id}
