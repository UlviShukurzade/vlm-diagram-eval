"""Quantification and modality-gap tests.

Three layers:

1. Parsing and the failed-prediction convention, on synthetic data.
2. Aggregation to thesis Table 5.13, from the committed per-prompt MAE values in
   ``tests/fixtures/quantification_reference.csv``.
3. Full reproduction from raw predictions -- skipped unless the inference parquets
   are present locally, since they are too large to commit.

Layer 2 runs everywhere, including CI. Layer 3 is the strongest check available to
anyone holding the dataset.
"""

import csv
import os
from pathlib import Path

import pytest

from vlm_diagram_eval.evaluators.quantification import (
    COMPONENT_KEYS,
    FAILED_PREDICTION,
    component_mae,
    find_prediction_column,
    modality_gap,
    parse_counts,
    parse_failure_rate,
)

REFERENCE = Path(__file__).parent / "fixtures" / "quantification_reference.csv"

# Thesis Table 5.13: component MAE by model and modality, averaged across prompts.
TABLE_5_13 = {
    ("gpt-4.1", "image2counts"): {"node": 1.898, "edge": 1.113, "decision": 0.498, "parent": 0.299},
    ("gpt-4.1", "mermaid2counts"): {"node": 1.489, "edge": 0.634, "decision": 0.594, "parent": 0.204},
    ("gpt-o4-mini", "image2counts"): {"node": 1.559, "edge": 0.712, "decision": 0.233, "parent": 0.247},
    ("gpt-o4-mini", "mermaid2counts"): {"node": 1.503, "edge": 0.594, "decision": 0.212, "parent": 0.284},
}

# Where the raw prediction parquets live, if available.
RAW_DIR = Path(
    os.environ.get(
        "QUANT_DATA_DIR",
        Path.home() / "Desktop/final thesis files/pictureRepresentation/inference_mermaid2counts",
    )
)


# ── 1. Parsing and conventions ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw",
    [
        '{"nodes_count": 5, "edges_count": 4, "nesting_count": 1, "branching_count": 2}',
        "{'nodes_count': 5, 'edges_count': 4, 'nesting_count': 1, 'branching_count': 2}",
        {"nodes_count": 5, "edges_count": 4, "nesting_count": 1, "branching_count": 2},
    ],
    ids=["json", "python-literal", "already-a-dict"],
)
def test_parses_every_response_shape(raw):
    assert parse_counts(raw)["nodes_count"] == 5


@pytest.mark.parametrize("raw", [None, "", "   ", "null", "NaN", "not json at all", 42, "{broken"])
def test_unparseable_responses_yield_all_none(raw):
    assert all(v is None for v in parse_counts(raw).values())


def test_partial_response_keeps_what_it_can():
    result = parse_counts('{"nodes_count": 7}')
    assert result["nodes_count"] == 7
    assert result["edges_count"] is None


def test_failed_predictions_score_as_zero_not_dropped():
    """The published numbers depend on this: a parse failure is maximally wrong.

    Dropping failed rows instead shifts MAE by up to 0.24 and stops Table 5.13
    reproducing, so the convention is pinned here deliberately.
    """
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame(
        {
            "node_count": [10, 20],
            "edge_count": [0, 0],
            "decision_count": [0, 0],
            "parent_count": [0, 0],
            "quantification_v1": ['{"nodes_count": 10, "edges_count": 0}', "garbage"],
        }
    )
    mae = component_mae(frame, "quantification_v1")
    # row 1 is exact (0 error); row 2 fails -> predicted 0 -> error is the full 20.
    assert mae["node_count"] == pytest.approx(10.0)  # (0 + 20) / 2, denominator keeps both rows
    assert FAILED_PREDICTION == 0.0


def test_parse_failure_rate_counts_only_total_failures():
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame({"quantification_v1": ['{"nodes_count": 1}', "garbage", None]})
    assert parse_failure_rate(frame, "quantification_v1") == pytest.approx(2 / 3)


def test_find_prediction_column():
    assert find_prediction_column(["code", "mermaid_4.1_quantification_v1"]) == "mermaid_4.1_quantification_v1"
    with pytest.raises(ValueError, match="no quantification column"):
        find_prediction_column(["code", "node_count"])


def test_modality_gap_is_image_minus_mermaid():
    image = dict.fromkeys(COMPONENT_KEYS, 1.5)
    mermaid = dict.fromkeys(COMPONENT_KEYS, 1.0)
    assert all(v == pytest.approx(0.5) for v in modality_gap(image, mermaid).values())


