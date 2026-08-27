"""Guards that diagram sources are never modified.

Mermaid is whitespace-sensitive: indentation defines subgraph nesting, and a
stripped blank line inside a block can change how the diagram parses. A formatter
or an editor's save-on-trim can therefore silently alter results long after the
fact, with no visible diff in a rendered view.

These tests make that failure loud. The checksums below were recorded when the
fixtures were harvested. If one changes, a diagram was edited -- investigate
rather than updating the constant.
"""

import hashlib
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.diagrams import ALL_DIAGRAMS

REPO_ROOT = Path(__file__).resolve().parents[1]

# sha256 of each harvested diagram, recorded at import time from the originals.
EXPECTED_DIGESTS = {
    "state_diagram": "c5b5615ce7b3e914",
    "mermaid": "304d50183dda6803",
    "minimal": "6e5dfb3f70f10e69",
    "nested_layers": "60484298ae9807e9",
    "mermaid_class_diagram": "837ba6879b861ed2",
    "mermaid_yes_no": "2f1a3ee8ff03f790",
    "flowchart_49441_65": "c6897c3e52d60160",
    "flowchart_49441_65_gen": "1240731b9a4aa355",
}


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


@pytest.mark.parametrize("name", sorted(EXPECTED_DIGESTS))
def test_harvested_diagram_is_unmodified(name):
    assert name in ALL_DIAGRAMS, f"fixture {name!r} disappeared"
    assert _digest(ALL_DIAGRAMS[name]) == EXPECTED_DIGESTS[name], (
        f"Diagram {name!r} changed. Mermaid is whitespace-sensitive, so this may "
        f"alter parse results. Do not update the expected digest without checking "
        f"what edited it -- a formatter or trailing-whitespace hook is the usual cause."
    )


def test_no_diagram_was_dropped_or_added():
    assert set(ALL_DIAGRAMS) == set(EXPECTED_DIGESTS)


def test_sample_mmd_files_match_recorded_checksums():
    """`.mmd` files under data/sample/ must be byte-identical to what was copied in."""
    checksums = REPO_ROOT / ".mmd-checksums.txt"
    if not checksums.exists():
        pytest.skip(".mmd-checksums.txt not present")

    result = subprocess.run(  # noqa: S603
        ["/usr/bin/shasum", "-a", "256", "-c", str(checksums)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    failed = [line for line in result.stdout.splitlines() if "FAILED" in line]
    assert not failed, "sample diagrams were modified:\n" + "\n".join(failed)
    assert result.returncode == 0, result.stderr


# ── Prompt templates ──────────────────────────────────────────────────────────
# Prompt text is experimental data: the exact strings produced the thesis results,
# down to trailing whitespace inside the templates. ruff and pre-commit are
# configured to skip this file; these digests catch anything that slips past.

PROMPT_DIGESTS = {
    "base_system": "ca123e0a936abf9f",
    "base_user": "f4197acbfdacf615",
    "mermaid_quant_v1_base_system": "a628b3af45604b63",
    "mermaid_quant_v1_base_user": "407eb5cb27a9a12f",
    "mermaid_quant_v2_syntactic_system": "67863e1310f03519",
    "mermaid_quant_v2_syntactic_user": "701fe455526fb969",
    "mermaid_quant_v3_few_shot_system": "efca09de704bc7c8",
    "mermaid_quant_v3_few_shot_user": "d376971791b12961",
    "mermaid_quant_v4_self_correction_system": "f47affb0da4f1b5a",
    "mermaid_quant_v4_self_correction_user": "1c3058ff76346b49",
    "quant_v1_base_system": "e30775d8c3375596",
    "quant_v1_base_user": "d8294fe408f11547",
    "quant_v2_syntactic_guardrail_system": "9540b3660a876fbe",
    "quant_v2_syntactic_guardrail_user": "e71cac1920b37951",
    "quant_v3_few_shot_system": "e0a7e8287e4a2b11",
    "quant_v3_few_shot_user": "437e59276d155a30",
    "quant_v4_self_correction_system": "31e5aa0081c25646",
    "quant_v4_self_correction_user": "27f4b7644c98099a",
    "v1_syntactic_guardrail_system": "6341a41befc6fc1a",
    "v1_syntactic_guardrail_user": "3b89477dfb16db14",
    "v2_few_shot_system": "305a08d669b2d03a",
    "v2_few_shot_user": "d14b1daa89d85800",
    "v3_self_correction_system": "b15bb58fd94443d1",
    "v3_self_correction_user": "49e46e8e46b2c859",
}


@pytest.mark.parametrize("name", sorted(PROMPT_DIGESTS))
def test_prompt_template_is_unmodified(name):
    from vlm_diagram_eval.llm import prompts

    value = getattr(prompts, name, None)
    assert value is not None, f"prompt {name!r} disappeared"
    assert _digest(value) == PROMPT_DIGESTS[name], (
        f"Prompt {name!r} changed. These strings are the experimental condition -- "
        f"altering one invalidates comparison with the thesis results."
    )


def test_all_four_tiers_present_for_each_task():
    """Four tiers per task: baseline plus guardrails, few-shot, self-correction."""
    from vlm_diagram_eval.llm import prompts

    names = {n for n in dir(prompts) if not n.startswith("_")}
    families = {
        "image->mermaid": [n for n in names if not n.startswith(("quant_", "mermaid_quant_"))],
        "image->counts": [n for n in names if n.startswith("quant_")],
        "mermaid->counts": [n for n in names if n.startswith("mermaid_quant_")],
    }
    for family, members in families.items():
        tiers = {m.removesuffix("_system").removesuffix("_user") for m in members}
        assert len(tiers) == 4, f"{family} has {len(tiers)} tiers, expected 4: {sorted(tiers)}"
        for tier in tiers:
            assert f"{tier}_system" in names, f"{tier} missing a system prompt"
            assert f"{tier}_user" in names, f"{tier} missing a user prompt"
