from typing import Optional

from pydantic import BaseModel, Field


class AuthenticationSchema(BaseModel):
    email: str
    password: str


class AuthenticationTokenSchema(BaseModel):
    token: str


class SessionCreateSchema(BaseModel):
    """Schema for creating a session without a user."""

    ip_v4: Optional[str] = Field(None, description="IPv4 address")
    ip_v6: Optional[str] = Field(None, description="IPv6 address")

    token: Optional[str] = Field(None, description="Token")

    class Config:
        from_attributes = True