# ── 2. Reproduction of Table 5.13 ─────────────────────────────────────────────


def _reference_rows():
    if not REFERENCE.exists():
        pytest.skip("quantification_reference.csv not present")
    with REFERENCE.open() as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize(("model", "mode"), list(TABLE_5_13))
def test_reproduces_table_5_13(model, mode):
    """Averaging the per-prompt MAEs must give the published table."""
    rows = [r for r in _reference_rows() if r["model"] == model and r["mode"] == mode]
    assert len(rows) == 4, f"expected 4 prompt tiers, got {len(rows)}"

    for component, expected in TABLE_5_13[(model, mode)].items():
        values = [float(r[f"mae_{component}"]) for r in rows]
        got = sum(values) / len(values)
        # Agreement to the precision the thesis prints (3 dp), rather than exact
        # equality after rounding. One cell -- o4-mini/mermaid/decision -- is an
        # exact .2125 tie, so the printed digit depends on summation order and
        # rounding mode: numpy's pairwise mean gives 0.2125 and banker's rounding
        # prints 0.212, while a left-to-right sum gives 0.21250000000000002.
        assert abs(got - expected) <= 0.0005 + 1e-9, f"{model} {mode} {component}: got {got:.6f}, thesis {expected}"


def test_reproduces_published_modality_gaps():
    """Signs and magnitudes of delta_MAE, thesis section 5.3."""
    rows = _reference_rows()

    def mae(model, mode, component):
        vals = [float(r[f"mae_{component}"]) for r in rows if r["model"] == model and r["mode"] == mode]
        return sum(vals) / len(vals)

    # GPT-4.1: image is worse on nodes and edges, better on decisions.
    assert round(mae("gpt-4.1", "image2counts", "node") - mae("gpt-4.1", "mermaid2counts", "node"), 3) == 0.409
    assert round(mae("gpt-4.1", "image2counts", "edge") - mae("gpt-4.1", "mermaid2counts", "edge"), 3) == 0.479
    assert round(mae("gpt-4.1", "image2counts", "decision") - mae("gpt-4.1", "mermaid2counts", "decision"), 3) == -0.096
    # o4-mini: much smaller node/edge gaps.
    assert round(mae("gpt-o4-mini", "image2counts", "node") - mae("gpt-o4-mini", "mermaid2counts", "node"), 3) == 0.056
    assert round(mae("gpt-o4-mini", "image2counts", "edge") - mae("gpt-o4-mini", "mermaid2counts", "edge"), 3) == 0.118


def test_every_prompt_tier_is_present_for_both_modalities():
    rows = _reference_rows()
    for model in ("gpt-4.1", "gpt-o4-mini"):
        for mode in ("image2counts", "mermaid2counts"):
            tiers = {r["prompt"] for r in rows if r["model"] == model and r["mode"] == mode}
            assert tiers == {"v1", "v2", "v3", "v4"}, f"{model}/{mode} has {tiers}"


# ── 3. Full reproduction from raw predictions (needs the dataset) ─────────────


@pytest.mark.skipif(not RAW_DIR.exists(), reason="raw inference parquets not available")
def test_recomputes_per_prompt_mae_from_raw_predictions():
    """Recompute every per-prompt MAE from the model responses themselves."""
    pd = pytest.importorskip("pandas")
    from vlm_diagram_eval.evaluators.quantification import RESULT_FILENAME

    short = {"node_count": "node", "edge_count": "edge", "decision_count": "decision", "parent_count": "parent"}
    expected = {(r["model"], r["mode"], r["prompt"]): r for r in _reference_rows()}

    checked, mismatches = 0, []
    for path in sorted(RAW_DIR.glob("9*.parquet")):
        match = RESULT_FILENAME.match(path.name)
        if not match:
            continue
        key = (match.group("model"), match.group("mode").lower(), match.group("prompt").lower())
        if key not in expected:
            continue
        frame = pd.read_parquet(path)
        mae = component_mae(frame, find_prediction_column(frame.columns))
        for component, name in short.items():
            want = float(expected[key][f"mae_{name}"])
            if abs(mae[component] - want) > 1e-6:
                mismatches.append(f"{path.name} {component}: got {mae[component]:.6f}, published {want:.6f}")
        checked += 1

    assert checked == 16, f"expected 16 result files, processed {checked}"
    assert not mismatches, "MAE no longer reproduces published values:\n" + "\n".join(mismatches[:10])
