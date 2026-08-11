#!/usr/bin/env python3
"""Haal een bron op als platte tekst, zodat je er letterlijk in kunt zoeken.

Aanleiding: deel 1 van de intentie-reeks kwam live te staan met een citaat dat in de
aangehaalde paper niet voorkomt. WebFetch gaf op beide PDF's onbruikbare uitvoer ("the
content appears as compressed binary data"), waarna het citaat ongecontroleerd bleef. Met
pdftotext was de zin in één opdracht te weerleggen.

Dit script haalt een URL op, zet PDF om naar tekst, en zoekt optioneel naar een zin.

Gebruik:
    python3 scripts/haal_bron.py <url>
    python3 scripts/haal_bron.py <url> --zoek "letterlijke zin uit de blogpost"
    python3 scripts/haal_bron.py <url> --zoek "zin" --context 3

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
    """Regelafbrekingen en typografische aanhalingstekens onschadelijk maken.

    In een PDF staat een zin vaak over twee regels, soms met een afbreekstreepje. Zonder
    deze normalisatie mist een letterlijke zoekopdracht die zin en meld je ten onrechte
    dat een citaat niet bestaat.
    """
    t = t.replace("‘", "'").replace("’", "'")
    t = t.replace("“", '"').replace("”", '"')
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"-\s*\n\s*", "", t)
    return re.sub(r"\s+", " ", t).lower()


def main() -> int:
    ap = argparse.ArgumentParser(description="Haal een bron op als platte tekst.")
    ap.add_argument("url")
    ap.add_argument("--zoek", help="letterlijke zin die in de bron moet voorkomen")
    ap.add_argument("--context", type=int, default=2,
                    help="aantal zinnen context rond een treffer (standaard 2)")
    ap.add_argument("--dump", action="store_true", help="print de volledige tekst")
    args = ap.parse_args()

    try:
        ruw, ct = haal_op(args.url)
    except Exception as e:
        print(f"OPHALEN MISLUKT: {args.url}\n  {e}", file=sys.stderr)
        return 1
    try:
        tekst = naar_tekst(ruw, ct, args.url)
    except subprocess.CalledProcessError as e:
        print(f"OMZETTEN MISLUKT: {e}", file=sys.stderr)
        return 1

    print(f"Bron: {args.url}")
    print(f"Type: {ct or 'onbekend'} | {len(tekst)} tekens tekst\n")

    if args.dump:
        print(tekst)
        return 0

    if not args.zoek:
        print(tekst[:2000])
        print("\n(eerste 2000 tekens; gebruik --zoek of --dump)")
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
        print("Losse kernwoorden uit de gezochte zin, om te zien of er een variant staat:")
        for w in woorden:
            n = hooi.count(w)
            print(f"  {w}: {n}x")
        zwaarste = max(woorden, key=lambda w: hooi.count(w))
        if hooi.count(zwaarste):
            j = hooi.find(zwaarste)
            print(f"\nOmgeving van '{zwaarste}':\n…{hooi[max(0, j - 250): j + 250]}…")
    print("\nConclusie: het citaat staat niet letterlijk in deze bron. Zoek de echte")
    print("vindplaats of vervang het citaat door een formulering die er wel in staat.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
