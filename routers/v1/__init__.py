from fastapi import APIRouter
from . import core, users, auth, geo, intents, assets

router = APIRouter()
router.include_router(core.router, tags=["Core"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(geo.router, prefix="/geo", tags=["Geo"])
router.include_router(intents.router, prefix="/intents", tags=["Intents"])
# router.include_router(assets.router, prefix="/assets", tags=["Assets"])
