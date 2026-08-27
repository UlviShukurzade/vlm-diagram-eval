// index.cjs
// 1) load and wire up JSDOM+DOMPurify first:
const { JSDOM }     = require("jsdom");
const createDP      = require("dompurify");
const { window }    = new JSDOM(`<!doctype html><html><body></body></html>`, {
  pretendToBeVisual: true
});

const DOMPurify     = createDP(window);
// Monkey-patch all the globals Mer­maid expects:
global.window                = window;
global.document              = window.document;
global.DOMParser             = window.DOMParser;
global.Node                  = window.Node;
global.Element               = window.Element;
global.HTMLElement           = window.HTMLElement;
global.SVGElement            = window.SVGElement;
global.SVGSVGElement         = window.SVGSVGElement;
global.MutationObserver      = window.MutationObserver;
global.DOMPurify             = DOMPurify;

// 2) **Override** the dompurify module in Node’s cache
//    so that `require("dompurify")` now returns your instance:
const dpPath = require.resolve("dompurify");
require.cache[dpPath].exports = DOMPurify;

// 3) now load Mermaid (it’ll pick up your patched dompurify)
let mermaid = require("mermaid");
if (mermaid.default) mermaid = mermaid.default;
mermaid.initialize({ startOnLoad: false });


const express = require('express');
const bodyParser = require('body-parser');
const app = express();

app.use(bodyParser.json({ limit: '1mb' }));

app.post('/diagram', async (req, res) => {
  const { code } = req.body;
  if (typeof code !== 'string') {
    return res.status(400).json({ error: 'Request must contain { code: string }' });
  }
  try {
    const { db } = await mermaid.mermaidAPI.getDiagramFromText(code);
    const data = db.getData();
    return res.json({
      nodes: data.nodes,
      edges: data.edges
});
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => console.log(`Mermaid JSON service listening on port ${PORT}`));
