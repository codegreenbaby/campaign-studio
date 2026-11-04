"""One self-contained HTML board for sharing: every banner of a campaign, live animation, no other files.

  .venv/Scripts/python tools/board_standalone.py <CODE>

Writes
  campaigns/<CODE>/dist/<CODE>-board.html            standalone file (double-click to open)
  campaigns/<CODE>/dist/artifact/<CODE>-board.html   same page without the document skeleton (Artifact publish)

The banner template is stored once, texts once per language, images once as data: URIs. The page
builds each banner into an iframe (srcdoc) when its row scrolls near, so it plays its animation then.
Only Google Fonts load from the network (allowed by the Artifact CSP).
"""
import base64
from html import escape as html_escape
import json
import sys
from pathlib import Path

from common import campaign_dir

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def data_uri(p):
    mime = {".svg": "image/svg+xml", ".jpg": "image/jpeg", ".png": "image/png"}[p.suffix]
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def main(code):
    cd = campaign_dir(code)
    camp, formats = load(cd / "campaign.json"), load(ROOT / "formats.json")
    tpl = (ROOT / camp["template"]).read_text(encoding="utf-8")
    langs = camp.get("langs") or formats["langs"]
    texts = {l: {**load(cd / "i18n" / "en.json"), **load(cd / "i18n" / f"{l}.json")} for l in langs if (cd / "i18n" / f"{l}.json").exists()}
    assets = {k: data_uri(cd / v) for k, v in camp["assets"].items() if k != "candles"}
    data = {
        "code": code, "version": camp["version"], "tpl": tpl, "texts": texts, "assets": assets,
        "candlesSvg": (cd / camp["assets"]["candles"]).read_text(encoding="utf-8"),
        "formats": formats["formats"], "langs": [l for l in langs if l in texts],
        "langLabel": formats["langLabel"], "rtl": formats["rtl"],
        "title": camp.get("title", code), "brandName": camp.get("brandName", ""), "theme": camp.get("theme", {}),
        "counts": camp.get("counts", []), "shortOrder": camp.get("shortOrder", []), "seconds": camp.get("seconds", 6),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = camp.get("title", code)
    head = HEAD.replace("{TITLE}", html_escape(title))
    body = BODY.replace("{TITLE}", html_escape(title)).replace("/*DATA*/", payload)
    out = cd / "dist"; (out / "artifact").mkdir(parents=True, exist_ok=True)
    (out / "artifact" / f"{code}-board.html").write_text(head + body, encoding="utf-8")
    (out / f"{code}-board.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + head + "</head>\n<body>\n" + body + "</body>\n</html>\n", encoding="utf-8")
    kb = (out / f"{code}-board.html").stat().st_size / 1024
    print(f"wrote dist/{code}-board.html ({kb:.0f} KB) and dist/artifact/{code}-board.html; {len(data['langs'])} languages x {len(data['formats'])} formats")


HEAD = """<title>{TITLE}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: a Figma-like review canvas. Sticky toolbar, one horizontally scrolling row per language,
   frames at true proportions with their production names above them. */
:root {
  --canvas: #EEEDF2; --surface: #FFFFFF; --ink: #15121F; --muted: #6A6577; --line: #DAD6E3;
  --accent: #A761FF; --accent-ink: #111827; --chip: #F3EEFC;
  --display: "Poppins", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, "Cascadia Mono", Consolas, monospace;
  --s: 0.24;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --canvas: #141219; --surface: #1D1A24; --ink: #EEEAF6; --muted: #A49DB3; --line: #2E2939; --chip: #2A2236; color-scheme: dark; } }
:root[data-theme="dark"] { --canvas: #141219; --surface: #1D1A24; --ink: #EEEAF6; --muted: #A49DB3; --line: #2E2939; --chip: #2A2236; color-scheme: dark; }
@media (max-width: 640px) {
  :root { --s: 0.16; }
  header.bar { position: static; }
  nav.langs { flex-wrap: nowrap; overflow-x: auto; }
  nav.langs a { flex: none; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--canvas); color: var(--ink); font-family: var(--display); font-size: 14px; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--surface); }
.wrap { padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
header.bar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--surface); border-bottom: 1px solid var(--line); }
.bar .wrap { display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: center; justify-content: space-between; padding-block: 14px; }
.title { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.title h1 { margin: 0; font-size: 18px; font-weight: 600; letter-spacing: -0.01em; text-wrap: balance; }
.title p { margin: 0; color: var(--muted); font-size: 12.5px; }
.tools { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
button { font: 600 13px var(--display); border: 0; border-radius: 999px; padding: 9px 16px; cursor: pointer; background: var(--accent); color: var(--accent-ink); }
button.ghost { background: transparent; color: var(--ink); box-shadow: inset 0 0 0 1px var(--line); }
button:focus-visible, a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
nav.langs { display: flex; flex-wrap: wrap; gap: 6px; padding-block: 0 12px; }
nav.langs a { font: 500 12px var(--mono); color: var(--ink); text-decoration: none; background: var(--chip); padding: 5px 10px; border-radius: 999px; letter-spacing: 0.04em; }
main { padding-block: 28px 64px; display: flex; flex-direction: column; gap: 44px; }
section.lang { display: flex; flex-direction: column; gap: 12px; scroll-margin-top: 140px; }
section.lang h2 { margin: 0; display: flex; align-items: baseline; gap: 10px; font-size: 15px; font-weight: 600; }
section.lang h2 small { font: 400 12px var(--mono); color: var(--muted); }
.row { display: flex; gap: calc(120px * var(--s)); align-items: flex-start; overflow-x: auto; padding-bottom: 10px; }
figure { margin: 0; flex: none; display: flex; flex-direction: column; gap: 6px; }
figcaption { font: 400 10.5px var(--mono); color: var(--muted); white-space: nowrap; }
.frame { position: relative; overflow: hidden; background: #07060B; border-radius: 2px; box-shadow: 0 1px 2px rgba(21, 18, 31, 0.12); }
.frame iframe { position: absolute; left: 0; top: 0; border: 0; transform-origin: 0 0; }
.frame .wait { position: absolute; inset: 0; display: grid; place-items: center; color: #6A6577; font: 400 11px var(--mono); }
footer { color: var(--muted); font-size: 12px; padding-block: 0 40px; max-width: 70ch; line-height: 1.55; }
</style>
"""

BODY = """<header class="bar"><div class="wrap">
  <div class="title"><h1>{TITLE}</h1>
    <p><span id="count"></span> Each banner plays its 6-second animation when it scrolls into view.</p></div>
  <div class="tools"><button id="replay" type="button">Replay animation</button><button id="final" class="ghost" type="button">Show final frame</button></div>
</div><div class="wrap"><nav class="langs" id="langs" aria-label="Languages"></nav></div></header>
<main class="wrap" id="board"></main>
<footer class="wrap">Static versions equal the last frame. Translations are machine translations pending native review. Items marked [VERIFY] in the disclaimer are not confirmed yet. </footer>
<script>
const D = /*DATA*/;
const board = document.getElementById("board"), nav = document.getElementById("langs");
const live = new Set();
function scale() { return parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--s")) || 0.24; }
function name(f, l) { return `${D.code}_${f.w}x${f.h}_Static_${D.langLabel[l]}_v${D.version}`; }
function srcdoc(f, l) {
  const cfg = { w: f.w, h: f.h, layout: f.layout, slots: f.slots, safe: f.safe || null, platform: f.platform, lang: l,
    dir: D.rtl.includes(l) ? "rtl" : "ltr", text: D.texts[l], assets: D.assets, candlesSvg: D.candlesSvg,
    counts: D.counts, shortOrder: D.shortOrder, seconds: D.seconds, vars: Object.assign({}, D.theme, f.vars || {}),
    brandName: D.brandName, name: name(f, l) };
  return D.tpl.replace("<!--CFG-->", "<script>window.CFG = " + JSON.stringify(cfg).replace(/<\\//g, "<\\\\/") + ";<\\/script>");
}
function sizeFrames() {
  const s = scale();
  document.querySelectorAll(".frame").forEach((fr) => {
    const w = +fr.dataset.w, h = +fr.dataset.h;
    fr.style.width = Math.round(w * s) + "px"; fr.style.height = Math.round(h * s) + "px";
    const ifr = fr.querySelector("iframe"); if (ifr) ifr.style.transform = `scale(${s})`;
  });
}
function mount(sec) {
  if (sec.dataset.mounted) return; sec.dataset.mounted = "1";
  sec.querySelectorAll(".frame").forEach((fr) => {
    const f = D.formats[+fr.dataset.i], l = sec.dataset.lang;
    const ifr = document.createElement("iframe");
    ifr.width = f.w; ifr.height = f.h; ifr.title = name(f, l); ifr.style.transform = `scale(${scale()})`;
    ifr.srcdoc = srcdoc(f, l);
    ifr.addEventListener("load", () => { const w = fr.querySelector(".wait"); if (w) w.remove(); });
    fr.appendChild(ifr); live.add(ifr);
  });
}
D.langs.forEach((l) => {
  const a = document.createElement("a"); a.href = "#" + l; a.textContent = D.langLabel[l]; nav.appendChild(a);
  const sec = document.createElement("section"); sec.className = "lang"; sec.id = l; sec.dataset.lang = l;
  sec.innerHTML = `<h2>${D.langLabel[l]} <small>${D.rtl.includes(l) ? "right-to-left" : ""}</small></h2><div class="row"></div>`;
  const row = sec.querySelector(".row");
  D.formats.forEach((f, i) => {
    const fig = document.createElement("figure");
    fig.innerHTML = `<figcaption>${name(f, l)} - ${f.platform}</figcaption><div class="frame" data-i="${i}" data-w="${f.w}" data-h="${f.h}"><div class="wait">loading</div></div>`;
    row.appendChild(fig);
  });
  board.appendChild(sec);
});
document.getElementById("count").textContent = `${D.formats.length} formats × ${D.langs.length} languages.`;
sizeFrames();
const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) mount(e.target); }), { rootMargin: "400px 0px" });
document.querySelectorAll("section.lang").forEach((s) => io.observe(s));
document.getElementById("replay").addEventListener("click", () => live.forEach((f) => { try { f.contentWindow.postMessage("replay", "*"); } catch (e) {} }));
document.getElementById("final").addEventListener("click", () => live.forEach((f) => { try { f.contentWindow.postMessage("final", "*"); } catch (e) {} }));
matchMedia("(max-width: 640px)").addEventListener("change", sizeFrames);
</script>
"""

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
