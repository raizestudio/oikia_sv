from celery import Celery

from config import Settings

settings = Settings()

celery_app = Celery(
    "oikia",
    broker=settings.celery_broker_url,
)

celery_app.conf.update(
    task_routes={
        "intents.tasks.*": {"queue": "intents"},
    },
)

import utils.tasks
