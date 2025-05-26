import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.transactions import in_transaction

from models.auth import ApiKey, Refresh, Session, Token, TokenBlacklist
from models.clients import Client
from models.geo import Email
from models.users import User
from schemas.auth import SessionCreateSchema
from schemas.users import UserCreate, UserRead
from utils.crypt import (
    check_password,
    generate_refresh_token,
    generate_token,
    hash_password,
)

logger = logging.getLogger("auth")
router = APIRouter()


@router.post(
    "/register",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
    },
)
async def register_user(user: UserCreate):
    async with in_transaction():
        email, created = await Email.get_or_create(email=user.email)
        if not created:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        try:
            encrypted_password = hash_password(user.password)
            _ = await User.create(
                username=user.username,
                password=encrypted_password,
                email=email,
                first_name=user.first_name,
                last_name=user.last_name,
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        return JSONResponse(
            content={
                "detail": "User created successfully",
                "user": UserRead.model_dump_json(user),
            }
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="User could not be created",
    )


@router.post("/authenticate", responses={status.HTTP_200_OK: {"description": "Successful connection"}, status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"}})
async def authenticate_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Authenticate a user with the provided credentials, will always issue a new token and refresh.
    If token exists it will be blacklisted.
    """
    try:
        _user = await User.get(email=form_data.username).prefetch_related("email")

    except DoesNotExist:
        logger.warning(f"Authentication attempt with missing user", extra={"user_email": form_data.username, "password": form_data.password})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if not check_password(form_data.password, _user.password):
        logger.warning(f"Authentication attempt for {form_data.username}, user was denied", extra={"user_email": form_data.username, "password": form_data.password})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    _token, created = await Token.get_or_create(user=_user, defaults={"token": generate_token({"email": str(_user.email)})})
    _refresh, created = await Refresh.get_or_create(user=_user, defaults={"token": generate_refresh_token()})

    if not created:
        _token_blacklist, tk_created = await TokenBlacklist.get_or_create(token=_token.token)
        await _token.delete()
        await _refresh.delete()
        _token = await Token.create(token=generate_token({"email": str(_user.email)}, 10), user=_user)
        _refresh = await Refresh.create(token=generate_refresh_token(), user=_user)

    logger.info(f"User {str(_user.id)} authenticated successfully")
    return {
        "token": _token.token,
        "refresh": _refresh.token,
    }


@router.post("/session", responses={status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"}})
async def create_session(session: SessionCreateSchema):
    """
    Detect if there's already a session for a given connection.
    If there's no session, create one.

    Args:
        session (SessionCreateSchema): Session data

    Returns:
        dict: Session data
    """
    print(session)
    if not session.ip_v4 and not session.ip_v6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="IP address is required")

    _session = None
    created = False

    if session.ip_v4:
        try:
            _session = await Session.get(ip_v4=session.ip_v4)

        except DoesNotExist:
            _session = await Session.create(ip_v4=session.ip_v4)
            created = True

    if session.ip_v6:
        try:
            print("Getting session")
            _session = await Session.get(ip_v6=session.ip_v6)
        except DoesNotExist:
            print("Creating session")
            _session = await Session.create(ip_v6=session.ip_v6)
            created = True

    if _session is None:
        _session = await Session.create(ip_v4=session.ip_v4, ip_v6=session.ip_v6)
        created = True

    return {"session": _session, "created": created}


@router.get("/api-key")
async def create_api_key():
    """
    Create an API key for the client.

    Returns:
        dict: API key data
    """
    print("Creating API key")
    _client = await Client.create(name="aa")
    token = generate_token({"client_id": str(_client.id)})
    _api_key = await ApiKey.create(key=token, client=_client)
    return {"api_key": _api_key.key}
