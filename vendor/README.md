# vendor/

`mermaid.min.js` is the exact build used to render every diagram in the thesis,
copied byte-for-byte from the original working tree.

    size    3338725 bytes
    sha256  616a109f19cd186842e11d45b35ac07456b3a75513310f6ea075351aa430b1e2

It carries no extractable version string, so it cannot be re-fetched from a CDN
and is committed here instead. **Do not replace it with a released mermaid build**
— Mermaid's layout changes between versions, so a different build produces
different images and the rendered inputs stop matching the thesis.

The parser service (`services/mermaid_parser`) separately pins mermaid 11.12.2 for
*parsing*. The two need not match: parsing extracts structure, rendering produces
pixels, and ground truth and model output both go through the same parser.
