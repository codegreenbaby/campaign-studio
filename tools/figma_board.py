"""Turn a campaign's exported PNGs into a plugin patch (state/patch.json), and record the ids back.

  .venv/Scripts/python tools/figma_board.py <CODE>                  # write state/patch.json (build)
  .venv/Scripts/python tools/figma_board.py <CODE> --record         # after the plugin ran: ids -> state/figma.json
  .venv/Scripts/python tools/figma_board.py <CODE> --cleanup-legacy # patch that removes this campaign from the legacy file in state

Target file: state/figma.json "file" / "fileKey". Three pages per campaign, as in the
reference board:
  {CODE} — Master visuals   EN row + source assets
  {CODE} — Formats          one row per language, formats in formats.json order
  {CODE} — video layers     EN, per format a column: bg / candles / rocket / text
Each banner is a frame named {CODE}_{W}x{H}_Static_{LANG}_v{N} with a text layer
"label - <name>" above it reading "<name> - <platform>".
The patch carries "file": the plugin refuses to run it in any other Figma file. A re-run empties
the campaign's own pages first (clearPage, guarded by the page-name prefix).
Banner images go in as JPEG (q92) to keep the patch small; layers stay PNG for transparency.
"""
import argparse
import json
from pathlib import Path

from PIL import Image

from common import campaign_dir, fail, figma_state

