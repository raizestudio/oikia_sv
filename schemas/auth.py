from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from schemas.users import UserRead


class AuthenticationSchema(BaseModel):
    email: str
    password: str


class AuthenticationTokenSchema(BaseModel):
    token: str = Field(..., description="The authentication token")
    refresh: str = Field(..., description="The refresh token")

    user: UserRead = Field(..., description="The user associated with the token")


class SessionCreateSchema(BaseModel):
    """Schema for creating a session without a user."""

    ip_v4: Optional[str] = Field(None, description="IPv4 address")
    ip_v6: Optional[str] = Field(None, description="IPv6 address")

    token: Optional[str] = Field(None, description="Token")

    class Config:
        from_attributes = True


class TokenRead(BaseModel):
    """Schema for reading a token."""

    token: str = Field(..., description="The authentication token")
    created_at: datetime = Field(..., description="Creation date of the token")

    user: UUID = Field(..., alias="user__id", description="Id of the user associated with the token")

    class Config:
        from_attributes = True
        orm_mode = True


class TokenAuthenticate(BaseModel):
    """Schema for authenticating a token."""

    token: str = Field(..., description="The authentication token")

    class Config:
        from_attributes = True
        orm_mode = True


class RefreshRead(BaseModel):
    """Schema for reading a token."""

    token: str = Field(..., description="The authentication token")
    created_at: datetime = Field(..., description="Creation date of the token")
    expire_at: datetime = Field(..., description="Expiration date of the token")

    user: UUID = Field(..., alias="user__id", description="Id of the user associated with the token")

    class Config:
        from_attributes = True
        orm_mode = True


class SessionRead(BaseModel):
    """Schema for reading a session."""

    id: UUID = Field(..., description="ID of the session")
    ip_v4: Optional[str] = Field(None, description="IPv4 address")
    ip_v6: Optional[str] = Field(None, description="IPv6 address")
    ip_type: str = Field(..., description="Type of the IP address (e.g., IPv4, IPv6)")
    ip_class: str = Field(..., description="Class of the IP address (e.g., public, private)")
    isp: Optional[str] = Field(None, description="Internet Service Provider")
    os: Optional[str] = Field(None, description="Operating System")
    user_agent: Optional[str] = Field(None, description="User agent string of the client")
    created_at: datetime = Field(..., description="Creation date of the session")
    updated_at: datetime = Field(..., description="Last update date of the session")

    user: UUID = Field(..., alias="user__id", description="Id of the user associated with the session")

    class Config:
        from_attributes = True
        orm_mode = True
