"""
Root pytest conftest.

Ensures the project root is importable as `rag.*` / `agents.*` regardless
of which directory pytest is invoked from, and points test runs at an
isolated log directory so they don't pollute the real logs/ folder.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LOG_DIR", str(ROOT / "logs" / "test"))
os.environ.setdefault("VECTOR_DB_DIR", str(ROOT / "rag" / "vectordb" / "test_store"))
