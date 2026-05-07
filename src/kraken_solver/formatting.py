"""Output formatting helpers for KRAKEN solver benchmark integration."""

from pydantic import BaseModel


def format_output_for_benchmark(synthesis_report: str, hypotheses: list) -> str:
    """Convert KRAKEN's structured output into text for benchmark scoring.

    Renders the synthesis report followed by a numbered list of hypotheses.
    This format is intentionally simple and may be revised when custom
    scorers are built in Phase 4.
    """
    parts = []

    if synthesis_report:
        parts.append(synthesis_report)

    if hypotheses:
        parts.append("")  # blank line separator
        parts.append("## Hypotheses")
        for i, h in enumerate(hypotheses, 1):
            title = getattr(h, "title", str(h))
            claim = getattr(h, "claim", "")
            tier = getattr(h, "tier", "?")
            parts.append(f"\n### {i}. {title} (Tier {tier})")
            if claim:
                parts.append(claim)

    return "\n".join(parts)


def serialize_kraken_state(final_state: dict) -> dict:
    """Serialize DiscoveryState dict for metadata attachment.

    Walks the state dict and calls .model_dump() on any Pydantic BaseModel
    instances. Handles nested lists and dicts recursively.
    """
    return _serialize_value(final_state)


def _serialize_value(value):
    """Recursively serialize a value, converting Pydantic models to dicts."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode='json')
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    elif isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    return value
