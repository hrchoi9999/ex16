from __future__ import annotations

import runpy
from pathlib import Path


LEGACY_STREAMLIT_APP = Path(__file__).resolve().parent / "legacy_streamlit" / "app.py"

runpy.run_path(str(LEGACY_STREAMLIT_APP), run_name="__main__")
