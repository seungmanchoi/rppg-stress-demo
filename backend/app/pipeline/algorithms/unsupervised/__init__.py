import sys
from pathlib import Path

_TOOLBOX_ROOT = Path(__file__).resolve().parents[4] / "rppg_toolbox"
if str(_TOOLBOX_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLBOX_ROOT))
