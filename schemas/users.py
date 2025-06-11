import uuid
from datetime import datetime
from typing import Optional, Union

from fastapi import Request
from pydantic import BaseModel, computed_field
from pydantic.fields import Field
from pydantic.networks import EmailStr


class UserRead(BaseModel):
    """Schema that defines the structure of the User model read."""

    id: uuid.UUID = Field(..., description="Unique identifier of the user")
    username: str = Field(..., min_length=3, max_length=50, description="Username of the user")
    # password: str = Field(..., min_length=6, description="Password for the user")
    # password2: str = Field(None, min_length=6, description="Password for the user")
    first_name: str = Field(None, max_length=30, description="First name of the user")
    last_name: str = Field(None, max_length=30, description="Last name of the user")
    is_active: bool = Field(default=True, description="Status of the user account")
    avatar: str | None = Field(None, max_length=255, description="Avatar of the user")
    created_at: Optional[datetime] = Field(None, description="Creation date of the user")
    updated_at: Optional[datetime] = Field(None, description="Last update date of the user")
    is_admin: bool = Field(default=False, description="Is the user an admin")
    is_superuser: bool = Field(default=False, description="Is the user a superuser")

    email: Union[str, None] = Field(None, alias="email__email", description="Email address of the user")
    phone_number: Union[str, None] = Field(None, alias="phone_number__phone_number", description="Phone number of the user")
    calling_code: Union[str, None] = Field(None, alias="phone_number__calling_code__code", description="Phone number of the user")

    @computed_field
    def full_phone_number(self) -> Optional[str]:
        if self.calling_code and self.phone_number:
            code = self.calling_code.replace("00", "+", 1) if self.calling_code.startswith("00") else self.calling_code
            phone_number = self.phone_number.replace("0", "") if self.phone_number.startswith("0") else self.phone_number
            return f"{code}{phone_number}"
        return None

    @computed_field
    def role(self) -> str:
        if self.is_superuser:
            return "superuser"
        if self.is_admin:
            return "admin"
        return "user"

    class Config:
        populate_by_name = True
        from_attributes = True

    @classmethod
    def from_orm_with_request(cls, user, request: Request):
        avatar_url = request.url_for("static", path=user.avatar) if user.avatar else None
        return cls(
            **user.__dict__,
            avatar=str(avatar_url) if avatar_url else None,
        )


class UserCreate(BaseModel):
    """Schema that defines the structure of the User model create."""

    username: str = Field(..., min_length=3, max_length=50, description="Username of the user")
    password: str = Field(..., min_length=6, description="Password for the user")
    email: EmailStr = Field(..., description="Valid email address of the user")
    first_name: Optional[str] = Field(None, max_length=30, description="First name of the user")
    last_name: Optional[str] = Field(None, max_length=30, description="Last name of the user")
    is_active: bool = Field(default=True, description="Status of the user account")

    class Config:
        from_attributes = True
