#!/usr/bin/env python3
"""Render een SVG naar een scherpe PNG via headless Chrome.

Deterministische render-stap van de blogpost-workflow (fase 5). Wikkelt de SVG in een
HTML-wrapper en maakt een screenshot op 2x scale. Lost de bekende gotcha's op: gebruikt
altijd absolute paden (relatieve paden falen op Windows door spaties/haakjes in de
mapnaam) en verifieert dat de PNG een reële grootte heeft.

Alleen de Python-standaardlibrary.

Gebruik:
    python scripts/render_svg.py --svg posts/<slug>/visuals/naam.svg
        [--out ...png] [--width 960 --height 640] [--scale 2] [--chrome <pad>]

Zonder --width/--height leidt het script de afmetingen af uit de SVG (viewBox of
width/height). Zonder --out schrijft het naast de SVG een gelijknamige .png.
"""

import argparse
import os
import re
import subprocess
import sys

CHROME_CANDIDATES = [
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    # Linux
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_chrome(explicit):
    if explicit:
        return explicit
    env = os.environ.get("CHROME")
    if env and os.path.isfile(env):
        return env
    for c in CHROME_CANDIDATES:
        if os.path.isfile(c):
            return c
    raise RuntimeError("Chrome niet gevonden. Geef --chrome <pad> of zet $CHROME.")


def svg_dimensions(svg_text):
    """Leid breedte/hoogte af uit width/height of viewBox. Default 960x640."""
    w = re.search(r'\bwidth="([\d.]+)', svg_text)
    h = re.search(r'\bheight="([\d.]+)', svg_text)
    if w and h:
        return round(float(w.group(1))), round(float(h.group(1)))
    vb = re.search(r'viewBox="[\d.\s]*?([\d.]+)\s+([\d.]+)"', svg_text)
    if vb:
        return round(float(vb.group(1))), round(float(vb.group(2)))
    return 960, 640


def main():
    ap = argparse.ArgumentParser(description="Render SVG naar PNG via headless Chrome.")
    ap.add_argument("--svg", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--chrome", default=None)
    args = ap.parse_args()

    svg_path = os.path.abspath(args.svg)
    if not os.path.isfile(svg_path):
        print(f"FOUT: SVG niet gevonden: {svg_path}", file=sys.stderr)
        sys.exit(1)
    out_path = os.path.abspath(args.out) if args.out else os.path.splitext(svg_path)[0] + ".png"

    svg_text = open(svg_path, encoding="utf-8").read()
    w = args.width or svg_dimensions(svg_text)[0]
    h = args.height or svg_dimensions(svg_text)[1]

    # HTML-wrapper met de SVG inline; nul marge zodat de screenshot strak sluit.
    html_path = os.path.splitext(svg_path)[0] + ".src.html"
    wrapper = ("<!doctype html><html><head><meta charset='utf-8'>"
               "<style>*{margin:0;padding:0}html,body{background:transparent}</style>"
               f"</head><body>{svg_text}</body></html>")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(wrapper)

    chrome = find_chrome(args.chrome)
    file_url = "file:///" + html_path.replace("\\", "/")
    cmd = [
        chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
        f"--force-device-scale-factor={args.scale}",
        f"--window-size={w},{h}",
        "--virtual-time-budget=4000",
        f"--screenshot={out_path}",
        file_url,
    ]
    subprocess.run(cmd, check=False, capture_output=True)

    if not os.path.isfile(out_path) or os.path.getsize(out_path) < 1000:
        print(f"FOUT: render leverde geen bruikbare PNG op ({out_path}).", file=sys.stderr)
        sys.exit(2)

    size = os.path.getsize(out_path)
    print(f"OK: {out_path} ({size} bytes, bron {w}x{h} @ {args.scale}x = "
          f"{round(w*args.scale)}x{round(h*args.scale)}px)")
    print("Let op: controleer de PNG ook visueel; een render-fout geeft geen exitcode "
          "maar wel een onvolledig beeld (bv. een SVG-gradient met objectBoundingBox "
          "op een horizontale lijn rendert blanco — gebruik userSpaceOnUse).")


if __name__ == "__main__":
    main()
