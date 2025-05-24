from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

from config import Settings
from models.auth import ApiKey
from models.clients import Client
from models.geo import Email
from models.users import User
from routers import core
from utils.crypt import generate_token, hash_password
from utils.db import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


settings = Settings()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(core.router, tags=["Core"])
# app.include_router(users.router, prefix="/users", tags=["Users"])
# app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(assets.router, prefix="/assets", tags=["Assets"])
# app.include_router(geo.router, prefix="/geo", tags=["Geo"])

db = Database()


@pytest.fixture(autouse=True)
async def init_db():
    """Set up and tear down the test database."""
    await db.create_test_db()
    await Tortoise.init(
        db_url=settings.db_url_test,
        modules={"models": [f"models.{model}" for model in settings.models]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture(autouse=True)
async def client():
    """Create an HTTP client for tests."""
    async with AsyncClient(base_url="http://test", transport=ASGITransport(app=app)) as client:
        yield client


@pytest.fixture
async def test_client():
    """Create a test client with an API key."""
    _client = await Client.create(name="test_client")
    _api_key = await ApiKey.create(key=generate_token({"client_id": str(_client.id)}), client=_client)
    yield _api_key.key, str(_client.id)


@pytest.fixture
async def test_user():
    """Create a test user token."""
    _email = await Email.create(email="test@test.io")
    _user = await User.create(username="test_user", first_name="Coco", last_name="Jojo", email=_email, password=hash_password("test"))
    yield _user


@pytest.fixture
async def test_token():
    """Create a test token."""
    _email = await Email.create(email="test@test.io")
    _user = await User.create(username="test_user", first_name="Coco", last_name="Jojo", email=_email, password="test")
    yield generate_token({"email": str(_user.email)}), str(_user.id)
