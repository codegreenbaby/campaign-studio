# Campaign Studio Patch

A Figma development plugin that applies JSON patches the agent prepares. It exists because the
Figma MCP server is capped at a small number of calls per month on free and view-seat plans,
while plugins have no such cap.

## One-time setup (Figma Desktop)

Development plugins load only in the desktop app.

1. Open the target Figma file in Figma Desktop.
2. Plugins → Development → Import plugin from manifest…
3. Pick `plugin/manifest.json` from this repository.

## Each run

1. The agent writes `state/patch.json` and starts `tools/patch_server.py` (127.0.0.1:8787).
2. In Figma: Plugins → Development → Campaign Studio Patch → **Apply patch from agent**.
3. The plugin applies the ops, shows a toast with counts and its build stamp, and posts a report
   back. The agent reads `state/patch-result.json`; screenshots land in `state/shots/`.

If the plugin cannot reach the server, use "Paste a patch instead" and paste the JSON. The report
then stays in the plugin window.

If the window title shows an old build stamp, Figma is running a cached copy: remove the plugin
under Plugins → Development → Manage plugins in development and import the manifest again.

## Patch format

```json
{ "id": "SPRING25-pages-v1", "file": "Campaigns", "ops": [
  { "op": "page",      "name": "SPRING25 — Formats", "index": 1, "ref": "page:Formats" },
  { "op": "clearPage", "node": "$0", "prefix": "SPRING25 — " },
  { "op": "label",     "parent": "$0", "text": "SPRING25_1080x1350_Static_EN_v1 - Meta", "x": 0, "y": 90, "size": 24 },
  { "op": "frame",     "parent": "$0", "name": "SPRING25_1080x1350_Static_EN_v1", "x": 0, "y": 154, "w": 1080, "h": 1350,
    "file": "campaigns/SPRING25/dist/figma/SPRING25_1080x1350_Static_EN_v1.jpg" },
  { "op": "svg",       "parent": "$0", "svgFile": "campaigns/SPRING25/assets/logo.svg", "x": 1200, "y": 154 },
  { "op": "removeEmptyPage", "name": "Page 1" }
] }
```

- `"file"` at the top names the Figma file the patch is for. Opened in any other file, the plugin
  changes nothing and reports which file it saw.
- `"$3"` anywhere in an op means "the node made or returned by op 3".
- `file` and `svgFile` inside ops are repository-relative paths; the server inlines them as
  base64 / SVG text and refuses paths outside the repository.
- Each op runs on its own: a failing op is reported and the rest still run.

## Ops

| Op | What it does |
|---|---|
| `page` | Find a page by exact name or create it, and make it current. On plans with a page limit, takes over an empty page that is not another campaign's page. |
| `clearPage` | Empty one of the campaign's own pages (its name must start with `prefix`). Makes re-runs idempotent. |
| `removeEmptyPage` | Remove a leftover default page, only if it is empty. |
| `section` | A container frame with no fill, placed below everything on the current page. |
| `removeByPrefix` | Remove top-level nodes on the current page whose name starts with `prefix`. |
| `frame` | A frame, optionally filled with an image (`file`). |
| `label` | A text layer (Inter Regular). |
| `image`, `setImage` | Rectangle with an image fill / swap the image in an existing layer. |
| `svg`, `replaceWithSvg` | Import SVG markup / swap a layer for SVG at the same spot. |
| `text`, `fill`, `stroke`, `effects`, `set`, `resize`, `findSet`, `shiftChildren`, `clone`, `remove`, `badge` | In-place edits of existing layers. `set` accepts only properties in `SETTABLE`. |
| `inspect`, `screenshot` | Read a subtree's ids and bounds / export a PNG, without spending MCP calls. |

## Things that fail silently in Figma (and how the plugin handles them)

- **Pages must be loaded before reading their children** (`documentAccess: dynamic-page`).
  The plugin calls `loadAsync()` first.
- **Plan page limits.** `createPage` throws on plans with a page cap; `page` falls back to an
  empty spare page and says so in its result (`isNew: "reused"`).
- **Unloaded fonts throw** on any text write; every text op loads its font first.
- **Never draw at the origin by accident**: `section` places itself below existing content.

## Tests

```
.venv/Scripts/python plugin/test/run_stub_tests.py
```

Runs `code.js` against `plugin/test/stub.js`, a stand-in for the Figma plugin API that throws
where the real API throws (unloaded pages and fonts, negative sizes, page limits), using the
current `state/patch.json` or a built-in sample. It proves the code runs and the patch is
idempotent; it cannot prove text metrics or rendering.