ROOT = Path(__file__).resolve().parent.parent
LABEL_H, LABEL_GAP, COL_GAP, ROW_GAP, ROW_TITLE = 40, 24, 120, 280, 90
LAYERS = ["bg", "candles", "rocket", "text"]
PAGES = ["Master visuals", "Formats", "video layers"]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save_state(state):
    (ROOT / "state" / "figma.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def to_jpg(png, out_dir):
    out = out_dir / (png.stem + ".jpg")
    if not out.exists() or out.stat().st_mtime < png.stat().st_mtime:
        Image.open(png).convert("RGB").save(out, quality=92, optimize=True)
    return out


def rel(p):
    return p.resolve().relative_to(ROOT).as_posix()


def build(code):
    cdir = campaign_dir(code)
    camp = load(cdir / "campaign.json")
    formats = load(ROOT / "formats.json")
    state = figma_state()
    if not any((cdir / "dist" / "png").glob("*.png")):
        fail(f"no PNGs in campaigns/{code}/dist/png. Run tools/render.py {code} and tools/export.py {code} first.")
    d = ROOT / "campaigns" / code / "dist"
    jpg_dir = d / "figma"; jpg_dir.mkdir(exist_ok=True)
    ver = camp["version"]
    label = formats["langLabel"]
    langs = [l for l in formats["langs"] if any((d / "png").glob(f"{code}_*_{label[l]}_v{ver}.png"))]
    fmts = formats["formats"]
    max_h = max(f["h"] for f in fmts)
    ops = []

    def name(f, lang, kind="Static"):
        return f"{code}_{f['w']}x{f['h']}_{kind}_{label[lang]}_v{ver}"

    def page(title, index):
        ops.append({"op": "page", "name": f"{code} — {title}", "index": index, "ref": f"page:{title}"})
        pid = f"${len(ops) - 1}"
        ops.append({"op": "clearPage", "node": pid, "prefix": f"{code} — "})
        return pid

    def banner(parent, f, n, x, y, file, ref):
        ops.append({"op": "label", "parent": parent, "text": f"{n} - {f['platform']}", "x": x, "y": y, "size": 24, "name": f"label - {n}"})
        ops.append({"op": "frame", "parent": parent, "name": n, "x": x, "y": y + LABEL_H + LABEL_GAP, "w": f["w"], "h": f["h"], "file": file, "ref": ref})

    def row(parent, y, lang):
        ops.append({"op": "label", "parent": parent, "text": label[lang], "x": 0, "y": y, "size": 48, "color": "#111827", "name": f"row - {label[lang]}"})
        x, y0 = 0, y + ROW_TITLE
        for f in fmts:
            n = name(f, lang)
            png = d / "png" / f"{n}.png"
            if png.exists():
                banner(parent, f, n, x, y0, rel(to_jpg(png, jpg_dir)), f"frame:{n}")
            x += f["w"] + COL_GAP
        return y0 + LABEL_H + LABEL_GAP + max_h + ROW_GAP

    # 1. Master visuals: EN row + assets
    pm = page("Master visuals", 0)
    y = row(pm, 0, "en")
    ops.append({"op": "label", "parent": pm, "text": f"Assets (campaigns/{code}/assets)", "x": 0, "y": y, "size": 48, "color": "#111827", "name": "row - assets"})
    y += ROW_TITLE
    bg = ROOT / "campaigns" / code / camp["assets"]["bg"]
    im = Image.open(bg); w = 1200; h = round(w * im.height / im.width)
    ops.append({"op": "label", "parent": pm, "text": f"asset - {bg.name}", "x": 0, "y": y, "size": 24, "name": f"label - asset - {bg.name}"})
    ops.append({"op": "frame", "parent": pm, "name": f"asset - {bg.name}", "x": 0, "y": y + LABEL_H + LABEL_GAP, "w": w, "h": h, "file": rel(bg)})
    x = w + COL_GAP
    for key in ("rocket", "candles", "logo"):
        f = ROOT / "campaigns" / code / camp["assets"][key]
        ops.append({"op": "label", "parent": pm, "text": f"asset - {f.name}", "x": x, "y": y, "size": 24, "name": f"label - asset - {f.name}"})
        ops.append({"op": "svg", "parent": pm, "svgFile": rel(f), "name": f"asset - {f.name}", "x": x, "y": y + LABEL_H + LABEL_GAP})
        x += 560

    # 2. Formats: one row per language
    pf = page("Formats", 1)
    y = 0
    for lang in langs:
        y = row(pf, y, lang)

    # 3. video layers: EN, one column per format
    lay_dir = d / "layers"
    pv = page("video layers", 2)
    x = 0
    for f in fmts:
        n = name(f, "en", "Video")
        y = 0
        ops.append({"op": "label", "parent": pv, "text": n, "x": x, "y": y, "size": 32, "color": "#111827", "name": f"row - {n}"})
        y += ROW_TITLE
        for L in LAYERS:
            png = lay_dir / f"{name(f, 'en')}__{L}.png"
            if png.exists():
                banner(pv, {**f, "platform": L}, f"{n} / {L}", x, y, rel(png), f"layer:{n}/{L}")
            y += LABEL_H + LABEL_GAP + f["h"] + 120
        x += f["w"] + COL_GAP

    for leftover in ("Page 1", "Страница 1"):
        ops.append({"op": "removeEmptyPage", "name": leftover})
    patch = {"id": f"{code}-pages-v{ver}", "file": state["file"], "ops": ops}
    (ROOT / "state" / "patch.json").write_text(json.dumps(patch, ensure_ascii=False, indent=1), encoding="utf-8")
    size = sum((ROOT / o["file"]).stat().st_size for o in ops if "file" in o)
    print(f"patch for file '{state['file']}': {len(ops)} ops, {sum(1 for o in ops if o['op'] == 'frame')} frames, images {size / 1e6:.1f} MB, langs {langs}")


def cleanup_legacy(code):
    state = figma_state()
    leg = state.get("legacy")
    if not leg:
        fail('state/figma.json has no "legacy" entry: nothing to clean up.')
    patch = {"id": f"{code}-cleanup-legacy", "file": leg["file"], "page": leg["page"],
             "ops": [{"op": "removeByPrefix", "prefix": f"{code} — "}]}
    (ROOT / "state" / "patch.json").write_text(json.dumps(patch, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"cleanup patch for file '{leg['file']}', page {leg['page']}: removes top-level nodes named '{code} — *'")


def record(code):
    if not (ROOT / "state" / "patch-result.json").exists():
        fail("state/patch-result.json is missing: run the plugin first.")
    res = load(ROOT / "state" / "patch-result.json")
    patch = load(ROOT / "state" / "patch.json")
    state = figma_state()
    c = state["campaigns"].setdefault(code, {})
    c["pages"], c["frames"], c["bySection"] = {}, {}, {}
    applied = {item["i"]: item for item in res["applied"]}
    section = None
    for i, op in enumerate(patch["ops"]):
        ref = op.get("ref")
        if not ref or i not in applied:
            continue
        r = applied[i]["result"]; nid = r if isinstance(r, str) else r.get("id")
        kind, key = ref.split(":", 1)
        if kind == "page":
            section = key; c["pages"][key] = nid; continue
        c["bySection"].setdefault(section, {})[key] = nid
        if section != "Master visuals":
            c["frames"][key] = nid
    save_state(state)
    print(f"recorded {len(c['pages'])} pages, {len(c['frames'])} frames; failed ops: {len(res['failed'])}")
    for f in res["failed"]:
        print("  failed", f)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("code")
    ap.add_argument("--record", action="store_true"); ap.add_argument("--cleanup-legacy", action="store_true")
    a = ap.parse_args()
    if a.record:
        record(a.code)
    elif a.cleanup_legacy:
        cleanup_legacy(a.code)
    else:
        build(a.code)
