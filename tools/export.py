"""Export built banners to PNG (final frame) and, with --video, to 6-second MP4.

  .venv/Scripts/python tools/export.py <CODE>                      # PNG for every built banner
  .venv/Scripts/python tools/export.py <CODE> --match _EN_         # only names containing _EN_
  .venv/Scripts/python tools/export.py <CODE> --video --match _EN_ # MP4 too (frame-exact, 30 fps)
  .venv/Scripts/python tools/export.py <CODE> --sheet               # also a contact sheet of the PNGs per language

Video frames come from window.__seek(t), so playback speed never affects the file.
"""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FFMPEG_FALLBACK = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe"


def ffmpeg_bin():
    return shutil.which("ffmpeg") or (str(FFMPEG_FALLBACK) if FFMPEG_FALLBACK.exists() else None)


def size_of(name):
    wh = name.split("_")[1]
    w, h = wh.split("x")
    return int(w), int(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code"); ap.add_argument("--match", default="")
    ap.add_argument("--video", action="store_true"); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--layers", action="store_true", help="also export bg/candles/rocket/text layers (final frame) to dist/layers")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    d = ROOT / "campaigns" / a.code / "dist"
    banners = sorted(p for p in (d / "banners").glob("*.html") if a.match in p.name)
    (d / "png").mkdir(exist_ok=True)
    if a.video:
        (d / "mp4").mkdir(exist_ok=True)
        ff = ffmpeg_bin()
        if not ff:
            raise SystemExit("ffmpeg not found")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for f in banners:
            name = f.stem
            w, h = size_of(name)
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.goto(f.as_uri() + "?t=6")
            pg.wait_for_function("window.__ready === true", timeout=30000)
            pg.wait_for_timeout(150)
            pg.screenshot(path=str(d / "png" / f"{name}.png"))
            print("png", name)
            if a.layers:
                (d / "layers").mkdir(exist_ok=True)
                for L in ("bg", "candles", "rocket", "text"):
                    lp = b.new_page(viewport={"width": w, "height": h})
                    lp.goto(f.as_uri() + "?t=6&layer=" + L)
                    lp.wait_for_function("window.__ready === true", timeout=30000)
                    lp.wait_for_timeout(100)
                    lp.screenshot(path=str(d / "layers" / f"{name}__{L}.png"), omit_background=(L != "bg"))
                    lp.close()
                print("layers", name)
            if a.video:
                T = pg.evaluate("window.__T")
                n = int(T * a.fps)
                vname = name.replace("_Static_", "_Video_")
                cmd = [ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(a.fps), "-i", "-",
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
                       "-movflags", "+faststart", str(d / "mp4" / f"{vname}.mp4")]
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                for i in range(n):   # n frames, the last one lands exactly on T (= the static banner)
                    pg.evaluate(f"window.__seek({i * T / (n - 1)})")
                    proc.stdin.write(pg.screenshot(type="png"))
                proc.stdin.close(); proc.wait()
                print("mp4", vname, "ok" if proc.returncode == 0 else f"ffmpeg exit {proc.returncode}")
            pg.close()
        b.close()
    if a.sheet:
        sheet(d, banners)


def sheet(d, banners):
    from PIL import Image
    by_lang = {}
    for f in banners:
        lang = f.stem.split("_")[3]
        by_lang.setdefault(lang, []).append(d / "png" / f"{f.stem}.png")
    for lang, files in by_lang.items():
        ims = [Image.open(x) for x in files]
        s = 0.35
        ims = [im.resize((round(im.width * s), round(im.height * s))) for im in ims]
        W = sum(im.width for im in ims) + 30 * (len(ims) + 1)
        H = max(im.height for im in ims) + 60
        out = Image.new("RGB", (W, H), (237, 237, 240))
        x = 30
        for im in ims:
            out.paste(im, (x, 30)); x += im.width + 30
        out.save(d / f"sheet_{lang}.png")
        print("sheet", lang)


if __name__ == "__main__":
    main()
