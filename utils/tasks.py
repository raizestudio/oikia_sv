from celery import Celery

from config import Settings

settings = Settings()
app = Celery("hello", broker=f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}@{settings.rabbitmq_host}//")


@app.task
def hello():
    return "hello world"
