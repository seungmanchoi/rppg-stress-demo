"""Download pre-trained rPPG-Toolbox model weights into backend/weights/."""
from __future__ import annotations

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.models.registry import ALGORITHMS  # noqa: E402


def main() -> int:
    failed: list[str] = []
    for a in ALGORITHMS:
        if not a.weight_url or not a.weight_filename:
            continue
        target = settings.weights_dir / a.weight_filename
        if target.exists() and target.stat().st_size > 1_000_000:
            print(f"  ✓ {a.id:<14}  already present ({target.stat().st_size // 1024 // 1024} MB)")
            continue
        print(f"  ↓ {a.id:<14}  {a.weight_url}")
        try:
            with httpx.stream("GET", a.weight_url, follow_redirects=True, timeout=300.0) as r:
                r.raise_for_status()
                tmp = target.with_suffix(target.suffix + ".tmp")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=1 << 16):
                        f.write(chunk)
                tmp.rename(target)
            size_mb = target.stat().st_size // 1024 // 1024
            print(f"    saved {size_mb} MB")
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED: {e}")
            failed.append(a.id)
    if failed:
        print(f"\n  Failed: {', '.join(failed)}")
        return 1
    print("\n  All weights ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
