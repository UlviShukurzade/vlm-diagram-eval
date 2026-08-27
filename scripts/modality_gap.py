"""Compute component MAE and the modality gap (thesis sections 5.2 and 5.3).

Reads the quantification result parquets -- one per (modality, prompt tier,
model) -- and reports mean absolute error per component, then the gap between
image-based and Mermaid-based inference:

    delta_MAE = MAE_image - MAE_mermaid

Positive means vision costs accuracy.

Usage::

    python scripts/modality_gap.py --data-dir path/to/inference_mermaid2counts
    python scripts/modality_gap.py --data-dir ... --by-prompt
    python scripts/modality_gap.py --data-dir ... --csv out.csv

Expects files named ``900_<image2counts|mermaid2counts>_prompt_<vN>_<model>.parquet``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vlm_diagram_eval.evaluators.quantification import (
    COMPONENT_KEYS,
    RESULT_FILENAME,
    component_mae,
    find_prediction_column,
    parse_failure_rate,
)

SHORT = {"node_count": "node", "edge_count": "edge", "decision_count": "decision", "parent_count": "parent"}


def collect(data_dir: Path):
    """Per-file MAE for every result parquet in ``data_dir``."""
    import polars as pl

    records = []
    for path in sorted(data_dir.glob("*.parquet")):
        match = RESULT_FILENAME.match(path.name)
        if not match:
            continue
        frame = pl.read_parquet(path)
        column = find_prediction_column(frame.columns)
        record = {
            "model": match.group("model"),
            "mode": match.group("mode").lower(),
            "prompt": match.group("prompt").lower(),
            "n": len(frame),
            "parse_fail_rate": parse_failure_rate(frame, column),
        }
        record.update({SHORT[k]: v for k, v in component_mae(frame, column).items()})
        records.append(record)

    if not records:
        sys.exit(f"no result parquets matched in {data_dir}")
    return pl.DataFrame(records)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--by-prompt", action="store_true", help="show each prompt tier instead of averaging")
    ap.add_argument("--csv", type=Path, help="also write the per-file table here")
    args = ap.parse_args()

    df = collect(args.data_dir)
    components = [SHORT[k] for k in COMPONENT_KEYS]

    if args.csv:
        df.write_csv(args.csv)
        print(f"wrote {args.csv}\n")

    import polars as pl

    if args.by_prompt:
        print("Per-prompt MAE")
        print(df.sort("model", "mode", "prompt"))
        print()

    # Round only for display; the gap is computed from full-precision means so it
    # does not inherit rounding from the table above.
    table = df.group_by("model", "mode").agg([pl.col(c).mean().alias(c) for c in components]).sort("model", "mode")
    print("Component MAE by model and modality (averaged across prompt tiers)")
    print(table.with_columns([pl.col(c).round(3) for c in components]))
    print()

    image = table.filter(pl.col("mode") == "image2counts").drop("mode")
    mermaid = table.filter(pl.col("mode") == "mermaid2counts").drop("mode")
    gap = image.join(mermaid, on="model", suffix="_merm").select(
        ["model", *[(pl.col(c) - pl.col(f"{c}_merm")).round(3).alias(c) for c in components]]
    )
    print("Modality gap  delta = MAE_image - MAE_mermaid  (positive: image worse)")
    print(gap)


if __name__ == "__main__":
    main()
