"""Fetch the full diagram dataset.

The repository ships only ``data/sample/`` (24 diagrams) so tests and the
quickstart run without a download. The complete dataset -- roughly 14,500 Mermaid
sources and 27,600 renders -- is too large for git and is hosted separately.

The host is not chosen yet. Once it is, implement ``download()`` below and record
the archive checksum so downloads are verifiable.
"""

from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
DATASET_URL: str | None = None  # TODO: set once the dataset is published


def download(destination: Path = DATA_ROOT / "full") -> Path:
    """Download and extract the full dataset into ``destination``."""
    if DATASET_URL is None:
        raise NotImplementedError(
            "The dataset is not published yet. Use data/sample/ for now, or point DATASET_URL at your own copy."
        )
    raise NotImplementedError


if __name__ == "__main__":
    download()
