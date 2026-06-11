import os

# Apple MPS lacks kernels for some 3D ops (e.g. adaptive_avg_pool3d used by
# PhysNet's 3D-CNN); without this they raise NotImplementedError and the model
# is dropped. Falling those ops back to CPU keeps PhysNet alive. Must be set
# before torch is imported anywhere. No effect on CUDA / CPU-only machines.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import logging  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.v1 import algorithms, health, measurements  # noqa: E402
from app.core.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="rPPG Stress Demo API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(measurements.router, prefix="/api/v1")
app.include_router(algorithms.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    return {"name": "rPPG Stress Demo API", "version": "0.1.0", "docs": "/docs"}
