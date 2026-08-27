"""Render Mermaid sources to PNG -- the preprocessing step that produces model inputs.

Ported from the thesis working tree's ``render_high_res.ipynb``.

Rendering runs Mermaid **in a headless browser** via Playwright, not through the
Mermaid CLI. Thesis section 4.1.2 states ``mmdc`` was used; the implementation
never invoked it. Anyone reproducing these images must use this path -- ``mmdc``
uses a different layout and rasterisation and will not produce matching images.

``mermaid.min.js`` is served from memory by intercepting the page's request for
it, so rendering is offline and pinned to one library build rather than whatever
a CDN serves that day. Fetch it with ``--fetch-lib`` before the first run.

The source is rendered **verbatim**. The notebook defined a ``fix_mermaid_syntax``
helper that stripped backslashes, but never called it; it is deliberately not
ported. Calling it would corrupt labels containing ``\\n`` and break trapezoid
shape syntax (``[/text\\]``), so images would stop matching the ground-truth
graphs parsed from the same source.

**Renders are not byte-reproducible across machines.** Verified by re-rendering
``flowchart_5087_23`` and comparing to the thesis original: the structure is
identical -- same nodes, edges, subgraphs and labels -- but the canvas differs
(3036x450 originally, 4171x565 here). Mermaid sizes nodes from measured text
width, so the host's font stack changes every dimension. The thesis rendered on
Linux; this was checked on macOS. Pin fonts, or render in a container, if you
need pixel-identical output.

Usage::

    python scripts/render_diagrams.py --fetch-lib
    python scripts/render_diagrams.py --input data/sample --output renders/
    python scripts/render_diagrams.py --parquet sample_900_sci.parquet --output renders/

Requires ``playwright`` and a Chromium build::

    uv pip install playwright && uv run playwright install chromium
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import urllib.request
from pathlib import Path

# ── Rendering parameters (thesis section 4.1.2: 2x scale was used) ────────────
DEFAULT_SCALE = 2.0  # "2x high-resolution images for inferencing"
CONCURRENCY = 50  # parallel browser pages
MAX_PX_LIMIT = 16000  # ceiling on the larger dimension; scale is reduced to fit
RESTART_INTERVAL = 50  # recycle each page every N diagrams to bound memory growth
SVG_TIMEOUT_MS = 10_000

MERMAID_VERSION = "11.12.2"  # matches the parser service, so both paths agree
MERMAID_CDN = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
LIB_PATH = Path(__file__).resolve().parents[1] / "vendor" / "mermaid.min.js"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
        body {{ margin: 0; padding: 0; background: white; width: fit-content; height: fit-content; }}
        #container {{ display: inline-block; padding: 10px; }}
    </style>
</head>
<body>
    <div id="container">
        <pre class="mermaid">
        {code}
        </pre>
    </div>

    <script src="http://localhost/mermaid.min.js"></script>

    <script>
      mermaid.initialize({{
        startOnLoad: true,
        theme: 'default',
        flowchart: {{ useMaxWidth: false, htmlLabels: true }},
        sequence: {{ useMaxWidth: false }},
        gantt: {{ useMaxWidth: false }},
        journey: {{ useMaxWidth: false }},
        er: {{ useMaxWidth: false }},
        pie: {{ useMaxWidth: false }}
      }});
    </script>
</body>
</html>
"""


