from __future__ import annotations

import json
from typing import Any


def parse_json(raw_text: str) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return None
