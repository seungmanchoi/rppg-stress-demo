from fastapi import APIRouter

from app.core.config import settings
from app.models.registry import ALGORITHMS

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict:
    import torch

    loaded = [
        a.id
        for a in ALGORITHMS
        if a.weight_filename and (settings.weights_dir / a.weight_filename).exists()
    ]
    return {
        "status": "ok",
        "mpsAvailable": bool(torch.backends.mps.is_available()),
        "weightsLoaded": loaded,
        "totalAlgorithms": len(ALGORITHMS),
    }
