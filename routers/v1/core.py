import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, Security
from fastapi.responses import JSONResponse

from config import Settings
from models.clients import Client
from models.users import User
from models.core import Menu
from utils.security import get_current_user_or_client

settings = Settings()
router = APIRouter()

logger = logging.getLogger("uvicorn")


@router.get("/")
async def root():
    """
    Root endpoint.
    """
    return JSONResponse(content={"message": "Should i call you mistah?"})


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


@router.get("/menus", responses={200: {"description": "List of menus"}})
async def get_menu(request: Request):
    """
    Get the menu items.
    """
    menus = await Menu.all().order_by("id")
    # logger.info(f"Menu accessed by {str(current_user_or_client.id)} at {request.url}")
    return menus