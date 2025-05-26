from fastapi import APIRouter

from models.assets import Asset, AssetType
from models.geo import Address
from schemas.assets import AssetCreate

router = APIRouter()


@router.get("/types")
async def get_asset_types():
    _asset_types = await AssetType.all()
    return _asset_types


@router.get("/")
async def get_assets():
    _assets = await Asset.all()
    return _assets


@router.get("/{asset}")
async def get_asset(asset: str):
    _asset = await Asset.get(id=asset)
    return _asset


@router.post("/")
async def create_asset(asset: AssetCreate):
    _asset_type = await AssetType.get(code=asset.asset_type)
    _address = await Address.get(id=asset.address)
    _asset = await Asset.create(
        area=asset.area,
        total_rooms=asset.total_rooms,
        latitude=asset.latitude,
        longitude=asset.longitude,
        asset_type=_asset_type,
        address=_address,
    )
    return _asset
