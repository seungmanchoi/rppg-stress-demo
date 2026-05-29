from fastapi import APIRouter

from app.models.registry import ALGORITHMS
from app.schemas.algorithm import AlgorithmMetaOut

router = APIRouter(prefix="/algorithms", tags=["algorithms"])


@router.get("", response_model=list[AlgorithmMetaOut], response_model_by_alias=True)
async def list_algorithms() -> list[AlgorithmMetaOut]:
    return [AlgorithmMetaOut(**m.to_dict()) for m in ALGORITHMS]
