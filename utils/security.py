import logging
from typing import Annotated, List, Optional, Union

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jwt import InvalidTokenError
from models.auth import ApiKey
from models.users import User
from tortoise.exceptions import DoesNotExist
from utils.crypt import decode_token

logger = logging.getLogger("auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_current_client(api_key: Annotated[str, Depends(api_key_header)]):
    """
    Validate and return the API client using the API key.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(api_key)
        if not payload:
            logger.warning(f"Attempt to access with invalid API key: {api_key}")
            raise credentials_exception

        if "client_id" not in payload:
            logger.warning(f"Attempt to access with expired API key: {api_key}")
            raise credentials_exception

        _api_key = await ApiKey.get(key=api_key).prefetch_related("client")

        return _api_key.client

    except DoesNotExist:
        logger.warning(f"Attempt to access with invalid API key: {api_key}")
        raise credentials_exception


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Get the current user from the token.
    """
    # TODO:
    # payload = decode_token(_token.token)
    # if not payload:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    # if "error" in payload:
    #     if payload["error"] == "expired":
    #         if _refresh.is_valid():
    #             _token_blacklist, tk_created = await TokenBlacklist.get_or_create(token=_token.token)
    #             await _token.delete()
    #             _token = await Token.create(token=generate_token({"email": str(_user.email)}, 10), user=_user)

    #         else:
    #             _token_blacklist, tk_created = await TokenBlacklist.get_or_create(token=_token.token)
    #             await _token.delete()
    #             await _refresh.delete()

    #             return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    #     else:
    #         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        if not payload:
            logger.warning(f"Attempt to access with invalid token: {token}")
            raise credentials_exception

        if "email" not in payload:
            logger.warning(f"Attempt to access with expired token: {token}")
            raise credentials_exception

        _user = await User.get(email=payload["email"])

        return _user

    except DoesNotExist:
        logger.warning(f"Attempt to access with missing user.")
        raise credentials_exception


async def get_current_user_or_client(
    api_key: Annotated[Optional[str], Depends(api_key_header)] = None,
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
):
    """
    Unified function to authenticate either a user or an API client.
    - If an API key is present, authenticate the client.
    - Otherwise, authenticate as a regular user.
    """
    if api_key:
        logger.warning(f"API Key: {api_key}")
        return await get_current_client(api_key)

    elif token:
        logger.warning(f"Token: {token}")
        return await get_current_user(token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials",
    )
