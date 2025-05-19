import asyncpg
from config import Settings
from tortoise.contrib.fastapi import register_tortoise

settings = Settings()


class Database:
    @staticmethod
    def init(app):
        """
        Initialize the database connection for the FastAPI app.

        Args:
            app: The FastAPI application instance.
            db_url: The database connection string.
        """
        register_tortoise(
            app,
            db_url=settings.db_url,
            modules={"models": [f"models.{model}" for model in settings.models]},
            generate_schemas=True,
            add_exception_handlers=True,
        )

    @staticmethod
    async def create_test_db():
        conn = await asyncpg.connect(user=settings.db_user, password=settings.db_password, database="postgres", host=settings.db_host)
        await conn.execute(f"DROP DATABASE IF EXISTS {settings.db_test_name};")
        await conn.execute(f"CREATE DATABASE {settings.db_test_name};")
        await conn.close()
