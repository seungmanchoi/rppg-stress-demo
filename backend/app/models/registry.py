from dataclasses import asdict, dataclass
from typing import Literal

WEIGHT_BASE = (
    "https://github.com/ubicomplab/rPPG-Toolbox/raw/main/final_model_release/"
)


@dataclass(frozen=True)
class AlgorithmMeta:
    id: str
    display_name: str
    short_description: str
    type: Literal["unsupervised", "supervised"]
    backbone: str
    pretrained_on: str | None = None
    model_size_mb: int | None = None
    weight_url: str | None = None
    weight_filename: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


ALGORITHMS: list[AlgorithmMeta] = [
    AlgorithmMeta(
        "POS", "POS",
        "RGB → 피부 톤 직교 평면 투영으로 혈류 분리 (de Haan 2014)",
        "unsupervised", "Signal processing",
    ),
    AlgorithmMeta(
        "CHROM", "CHROM",
        "피부 톤 표준화 후 색 차이 신호화 (de Haan 2013)",
        "unsupervised", "Signal processing",
    ),
    AlgorithmMeta(
        "OMIT", "OMIT",
        "Orthogonal Matrix Image Transformation, 조명 변화에 robust",
        "unsupervised", "Signal processing",
    ),
    AlgorithmMeta(
        "GREEN", "GREEN",
        "녹색 채널만으로 혈류 추출 — rPPG의 시초 (Verkruysse 2008)",
        "unsupervised", "Signal processing",
    ),
    AlgorithmMeta(
        "ICA", "ICA",
        "독립성분분석(ICA)으로 RGB에서 맥파 분리 (Poh 2010)",
        "unsupervised", "Signal processing",
    ),
    AlgorithmMeta(
        "TS-CAN", "TS-CAN",
        "2D-CNN + Temporal Shift Module, 모바일 실시간 친화",
        "supervised", "CNN+TSM",
        pretrained_on="UBFC-rPPG", model_size_mb=30,
        weight_url=WEIGHT_BASE + "UBFC-rPPG_TSCAN.pth",
        weight_filename="UBFC-rPPG_TSCAN.pth",
    ),
    AlgorithmMeta(
        "EfficientPhys", "EfficientPhys",
        "경량 CNN — 가장 빠른 supervised 모델",
        "supervised", "Light CNN",
        pretrained_on="UBFC-rPPG", model_size_mb=25,
        weight_url=WEIGHT_BASE + "UBFC-rPPG_EfficientPhys.pth",
        weight_filename="UBFC-rPPG_EfficientPhys.pth",
    ),
    AlgorithmMeta(
        "PhysFormer", "PhysFormer",
        "Video Transformer 기반 SOTA — 정확도 ↑",
        "supervised", "Transformer",
        pretrained_on="PURE", model_size_mb=200,
        weight_url=WEIGHT_BASE + "PURE_PhysFormer_DiffNormalized.pth",
        weight_filename="PURE_PhysFormer_DiffNormalized.pth",
    ),
    AlgorithmMeta(
        "RhythmFormer", "RhythmFormer",
        "Frequency-domain attention — HRV 안정성 ↑",
        "supervised", "Freq-attention",
        pretrained_on="PURE", model_size_mb=180,
        weight_url=WEIGHT_BASE + "PURE_RhythmFormer.pth",
        weight_filename="PURE_RhythmFormer.pth",
    ),
    AlgorithmMeta(
        "BigSmall", "BigSmall",
        "Multitask CNN — BVP + 호흡수 + AU 동시 추정 (BP4D 학습)",
        "supervised", "Multitask CNN",
        pretrained_on="BP4D", model_size_mb=80,
        weight_url=WEIGHT_BASE + "BP4D_BigSmall_Multitask_Fold1.pth",
        weight_filename="BP4D_BigSmall_Multitask_Fold1.pth",
    ),
    AlgorithmMeta(
        "PhysNet", "PhysNet",
        "3D-CNN encoder-decoder — 시공간 맥파 추출 (Yu 2019)",
        "supervised", "3D-CNN",
        pretrained_on="PURE", model_size_mb=3,
        weight_url=WEIGHT_BASE + "PURE_PhysNet_DiffNormalized.pth",
        weight_filename="PURE_PhysNet_DiffNormalized.pth",
    ),
    AlgorithmMeta(
        "DeepPhys", "DeepPhys",
        "Motion+Appearance 2-stream CNN — TS-CAN의 원조 (Chen 2018)",
        "supervised", "CNN+Attention",
        pretrained_on="UBFC-rPPG", model_size_mb=9,
        weight_url=WEIGHT_BASE + "UBFC-rPPG_DeepPhys.pth",
        weight_filename="UBFC-rPPG_DeepPhys.pth",
    ),
]

_META_BY_ID = {m.id: m for m in ALGORITHMS}


def get_meta(algo_id: str) -> AlgorithmMeta:
    return _META_BY_ID[algo_id]


def all_ids() -> list[str]:
    return [m.id for m in ALGORITHMS]
