from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RPPG_")

    project_root: Path = Path(__file__).resolve().parent.parent.parent
    weights_dir: Path = project_root / "weights"
    tmp_dir: Path = Path("/tmp/rppg_measurements")
    max_video_mb: int = 200
    min_video_seconds: float = 10.0
    max_video_seconds: float = 120.0
    target_fps: int = 30
    job_ttl_seconds: int = 3600
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
settings.weights_dir.mkdir(parents=True, exist_ok=True)
settings.tmp_dir.mkdir(parents=True, exist_ok=True)
