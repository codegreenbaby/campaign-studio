"""Build every format x language of a campaign into self-contained banner pages plus the board.

  .venv/Scripts/python tools/render.py <CODE>                # all languages in formats.json
  .venv/Scripts/python tools/render.py <CODE> --langs en     # English row only
  .venv/Scripts/python tools/render.py <CODE> --check        # also open each banner and report overflow

Writes campaigns/<CODE>/dist/banners/<name>.html and campaigns/<CODE>/dist/board.html.
Missing keys in a language file fall back to en.json and are listed.
"""
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def frame_name(fmt, code, kind, lang_label, ver):
    return f"{code}_{fmt['w']}x{fmt['h']}_{kind}_{lang_label}_v{ver}"


def build(code, langs, with_static_names=True):
    camp_dir = ROOT / "campaigns" / code
    camp = load(camp_dir / "campaign.json")
    formats = load(ROOT / "formats.json")
    tpl = (ROOT / camp["template"]).read_text(encoding="utf-8")
    en = load(camp_dir / "i18n" / "en.json")
    out = camp_dir / "dist" / "banners"
    out.mkdir(parents=True, exist_ok=True)
    candles_svg = (camp_dir / camp["assets"]["candles"]).read_text(encoding="utf-8")
    assets = {k: "../../" + v for k, v in camp["assets"].items() if k != "candles"}
    langs = langs or formats["langs"]
    rows = []
    missing = {}
    for lang in langs:
        lf = camp_dir / "i18n" / f"{lang}.json"
        tx = dict(en)
        if lf.exists():
            loc = load(lf)
            miss = [k for k in en if k not in loc]
            if miss:
                missing[lang] = miss
            tx.update(loc)
        elif lang != "en":
            missing[lang] = ["<no file>"]
        label = formats["langLabel"][lang]
        row = []
        for fmt in formats["formats"]:
            name = frame_name(fmt, code, "Static", label, camp["version"])
            cfg = {
                "w": fmt["w"], "h": fmt["h"], "layout": fmt["layout"], "slots": fmt["slots"],
                "safe": fmt.get("safe"), "platform": fmt["platform"], "lang": lang,
                "dir": "rtl" if lang in formats["rtl"] else "ltr", "text": tx, "assets": assets,
                "candlesSvg": candles_svg, "counts": camp.get("counts", []),
                "shortOrder": camp.get("shortOrder", []), "seconds": camp.get("seconds", 6),
                "vars": {**camp.get("theme", {}), **fmt.get("vars", {})}, "name": name, "brandName": camp.get("brandName", ""),
            }
            page = tpl.replace("<!--CFG-->", "<script>window.CFG = " + json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/") + ";</script>")
            page = page.replace("<title>banner</title>", f"<title>{html.escape(name)}</title>")
            (out / f"{name}.html").write_text(page, encoding="utf-8")
            row.append({"name": name, "platform": fmt["platform"], "w": fmt["w"], "h": fmt["h"]})
        rows.append({"lang": lang, "label": label, "items": row})
    write_board(camp_dir, code, rows, formats, camp.get("title", code))
    return rows, missing


def write_board(camp_dir, code, rows, formats, title):
    scale = 0.3
    gap = formats["board"]["gap"] * scale
    row_html = []
    for r in rows:
        cells = []
        for it in r["items"]:
            w, h = it["w"] * scale, it["h"] * scale
            cells.append(
                f'<figure style="width:{w:.0f}px"><figcaption>{html.escape(it["name"])} - {it["platform"]}</figcaption>'
                f'<div class="f" style="width:{w:.0f}px;height:{h:.0f}px"><iframe src="banners/{html.escape(it["name"])}.html" '
                f'width="{it["w"]}" height="{it["h"]}" style="transform:scale({scale})" loading="lazy" title="{html.escape(it["name"])}"></iframe></div></figure>')
        row_html.append(f'<section><h2>{html.escape(r["label"])}</h2><div class="row" style="gap:{gap:.0f}px">{"".join(cells)}</div></section>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--canvas:#EDEDF0;--label:#6B7280;--ink:#111827;--purple:#A761FF}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--canvas:#1E1E22;--label:#9CA3AF;--ink:#F3F4F6}}}}
:root[data-theme="dark"]{{--canvas:#1E1E22;--label:#9CA3AF;--ink:#F3F4F6}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--canvas);color:var(--ink);font-family:Poppins,system-ui,sans-serif;padding:24px 16px 80px}}
header{{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;max-width:100%;margin-bottom:28px}}
header h1{{font-size:18px;font-weight:600}}
header p{{font-size:13px;color:var(--label)}}
button{{font:600 13px Poppins,sans-serif;border:0;border-radius:999px;padding:10px 18px;background:var(--purple);color:#111827;cursor:pointer}}
button.ghost{{background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1px var(--label)}}
section{{margin-bottom:48px}}
h2{{font-size:13px;font-weight:600;color:var(--label);letter-spacing:.08em;margin-bottom:10px}}
.row{{display:flex;align-items:flex-start;overflow-x:auto;padding-bottom:8px}}
figure{{flex:none}}
figcaption{{font-size:10px;color:var(--label);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:6px}}
.f{{position:relative;overflow:hidden;border-radius:2px;box-shadow:0 1px 2px rgba(17,24,39,.08)}}
iframe{{border:0;transform-origin:0 0;position:absolute;left:0;top:0}}
</style></head><body>
<header><div><h1>{html.escape(title)}</h1><p>Rows are languages, columns are formats. Machine translations pending native review.</p></div>
<div style="display:flex;gap:8px"><button id="replay">Replay animation</button><button class="ghost" id="final">Show final frame</button></div></header>
{''.join(row_html)}
<script>
const send=(m)=>document.querySelectorAll('iframe').forEach(f=>{{try{{f.contentWindow.postMessage(m,'*')}}catch(e){{}}}});
document.getElementById('replay').onclick=()=>send('replay');
document.getElementById('final').onclick=()=>send('final');
</script></body></html>"""
    (camp_dir / "dist" / "board.html").write_text(page, encoding="utf-8")


def check(code, rows):
    from playwright.sync_api import sync_playwright
    camp_dir = ROOT / "campaigns" / code
    problems = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for r in rows:
            for it in r["items"]:
                pg = b.new_page(viewport={"width": it["w"], "height": it["h"]})
                pg.goto((camp_dir / "dist" / "banners" / f"{it['name']}.html").as_uri() + "?t=6")
                pg.wait_for_function("window.__ready === true", timeout=30000)
                rep = pg.evaluate("window.__report")
                if rep["overflow"] or rep["short"]:
                    problems[it["name"]] = rep
                pg.close()
        b.close()
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code"); ap.add_argument("--langs", nargs="*"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows, missing = build(a.code, a.langs)
    n = sum(len(r["items"]) for r in rows)
    print(f"built {n} banners + board.html")
    for lang, keys in missing.items():
        print(f"  {lang}: falls back to en for {keys}")
    if a.check:
        probs = check(a.code, rows)
        for name, rep in probs.items():
            print(f"  {name}: overflow={rep['overflow']} short={rep['short']}")
        print("check:", "clean" if not any(r["overflow"] for r in probs.values()) else "OVERFLOW")
        if any(r["overflow"] for r in probs.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()
