from __future__ import annotations

import sys
from pathlib import Path


SPIKE_BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend" / "src"
if str(SPIKE_BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(SPIKE_BACKEND_SRC))
