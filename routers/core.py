import logging
from typing import Annotated

from config import Settings
from fastapi import APIRouter, Depends, Request, Response, Security
from fastapi.responses import JSONResponse
from models.clients import Client
from models.users import User
from utils.security import get_current_user_or_client

settings = Settings()
router = APIRouter()

logger = logging.getLogger("uvicorn")


@router.get("/health")
async def health():
    """
    Just a simple health check endpoint.
    """
    return Response(status_code=200)


@router.get("/info", responses={200: {"description": "API information"}, 401: {"description": "Unauthorized"}})
async def info(request: Request, current_user_or_client: Annotated[User | Client, Depends(get_current_user_or_client)]):
    """
    Endpoint that return API app information.
    """
    response = {
        "name": settings.app_name,
        "version": settings.app_version,
        "version_api": settings.app_api_version,
    }
    if isinstance(current_user_or_client, User):
        logger.info(f"User {str(current_user_or_client.id)} accessed the {request.url} endpoint")
        response.update({"user": str(current_user_or_client.id)})

    elif isinstance(current_user_or_client, Client):
        logger.info(f"Client {str(current_user_or_client.id)} accessed the {request.url} endpoint")
        response.update({"client": str(current_user_or_client.id)})

    return JSONResponse(content=response)
