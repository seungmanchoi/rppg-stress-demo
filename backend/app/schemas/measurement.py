from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(w.title() for w in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)


class HRVMetrics(CamelModel):
    hr_bpm: float
    ibi_mean_ms: float
    sdnn_ms: float
    rmssd_ms: float
    pnn50_pct: float
    lf_power: float
    hf_power: float
    lf_hf_ratio: float
    sd1: float
    sd2: float


class StressIndices(CamelModel):
    baevsky_si: float
    baevsky_level: Literal["normal", "mild", "moderate", "high"]
    lf_hf_stress: float = 0.0
    composite_score: float
    composite_level: Literal["low", "mid", "high", "very_high"]


class ReliabilityComponents(CamelModel):
    snr_db: float
    face_tracking_pct: float
    deviation_from_consensus: float
    motion_penalty: float


class Reliability(CamelModel):
    score: float
    grade: Literal["low", "medium", "high"]
    components: ReliabilityComponents


class AlgorithmMetaOut(CamelModel):
    id: str
    display_name: str
    short_description: str
    type: Literal["unsupervised", "supervised"]
    backbone: str
    pretrained_on: str | None = None
    model_size_mb: int | None = None


class AlgorithmResult(CamelModel):
    meta: AlgorithmMetaOut
    available: bool
    error: str | None = None
    hrv: HRVMetrics | None = None
    stress: StressIndices | None = None
    reliability: Reliability | None = None
    bvp_sparkline: list[float] = Field(default_factory=list)
    extras: dict | None = None
    compute_ms: float


class ConsensusResult(CamelModel):
    stress_score: float
    stress_level: Literal["low", "mid", "high", "very_high"]
    hr_bpm: float
    rmssd_ms: float
    lf_hf_ratio: float
    baevsky_si: float
    reliability: Reliability
    contributing_algorithms: int


class VideoMeta(CamelModel):
    duration_s: float
    fps: float
    resolution: list[int]


class TimingInfo(CamelModel):
    total_ms: float
    decode_ms: float
    face_roi_ms: float
    quality_ms: float
    video_duration_s: float


class MeasurementResponse(CamelModel):
    job_id: str
    status: Literal["queued", "processing", "done", "failed"]
    progress: float
    stage: str = ""
    video_meta: VideoMeta | None = None
    timing: TimingInfo | None = None
    consensus: ConsensusResult | None = None
    algorithms: list[AlgorithmResult] | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    disclaimer: str = "Not a medical device. Educational / research use only."
