"""Component quantification and modality gap (thesis sections 5.2 and 5.3).

The reconstruction task asks a model to redraw a diagram; the quantification task
asks it only to *count* — how many nodes, edges, branches and containers. Running
that from an image and again from Mermaid source isolates how much is lost to
vision, which is the modality gap of RQ3:

    delta_MAE = MAE_image - MAE_mermaid

Positive means image-based inference is worse.

Models answer with a JSON object whose keys do not match the ground-truth column
names, and two of them read across rather than straight down:

    ground truth      model key           what it counts
    node_count        nodes_count         entities
    edge_count        edges_count         connections
    decision_count    branching_count     nodes with >1 outgoing edge
    parent_count      nesting_count       subgraph containers

Failed predictions count as zero
--------------------------------
When a model returns unparseable output, the prediction is treated as **0** — so
the absolute error becomes the full ground-truth count — and the row stays in the
denominator. Parse failure is scored as maximally wrong rather than excluded.

This is not stated in the thesis, but it is what produced the published numbers:
it is the only convention that reproduces Table 5.13 exactly, and dropping failed
rows instead shifts MAE by up to 0.24. ``tests/test_quantification.py`` pins it.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

# Ground-truth column -> key the model is asked to return.
COMPONENT_KEYS: dict[str, str] = {
    "node_count": "nodes_count",
    "edge_count": "edges_count",
    "decision_count": "branching_count",
    "parent_count": "nesting_count",
}

# 900_<mode>_prompt_<vN>_<model>.parquet
RESULT_FILENAME = re.compile(
    r"\d+_(?P<mode>image2counts|mermaid2counts)_prompt_(?P<prompt>v\d+)_(?P<model>.+)\.parquet$",
    re.IGNORECASE,
)

FAILED_PREDICTION = 0.0


def parse_counts(raw: Any) -> dict[str, int | None]:
    """Parse one model response into component counts.

    Responses arrive as JSON, as a Python-literal dict with single quotes, as an
    already-decoded dict, or as junk. Anything unrecognised yields all-None, which
    callers convert to :data:`FAILED_PREDICTION`.

    Args:
        raw: The model's raw response.

    Returns:
        A dict keyed by the model's own names (``nodes_count`` ...), values int or None.
    """
    blank: dict[str, int | None] = dict.fromkeys(COMPONENT_KEYS.values())

    if isinstance(raw, dict):
        return {**blank, **raw}
    if not isinstance(raw, str):
        return blank

    text = raw.strip()
    if not text or text.lower() in {"none", "null", "nan"}:
        return blank

    for loader in (json.loads, ast.literal_eval):
        try:
            value = loader(text)
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, dict):
            return {**blank, **value}
    return blank


def _to_count(value: Any) -> float:
    """Coerce one predicted count to a number, mapping anything unusable to zero."""
    try:
        if value is None:
            return FAILED_PREDICTION
        return float(value)
    except (TypeError, ValueError):
        return FAILED_PREDICTION


def absolute_errors(predictions, truth, component: str) -> list[float]:
    """Per-row absolute error for one component, scoring failures as zero.

    Args:
        predictions: Parsed responses (an iterable of dicts from :func:`parse_counts`).
        truth: Ground-truth counts, aligned with ``predictions``.
        component: A key of :data:`COMPONENT_KEYS`.

    Returns:
        Absolute errors, one per row, with no missing values.
    """
    key = COMPONENT_KEYS[component]
    return [abs(_to_count(p.get(key)) - float(t)) for p, t in zip(predictions, truth, strict=True)]


def component_mae(frame, prediction_column: str) -> dict[str, float]:
    """Mean absolute error per component for one result file.

    Args:
        frame: A polars (or pandas) DataFrame with the four ground-truth count
            columns and the model's response column.
        prediction_column: Name of the response column (contains "quantification").

    Returns:
        ``{component: mae}`` for all four components.
    """
    predictions = [parse_counts(v) for v in frame[prediction_column]]
    result = {}
    for component in COMPONENT_KEYS:
        errors = absolute_errors(predictions, frame[component], component)
        result[component] = sum(errors) / len(errors) if errors else 0.0
    return result


def parse_failure_rate(frame, prediction_column: str) -> float:
    """Fraction of responses that could not be parsed at all."""
    parsed = [parse_counts(v) for v in frame[prediction_column]]
    failed = sum(1 for p in parsed if all(v is None for v in p.values()))
    return failed / len(parsed) if parsed else 0.0


def find_prediction_column(columns) -> str:
    """Locate the model-response column, which always contains "quantification"."""
    matches = [c for c in columns if "quantification" in c.lower()]
    if not matches:
        raise ValueError(f"no quantification column found in {list(columns)}")
    if len(matches) > 1:
        raise ValueError(f"ambiguous quantification columns: {matches}")
    return matches[0]


def modality_gap(image_mae: dict[str, float], mermaid_mae: dict[str, float]) -> dict[str, float]:
    """delta_MAE = MAE_image - MAE_mermaid, per component.

    Positive values mean image-based inference carries more error, which is the
    modality gap RQ3 asks about.
    """
    return {c: image_mae[c] - mermaid_mae[c] for c in COMPONENT_KEYS}
