from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    """Schema for creating an asset."""

    area: float = Field(..., description="Area of the asset.")
    total_rooms: int = Field(..., description="Total number of rooms in the asset.")
    latitude: str = Field(..., description="Latitude of the asset.")
    longitude: str = Field(..., description="Longitude of the asset.")

    asset_type: str = Field(..., description="Type of the asset.")
    address: int = Field(..., description="Address of the asset.")
