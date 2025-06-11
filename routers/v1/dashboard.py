from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from config import Settings
from models.users import User

# from schemas.users import UserRead

settings = Settings()
router = APIRouter()


@router.get("/")
async def dashboard_overview(request: Request):
    """
    Dashboard overview endpoint.
    """
    _users_last_7_days = await User.filter(created_at__gte=datetime.now() - timedelta(days=7)).count()
    _users_previous_7_days = await User.filter(created_at__gte=datetime.now() - timedelta(days=14), created_at__lt=datetime.now() - timedelta(days=7)).count()

    if _users_previous_7_days == 0:
        if _users_last_7_days == 0:
            _users_diff_percentage = 0
        else:
            _users_diff_percentage = 100
    else:
        _users_diff_percentage = (_users_last_7_days - _users_previous_7_days) / _users_previous_7_days * 100 if _users_previous_7_days > 0 else 0

    return JSONResponse(
        content={
            "data": {
                "users_last_7_days": _users_last_7_days,
                "users_previous_7_days": _users_previous_7_days,
                "users_diff_percentage": _users_diff_percentage,
            },
        },
        status_code=200,
    )