def fetch_library(dest: Path = LIB_PATH) -> Path:
    """Download the pinned mermaid build used for rendering."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching mermaid {MERMAID_VERSION} -> {dest}")
    urllib.request.urlretrieve(MERMAID_CDN, dest)
    print(f"  {dest.stat().st_size / 1024 / 1024:.2f} MB")
    return dest


async def _worker(queue, browser, lib_bytes, out_dir, counter):
    from playwright.async_api import Error as PlaywrightError

    context = await browser.new_context(device_scale_factor=1.0)
    page = None

    async def reset_page():
        """Recreate the page; Mermaid leaks memory across many renders."""
        nonlocal page
        if page:
            await page.close()
        page = await context.new_page()
        await page.route(
            "**/mermaid.min.js",
            lambda route: route.fulfill(status=200, content_type="application/javascript", body=lib_bytes),
        )

    await reset_page()
    processed = 0

    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break

        name, code = item
        if processed and processed % RESTART_INTERVAL == 0:
            await reset_page()
        processed += 1

        target = out_dir / (name if name.lower().endswith(".png") else f"{name}.png")
        try:
            await page.set_content(HTML_TEMPLATE.format(code=code))
            svg = page.locator(".mermaid svg")
            await svg.wait_for(state="visible", timeout=SVG_TIMEOUT_MS)

            box = await svg.bounding_box()
            if not box:
                counter["no_dimensions"] += 1
                print(f"  warning: {name} rendered with no dimensions")
            else:
                # Scale down if 2x would exceed the pixel ceiling.
                largest = max(box["width"], box["height"])
                safe = MAX_PX_LIMIT / largest if largest else 1
                scale = max(1.0, min(DEFAULT_SCALE, safe))
                if scale > 1.0:
                    await page.evaluate(f"document.body.style.zoom = '{scale}'")
                target.write_bytes(await svg.screenshot())
                counter["rendered"] += 1
        except (PlaywrightError, OSError) as exc:
            counter["failed"] += 1
            print(f"  error: {name}: {str(exc)[:110]}")
        finally:
            queue.task_done()


async def render(items: list[tuple[str, str]], out_dir: Path) -> dict[str, int]:
    """Render ``(name, mermaid_code)`` pairs into ``out_dir``."""
    from playwright.async_api import async_playwright

    if not LIB_PATH.exists():
        sys.exit(f"missing {LIB_PATH}\nRun: python scripts/render_diagrams.py --fetch-lib")
    lib_bytes = LIB_PATH.read_bytes()
    out_dir.mkdir(parents=True, exist_ok=True)

    queue: asyncio.Queue = asyncio.Queue()
    for pair in items:
        queue.put_nowait(pair)

    counter = {"rendered": 0, "failed": 0, "no_dimensions": 0}
    print(f"rendering {len(items)} diagrams at {DEFAULT_SCALE}x -> {out_dir}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--ignore-certificate-errors", "--disable-gpu", "--no-sandbox"],
        )
        workers = []
        for _ in range(min(CONCURRENCY, max(1, len(items)))):
            queue.put_nowait(None)  # poison pill, one per worker
            workers.append(asyncio.create_task(_worker(queue, browser, lib_bytes, out_dir, counter)))
        await asyncio.gather(*workers)
        await browser.close()

    print(f"  rendered {counter['rendered']}, failed {counter['failed']}, no dimensions {counter['no_dimensions']}")
    return counter


def load_items(args) -> list[tuple[str, str]]:
    if args.parquet:
        import pandas as pd

        df = pd.read_parquet(args.parquet)
        return [(str(r["image_filename"]), str(r["code"])) for _, r in df.iterrows()]
    return [(p.stem, p.read_text()) for p in sorted(Path(args.input).rglob("*.mmd"))]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fetch-lib", action="store_true", help="download the pinned mermaid build and exit")
    ap.add_argument("--input", type=Path, help="directory of .mmd files")
    ap.add_argument("--parquet", type=Path, help="parquet with image_filename and code columns")
    ap.add_argument("--output", type=Path, default=Path("renders"))
    args = ap.parse_args()

    if args.fetch_lib:
        fetch_library()
        return
    if not args.input and not args.parquet:
        ap.error("give --input or --parquet (or --fetch-lib)")

    items = load_items(args)
    if not items:
        sys.exit("no diagrams found")
    asyncio.run(render(items, args.output))


if __name__ == "__main__":
    main()
