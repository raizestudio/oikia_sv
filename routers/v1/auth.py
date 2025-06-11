import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.transactions import in_transaction

from models.auth import ApiKey, Refresh, Session, Token, TokenBlacklist
from models.clients import Client
from models.geo import Email
from models.users import User
from schemas.auth import (
    AuthenticationTokenSchema,
    RefreshRead,
    SessionCreateSchema,
    SessionRead,
    TokenAuthenticate,
    TokenRead,
)
from schemas.pagination import PaginatedResponse
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

    _token, _token_created = await Token.get_or_create(user=_user, defaults={"token": generate_token({"email": str(_user.email)})})
    _refresh, _refresh_created = await Refresh.get_or_create(user=_user, defaults={"token": generate_refresh_token()})
    _session, _session_created = await Session.get_or_create(token=_token, refresh=_refresh, defaults={"user": _user})

    if not _token_created:
        _token_blacklist, tk_created = await TokenBlacklist.get_or_create(token=_token.token)
        await _token.delete()
        await _refresh.delete()
        _token = await Token.create(token=generate_token({"email": str(_user.email)}, 10), user=_user)
        _refresh = await Refresh.create(token=generate_refresh_token(), user=_user)
        _session, _session_created = await Session.update_or_create(token=_token, refresh=_refresh, defaults={"user": _user})

    logger.info(f"User {str(_user.id)} authenticated successfully")
    return {"token": _token.token, "refresh": _refresh.token, "session": _session.id}


@router.post(
    "/authenticate/token", response_model=AuthenticationTokenSchema, response_model_by_alias=False, responses={status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"}}
)
async def authenticate_token(request: Request, payload: TokenAuthenticate):
    """
    Authenticate a user with the provided token.
    If the token is valid, return the user information.

    Args:
        token (str): The token to authenticate

    Returns:
        dict: User information
    """
    try:
        _token = await Token.get(token=payload.token)
        _user = await User.get(id=_token.user_id).values(
            "id",
            "username",
            "email__email",
            "first_name",
            "last_name",
            "avatar",
            "created_at",
            "updated_at",
            "is_active",
            "is_admin",
            "is_superuser",
            "phone_number__phone_number",
            "phone_number__calling_code__code",
        )
        _refresh = await Refresh.get(user=_user.get("id"))

        avatar = _user.get("avatar")
        if avatar:
            _user["avatar"] = str(request.url_for("uploads", path=avatar))
        else:
            _user["avatar"] = None

        return AuthenticationTokenSchema(token=_token.token, refresh=_refresh.token, user=UserRead.model_validate(_user))

    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


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


@router.get("/tokens", response_model=PaginatedResponse[TokenRead], response_model_by_alias=False)
async def get_tokens(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Get paginated list of tokens."""
    count = await Token.all().count()
    offset = (page - 1) * size
    _tokens = await Token.all().offset(offset).limit(size).values("token", "created_at", "user__id")

    return PaginatedResponse[TokenRead](
        count=count,
        page=page,
        size=size,
        data=_tokens,
    )


@router.get("/refreshes", response_model=PaginatedResponse[RefreshRead], response_model_by_alias=False)
async def get_refresh_tokens(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Get paginated list of refresh tokens."""
    count = await Refresh.all().count()
    offset = (page - 1) * size
    _refresh_tokens = await Refresh.all().offset(offset).limit(size).values("token", "created_at", "expire_at", "user__id")

    return PaginatedResponse[RefreshRead](
        count=count,
        page=page,
        size=size,
        data=_refresh_tokens,
    )


@router.get("/sessions", response_model=PaginatedResponse[SessionRead], response_model_by_alias=False)
async def get_sessions(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """Get paginated list of sessions."""
    count = await Session.all().count()
    offset = (page - 1) * size
    _sessions = (
        await Session.all().offset(offset).limit(size).values("id", "ip_v4", "ip_v6", "ip_type", "ip_class", "isp", "os", "user_agent", "created_at", "updated_at", "user__id")
    )

    return PaginatedResponse[SessionRead](
        count=count,
        page=page,
        size=size,
        data=_sessions,
    )
