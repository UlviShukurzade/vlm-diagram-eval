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
    import pandas as pd

    records = []
    for path in sorted(data_dir.glob("*.parquet")):
        match = RESULT_FILENAME.match(path.name)
        if not match:
            continue
        frame = pd.read_parquet(path)
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
    return pd.DataFrame(records)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--by-prompt", action="store_true", help="show each prompt tier instead of averaging")
    ap.add_argument("--csv", type=Path, help="also write the per-file table here")
    args = ap.parse_args()

    df = collect(args.data_dir)
    components = [SHORT[k] for k in COMPONENT_KEYS]

    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"wrote {args.csv}\n")

    if args.by_prompt:
        print("Per-prompt MAE")
        print(df.sort_values(["model", "mode", "prompt"]).to_string(index=False))
        print()

    print("Component MAE by model and modality (averaged across prompt tiers)")
    table = df.groupby(["model", "mode"])[components].mean()
    print(table.round(3).to_string())
    print()

    print("Modality gap  delta = MAE_image - MAE_mermaid  (positive: image worse)")
    gap = (table.xs("image2counts", level="mode") - table.xs("mermaid2counts", level="mode")).round(3)
    print(gap.to_string())


if __name__ == "__main__":
    main()
