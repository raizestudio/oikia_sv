from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # APP
    app_name: str = "Oikia"
    app_version: str = "0.0.1"
    app_api_version: str = "1"
    app_api_host: str = "localhost"
    # LOGGING
    log_file_path: str = "logs"
    log_file_name: str = "api.log"
    log_file_max_bytes: int = 5 * 1024 * 1024
    log_backup_count: int = 3
    # DB
    db_user: str = "oikia"
    db_password: str = "oikia"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "oikia"
    db_url: str = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    db_test_name: str = "oikia_test"
    db_url_test: str = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_test_name}"
    # CACHE
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_db: int = 0
    cache_ttl: int = 60
    # RABBITMQ
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "admin"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    # COMMON
    debug: bool = True

    models: List[str] = [
        "core",
        "users",
        "auth",
        "clients",
        "geo",
        "assets",
        "intents",
    ]

    required_dirs: List[str] = [
        "uploads",
        "uploads/avatars",
        "uploads/documents",
        "logs",
    ]

    class Config:
        env_file = ".env"

    @property
    def celery_broker_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}" f"@{self.rabbitmq_host}:{self.rabbitmq_port}//"

    @property
    def fixtures_path(self) -> Path:
        return Path(__file__).resolve().parent / "fixtures"

    @property
    def csv_path(self) -> Path:
        return Path(__file__).resolve().parent / "data" / "csv"

    @property
    def json_path(self) -> Path:
        return Path(__file__).resolve().parent / "data" / "json"
