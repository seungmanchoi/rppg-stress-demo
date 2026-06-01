from dataclasses import dataclass

from app.pipeline.consensus import build_consensus


@dataclass
class _T:  # minimal stub for hrv/freq/baevsky records
    hr_bpm: float = 0.0
    rmssd_ms: float = 0.0
    lf_hf_ratio: float = 0.0
    si: float = 0.0


@dataclass
class _CompStub:
    score: float = 0.0


def _algo(aid, hr, rmssd, lfhf, si, comp, rel):
    return {
        "id": aid,
        "available": True,
        "hrv": _T(hr_bpm=hr, rmssd_ms=rmssd),
        "freq": _T(lf_hf_ratio=lfhf),
        "baevsky": _T(si=si),
        "composite": comp,
        "composite_v1": _CompStub(score=comp),
        "composite_v2": _CompStub(score=comp),
        "reliability": rel,
    }


def test_consensus_excludes_low_reliability():
    per_algo = [
        _algo("A", 70, 30, 1.5, 200, 40, 80),
        _algo("B", 72, 32, 1.6, 210, 42, 70),
        _algo("C", 120, 5, 8.0, 1200, 95, 20),  # rel=20 → excluded
    ]
    c = build_consensus(per_algo)
    assert c is not None
    assert 70 <= c["hr_bpm"] <= 72
    assert c["contributing_algorithms"] == 2
    assert c["stress_level"] in {"low", "mid"}


def test_consensus_none_when_all_unreliable():
    per_algo = [
        _algo("A", 70, 30, 1.5, 200, 40, 20),
        _algo("B", 72, 32, 1.6, 210, 42, 25),
    ]
    assert build_consensus(per_algo) is None


def test_consensus_handles_no_available():
    per_algo = [{"id": "A", "available": False, "error": "x", "compute_ms": 0}]
    assert build_consensus(per_algo) is None
