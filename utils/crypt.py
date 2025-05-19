import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from bcrypt import checkpw as bcrypt_checkpw
from bcrypt import gensalt, hashpw


def hash_password(password: str) -> str:
    return hashpw(password.encode(), gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt_checkpw(password.encode(), hashed.encode())


def generate_token(payload: Dict[str, Any], token_exp: int = 10):
    """
    Generate a token using jwt.

    :param user_email: The user email.
    :param token_exp: The token expiration time in seconds.

    :return: The generated jwt token.
    """
    exp_time = datetime.now(tz=timezone.utc) + timedelta(seconds=token_exp)
    payload.update({"exp": exp_time})

    generated_token = jwt.encode(payload, "secret", algorithm="HS256")

    return generated_token


def decode_token(token: str):
    """
    Decode a jwt token.

    :param token: The jwt token.

    :return: The decoded token.
    """
    try:
        decoded_token = jwt.decode(token, "secret", algorithms="HS256")

        print(f"Decoded token: {decoded_token}")
        return decoded_token

    except jwt.ExpiredSignatureError:
        return {"error": "expired"}

    except jwt.InvalidSignatureError:
        return {"error": "invalid_signature"}

    except jwt.DecodeError:
        return {"error": "invalid_decode"}

    except jwt.InvalidTokenError:
        return {"error": "invalid_token"}


def generate_refresh_token(length: int = 128):
    """
    Generate a refresh token using Base64 with a fixed length.

    :param length: The desired length of the resulting token.
    :return: A URL-safe Base64 encoded token.
    """
    num_bytes = (length * 3) // 4
    random_bytes = os.urandom(num_bytes)

    token = base64.urlsafe_b64encode(random_bytes).decode("utf-8")

    return token[:length] if len(token) > length else token.ljust(length, "=")
