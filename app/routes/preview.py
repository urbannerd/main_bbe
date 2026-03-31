from fastapi import APIRouter
from app.services.home_preview import build_home_preview, build_impulse_snapshot

router = APIRouter()


@router.get("/home-preview")
def home_preview():
    return build_home_preview()


@router.get("/impulse-snapshot")
def impulse_snapshot():
    return build_impulse_snapshot()