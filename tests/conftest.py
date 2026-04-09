from __future__ import annotations

import sys
import types
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")

    class OpenAI:  # pragma: no cover - test bootstrap shim
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

    openai_stub.OpenAI = OpenAI
    sys.modules["openai"] = openai_stub
