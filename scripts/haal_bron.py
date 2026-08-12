#!/usr/bin/env python3
"""Haal een of meerdere bronnen op als platte tekst, zodat je er letterlijk in kunt zoeken.

Aanleiding: deel 1 van de intentie-reeks kwam live te staan met een citaat dat in de
aangehaalde paper niet voorkomt. WebFetch gaf op beide PDF's onbruikbare uitvoer ("the
content appears as compressed binary data"), waarna het citaat ongecontroleerd bleef. Met
pdftotext was de zin in één opdracht te weerleggen.

Dit script haalt een of meerdere URL's op, zet PDF om naar tekst, zoekt optioneel naar
een zin en kan bronnen in bulk opslaan.

Gebruik:
    python3 scripts/haal_bron.py <url1> [<url2> ...]
    python3 scripts/haal_bron.py <url> --zoek "letterlijke zin uit de blogpost"
    python3 scripts/haal_bron.py <url1> <url2> --out-dir posts/<slug>/bronnen/

Exitcodes:
    0  opgehaald (en bij --zoek: gevonden)
    1  ophalen of omzetten mislukt
    3  opgehaald maar de gezochte zin komt er NIET in voor
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

UA = "Mozilla/5.0 (compatible; blogpost-bron-check/1.0)"


def haal_op(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read(), r.headers.get("Content-Type", "")


def naar_tekst(ruw: bytes, content_type: str, url: str) -> str:
    is_pdf = "pdf" in content_type.lower() or url.lower().endswith(".pdf") or ruw[:5] == b"%PDF-"
    if is_pdf:
        if not shutil.which("pdftotext"):
            raise SystemExit(
                "Dit is een PDF en pdftotext ontbreekt. Installeer poppler "
                "(brew install poppler) of gebruik een HTML-vindplaats."
            )
        with tempfile.TemporaryDirectory() as d:
            pdf = os.path.join(d, "bron.pdf")
            txt = os.path.join(d, "bron.txt")
            with open(pdf, "wb") as f:
                f.write(ruw)
            subprocess.run(["pdftotext", "-q", pdf, txt], check=True)
            with open(txt, encoding="utf-8", errors="replace") as f:
                return f.read()
    tekst = ruw.decode("utf-8", errors="replace")
    tekst = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", tekst)
    tekst = re.sub(r"(?s)<[^>]+>", " ", tekst)
    return re.sub(r"[ \t]+", " ", tekst)


def normaliseer(t: str) -> str:
    """Regelafbrekingen en typografische aanhalingstekens onschadelijk maken."""
    t = t.replace("‘", "'").replace("’", "'")
    t = t.replace("“", '"').replace("”", '"')
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"-\s*\n\s*", "", t)
    return re.sub(r"\s+", " ", t).lower()


def verwerk_enkele_url(url: str, args: argparse.Namespace, out_dir: str | None = None, idx: int = 1) -> int:
    try:
        ruw, ct = haal_op(url)
    except Exception as e:
        print(f"OPHALEN MISLUKT: {url}\n  {e}", file=sys.stderr)
        return 1

    try:
        tekst = naar_tekst(ruw, ct, url)
    except subprocess.CalledProcessError as e:
        print(f"OMZETTEN MISLUKT ({url}): {e}", file=sys.stderr)
        return 1

    print(f"\n--- Bron [{idx}]: {url} ---")
    print(f"Type: {ct or 'onbekend'} | {len(tekst)} tekens tekst")

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        fname = f"bron_{idx}.txt"
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\nType: {ct}\n\n" + tekst)
        print(f"Opgeslagen naar: {fpath}")

    if args.dump:
        print(tekst)
        return 0

    if not args.zoek:
        print(tekst[:1500])
        print("\n(eerste 1500 tekens getoond)")
        return 0

    hooi, naald = normaliseer(tekst), normaliseer(args.zoek)
    if naald in hooi:
        i = hooi.find(naald)
        marge = 200 * max(1, args.context)
        print("GEVONDEN. Context:\n")
        print("…" + hooi[max(0, i - marge): i + len(naald) + marge] + "…")
        return 0

    print("NIET GEVONDEN in deze bron.\n")
    woorden = [w for w in re.findall(r"[a-z]{5,}", naald)][:6]
    if woorden:
        print("Losse kernwoorden uit de gezochte zin:")
        for w in woorden:
            n = hooi.count(w)
            print(f"  {w}: {n}x")
        zwaarste = max(woorden, key=lambda w: hooi.count(w))
        if hooi.count(zwaarste):
            j = hooi.find(zwaarste)
            print(f"\nOmgeving van '{zwaarste}':\n…{hooi[max(0, j - 250): j + 250]}…")
    return 3


def main() -> int:
    ap = argparse.ArgumentParser(description="Haal een of meerdere bronnen op als platte tekst.")
    ap.add_argument("urls", nargs="+", help="Een of meerdere URL's van bronnen om op te halen")
    ap.add_argument("--zoek", help="letterlijke zin die in de bron moet voorkomen")
    ap.add_argument("--context", type=int, default=2, help="aantal zinnen context rond een treffer (standaard 2)")
    ap.add_argument("--dump", action="store_true", help="print de volledige tekst")
    ap.add_argument("--out-dir", help="Map waarin de bronnen opgeslagen moeten worden")
    args = ap.parse_args()

    exit_codes = []
    for i, url in enumerate(args.urls, start=1):
        code = verwerk_enkele_url(url, args, out_dir=args.out_dir, idx=i)
        exit_codes.append(code)

    if any(c == 1 for c in exit_codes):
        return 1
    if any(c == 3 for c in exit_codes):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
