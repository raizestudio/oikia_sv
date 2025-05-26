from typing import Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)

# from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.expressions import Q

from models.users import User
from schemas.pagination import PaginatedResponse
from schemas.users import UserCreate, UserRead

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserRead], response_model_by_alias=False, responses={200: {"description": "List of users"}})
async def get_users(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    """
    Retrieve a list of users, according to filters provided.
    """
    count = await User.all().count()
    offset = (page - 1) * size

    _users = (
        await User.all()
        .offset(offset)
        .limit(size)
        .values(
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
        )
    )
    return PaginatedResponse[UserRead](
        count=count,
        page=page,
        size=size,
        data=_users,
    )


@router.get(
    "/{user_email}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
async def get_user(user_email: str):
    """
    Retrieve a user.
    """
    _user: UserRead = await User.get(email=user_email)

    if not _user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return _user


@router.post(
    "/",
    responses={400: {"description": "User with this email or username already exists"}},
)
async def create_user(user: UserCreate):
    """
    Create a user with the provided data.
    """
    try:
        new_user = await User.create(
            username=user.username,
            password=user.password,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        return {"message": "User created successfully", "user": new_user}
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email or username already exists",
        )


@router.put(
    "/{user_id}",
    responses={404: {"description": "User not found"}},
)
async def update_user(user_id: int, user: UserCreate):
    """
    Update a user with the provided data.
    """
    _user: UserRead = await User.get(id=user_id)
    if not _user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await _user.update(
        username=user.username,
        password=user.password,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    return {"message": "User updated successfully", "user": _user}


@router.patch(
    "/{user_id}",
    responses={404: {"description": "User not found"}},
)
async def patch_user(user_id: int, user: UserCreate):
    """
    Patch a user with the provided data.
    """
    _user: UserRead = await User.get(id=user_id)
    if not _user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await _user.update(
        username=user.username,
        password=user.password,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    return {"message": "User updated successfully", "user": _user}


@router.delete(
    "/{user_id}",
    responses={404: {"description": "User not found"}},
)
async def delete_user(user_id: int):
    """
    Delete a user.
    """
    _user: UserRead = await User.get(id=user_id)
    if not _user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await _user.delete()
    return {"message": "User deleted successfully", "user": _user}


@router.post("/{user_id}/upload-avatar", response_model=dict)
async def upload_avatar(user_id: int, file: UploadFile = File(...)):
    """
    Endpoint to upload a user's avatar.
    """
    # Validate the file type (optional)
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG or PNG allowed.")

    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found.")

    # Save the file to a directory
    file_location = f"uploads/avatars/{user_id}_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Update the user's avatar field
    user.avatar = file_location
    await user.save()

    return {"message": "Avatar uploaded successfully", "avatar_url": file_location}
