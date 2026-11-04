"""Run plugin/code.js against the strict API stub in headless Chromium.

  .venv/Scripts/python plugin/test/run_stub_tests.py [patch.json]

Uses state/patch.json if it exists (images and SVGs replaced by small placeholders), otherwise a
built-in sample. Three scenarios:
  1. a fresh file with one empty default page and a 3-page limit
  2. the same patch run twice (must not duplicate anything)
  3. the patch opened in a different file (must change nothing)
Exits non-zero on any failed op.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

SAMPLE = {"id": "sample", "file": "Campaigns", "ops": [
    {"op": "page", "name": "DEMO — Master visuals", "index": 0, "ref": "page:Master visuals"},
    {"op": "clearPage", "node": "$0", "prefix": "DEMO — "},
    {"op": "label", "parent": "$0", "text": "DEMO_1080x1080_Static_EN_v1 - Meta", "x": 0, "y": 0, "size": 24},
    {"op": "frame", "parent": "$0", "name": "DEMO_1080x1080_Static_EN_v1", "x": 0, "y": 64, "w": 1080, "h": 1080, "file": "x"},
    {"op": "page", "name": "DEMO — Formats", "index": 1, "ref": "page:Formats"},
    {"op": "clearPage", "node": "$4", "prefix": "DEMO — "},
    {"op": "frame", "parent": "$4", "name": "DEMO_1200x628_Static_EN_v1", "x": 0, "y": 0, "w": 1200, "h": 628, "file": "x"},
    {"op": "page", "name": "DEMO — video layers", "index": 2, "ref": "page:video layers"},
    {"op": "clearPage", "node": "$7", "prefix": "DEMO — "},
    {"op": "svg", "parent": "$7", "svgFile": "x", "x": 0, "y": 0},
    {"op": "frame", "parent": "$7", "name": "bad size", "w": -5, "h": 0},
    {"op": "removeEmptyPage", "name": "Page 1"},
]}

HARNESS = """
window.__run = async (patch, fileName, pageLimit) => {
  const f = figma;
  f._page.name = "Page 1";
  const pages = [f._page];
  f.root = { name: fileName, get children() { return pages; },
    insertChild(i, p) { const k = pages.indexOf(p); if (k >= 0) pages.splice(k, 1); pages.splice(i, 0, p); } };
  f._page.parent = f.root;  // so page.remove() takes it out of the document
  f.createPage = () => {
    if (pageLimit && pages.length >= pageLimit) throw new Error("in createPage: The Starter plan only comes with " + pageLimit + " pages.");
    const p = f._make("PAGE", { name: "Page" }); p.parent = f.root; pages.push(p); return p;
  };
  const first = await applyPatch(patch);
  for (const p of pages) await p.loadAsync();
  const count1 = pages.map((p) => p.name + ":" + p.children.length).join(", ");
  const second = await applyPatch(patch);
  for (const p of pages) await p.loadAsync();
  const count2 = pages.map((p) => p.name + ":" + p.children.length).join(", ");
  const wrong = await applyPatch(Object.assign({}, patch, { file: fileName + " (other)" }));
  return { failed1: first.failed, failed2: second.failed, applied: first.applied.length, count1, count2, wrongFile: wrong };
};
"""


def load_patch(arg):
    p = Path(arg) if arg else ROOT / "state" / "patch.json"
    patch = json.loads(p.read_text(encoding="utf-8")) if p.exists() else SAMPLE
    for o in patch["ops"]:
        if "file" in o:
            o.pop("file"); o["base64"] = "SlBFRw=="
        if "svgFile" in o:
            o.pop("svgFile"); o["svg"] = "<svg width='10' height='10'></svg>"
    patch.setdefault("file", "Campaigns")
    return patch


def main():
    patch = load_patch(sys.argv[1] if len(sys.argv) > 1 else None)
    stub = (HERE / "stub.js").read_text(encoding="utf-8")
    code = (HERE.parent / "code.js").read_text(encoding="utf-8")
    ok = True
    with sync_playwright() as p:
        b = p.chromium.launch()
        for limit in (3, None):
            pg = b.new_page()
            pg.on("pageerror", lambda e: print("page error:", e))
            pg.set_content("<html><body></body></html>")
            pg.add_script_tag(content=stub); pg.add_script_tag(content=code); pg.add_script_tag(content=HARNESS)
            r = pg.evaluate("([p, n, l]) => window.__run(p, n, l)", [patch, patch["file"], limit])
            label = f"page limit {limit}" if limit else "no page limit"
            dup = r["count1"] != r["count2"]
            blocked = bool(r["wrongFile"]["failed"]) and not r["wrongFile"]["applied"]
            print(f"{label}: {r['applied']} applied, {len(r['failed1'])} failed; re-run duplicates: {dup}; wrong file blocked: {blocked}")
            print(f"  pages: {r['count2']}")
            for f in r["failed1"][:5]:
                print("  failed:", f)
            ok = ok and not r["failed1"] and not r["failed2"] and not dup and blocked
            pg.close()
        b.close()
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
