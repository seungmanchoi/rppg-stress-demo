import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import algorithms, health, measurements
from app.core.config import settings

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
