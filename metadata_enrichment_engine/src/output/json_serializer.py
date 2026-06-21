"""Serialize enriched metadata models to JSON-compatible dicts."""

from __future__ import annotations

import json
from typing import Any

from src.models.metadata import EnrichedOutput


def to_json_dict(output: EnrichedOutput) -> dict[str, Any]:
    """Convert an EnrichedOutput model to a plain dictionary."""
    return output.model_dump(mode="json", exclude_none=True)


def to_json_str(output: EnrichedOutput, indent: int = 2) -> str:
    """Convert an EnrichedOutput model to a JSON string."""
    return json.dumps(
        to_json_dict(output),
        indent=indent,
        ensure_ascii=False,
    )
