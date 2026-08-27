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
