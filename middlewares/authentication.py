from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jwt import decode, exceptions

from models.users import User

SECRET_KEY = "secret"
ALGORITHM = "HS256"
PUBLIC_ROUTES = [
    "/",
    "/docs",
    "/health",
    "/auth/authenticate",
    "/auth/authenticate/token",
    "/auth/session",
    "/geo/continents",
    "/geo/continents/AF",
    "/users",
    "/services",
    "/services/types",
    "/services/types/edl",
    "/assets",
    "/assets/types",
    "/assets/0fe9d44b-5229-4311-ae1a-f64d4b38dc21",
]
app = FastAPI()


@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    if request.url.path.rstrip("/") in PUBLIC_ROUTES:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Authorization header missing or invalid"},
        )

    token = auth_header.split(" ")[1]
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("email")
        if not user_email:
            raise exceptions.DecodeError("Email not found in token")

        _user = await User.get(email=user_email)
        if not _user:
            return JSONResponse(status_code=404, content={"detail": "User not found"})

        request.state.user = _user

    except exceptions.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Token has expired"})
    except exceptions.DecodeError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    return await call_next(request)
