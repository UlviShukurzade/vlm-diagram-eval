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

## Licence

`mermaid.min.js` is a minified build of [Mermaid](https://github.com/mermaid-js/mermaid),
distributed under the MIT Licence:

    Copyright (c) 2014 - 2024 Knut Sveidqvist

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the above copyright notice and this permission notice being included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

The minified bundle carries no licence header of its own, so it is reproduced here
to satisfy the MIT attribution requirement. The MIT licence on this repository
covers the project's own code, not this vendored dependency.
