from pydantic import BaseModel, Field


class IntentCreate(BaseModel):
    """Schema for creating an intent."""

    raw_input: str = Field(..., description="Raw input of the intent.")
