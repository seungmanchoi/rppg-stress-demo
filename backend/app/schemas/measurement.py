from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(w.title() for w in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)


class HRVMetrics(CamelModel):
    # Time-domain (ESC/NASPE 1996)
    hr_bpm: float
    ibi_mean_ms: float
    sdnn_ms: float
    rmssd_ms: float
    sdsd_ms: float
    pnn50_pct: float
    pnn20_pct: float
    cvnn_pct: float
    hrv_triangular_index: float
    # Frequency-domain
    vlf_power: float
    lf_power: float
    hf_power: float
    total_power: float
    lf_hf_ratio: float
    lf_nu: float
    hf_nu: float
    # Non-linear
    sd1: float
    sd2: float
    sd_ratio: float
    ellipse_area: float
    sample_entropy: float
    approximate_entropy: float
    shannon_entropy: float
    dfa_alpha1: float
    higuchi_fd: float


class StressComponent(CamelModel):
    name: str
    label: str
    weight: float
    raw_value: float
    raw_unit: str
    normalized: float
    contribution: float
    tier: Literal["clinical", "commercial", "research", "experimental", "rgbEstimated"]


class CompositeBreakdown(CamelModel):
    score: float
    level: Literal["low", "mid", "high", "very_high"]
    components: list[StressComponent] = Field(default_factory=list)


class StressIndices(CamelModel):
    # Baevsky (Russia)
    baevsky_si: float
    baevsky_level: Literal["normal", "mild", "moderate", "high"]
    baevsky_mo_s: float = 0.0
    baevsky_amo_pct: float = 0.0
    baevsky_mxdmn_s: float = 0.0
    # Composite v1 (this demo, 3-metric classical)
    lf_hf_stress: float = 0.0
    composite_score: float
    composite_level: Literal["low", "mid", "high", "very_high"]
    composite_v1: CompositeBreakdown | None = None
    # Composite v2 (extended autonomic balance ensemble — 9 metrics)
    composite_score_v2: float = 0.0
    composite_level_v2: Literal["low", "mid", "high", "very_high"] = "low"
    composite_v2: CompositeBreakdown | None = None
    # Kubios-style autonomic balance (-2..+2)
    pns_index: float = 0.0
    sns_index: float = 0.0
    # HeartMath emWave (0..3)
    coherence_score: float = 0.0
    coherence_peak_hz: float = 0.0


class HemodynamicMetrics(CamelModel):
    """Experimental, RGB-only estimates. Accuracy limited vs medical devices."""
    spo2_pct: float = 0.0
    spo2_confidence: float = 0.0
    pulse_rise_time_ms: float = 0.0


class RespirationMetrics(CamelModel):
    rate_rpm: float = 0.0
    confidence: float = 0.0


class SignalQuality(CamelModel):
    pqi: float = 0.0
    spectral_entropy: float = 0.0


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
    respiration: RespirationMetrics | None = None
    hemodynamic: HemodynamicMetrics | None = None
    signal_quality: SignalQuality | None = None
    beat_count: int | None = None
    bvp_sparkline: list[float] = Field(default_factory=list)
    extras: dict | None = None
    compute_ms: float


class ConsensusResult(CamelModel):
    stress_score: float
    stress_level: Literal["low", "mid", "high", "very_high"]
    stress_score_v2: float = 0.0
    stress_level_v2: Literal["low", "mid", "high", "very_high"] = "low"
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
