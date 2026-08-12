#!/usr/bin/env python3
"""Meet de leesbaarheidsmaten van een blogpost-draft.

Vergelijkt zinslengte, spreiding en voegwoorddichtheid met de gepubliceerde delen van
de anatomie-reeks. Die reeks is de referentie omdat Edwin die zelf heeft geredigeerd en
gepubliceerd; de bandbreedte ervan is dus per definitie "goed genoeg".

Aanleiding: na een correctieronde op feitelijkheid zakte deel 1 van de intentie-reeks
naar 14,7 woorden per zin met 48% korte zinnen. De stijl-check zag dat niet, want die
telt alleen overtredingen. Dit script maakt het zichtbaar.

Gebruik:
    python3 scripts/leesbaarheid.py posts/<slug>/draft.md
"""

import glob
import json
import os
import re
import statistics
import sys

ONDERSCHIKKEND = (
    r"\b(doordat|waardoor|zodat|terwijl|omdat|hoewel|zolang|voordat|nadat|tenzij|mits|zoals)\b"
)

# Zinsgrens: punt/vraagteken/uitroepteken, eventueel gevolgd door een sluitend
# aanhalingsteken of haakje, dan witruimte. Zonder die sluittekens plakte een citaat dat
# op `..."` eindigt aan de volgende zin vast, waardoor twee zinnen van 52 woorden als een
# van 124 werden geteld. Dat maakte de spreiding kunstmatig hoog bij citaatrijke posts.
ZINSGRENS = r"(?<=[.!?])[\"'\u201d\u2019)\]]*\s+"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENTIE_GLOB = os.path.join(REPO, "posts", "anatomie-agents-*", "draft.md")

# De referentieposts staan onder posts/ en dat is bewust niet geversioneerd. Zonder
# vangnet verliest dit script zijn norm zodra die drafts er niet zijn, en drukt het
# stilzwijgend alleen ruwe maten af. Daarom staat de band ook bevroren in git.
BAND_BESTAND = os.path.join(REPO, "reference", "leesbaarheid-band.json")


def leesbare_tekst(pad):
    """Strip alles wat geen lopende tekst is: koppen, tabellen, visuals, bronnen."""
    t = open(pad, encoding="utf-8").read()
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)          # image refs
    t = re.sub(r"\*\(bron:.*?\)\*", "", t, flags=re.S)   # bronvermeldingen
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)       # links -> linktekst
    regels = [
        r for r in t.split("\n")
        if r.strip() and not r.lstrip().startswith(("#", "|", ">", "---", "```"))
    ]
    return "\n".join(regels)


def maten(pad):
    t = leesbare_tekst(pad)
    zinnen = [z.strip() for z in re.split(ZINSGRENS, t) if len(z.strip()) > 3]
    lengtes = [len(z.split()) for z in zinnen]
    if not lengtes:
        raise SystemExit(f"Geen lopende tekst gevonden in {pad}")
    woorden = len(t.split())
    return {
        "n": len(lengtes),
        "gem": statistics.mean(lengtes),
        "sd": statistics.pstdev(lengtes),
        "pct_lang": 100 * sum(1 for x in lengtes if x >= 25) / len(lengtes),
        "pct_kort": 100 * sum(1 for x in lengtes if x <= 12) / len(lengtes),
        "onder": 1000 * len(re.findall(ONDERSCHIKKEND, t, re.I)) / woorden,
    }


def bevroren_band():
    """Lees de in git vastgelegde band. Geeft (band, herkomst) of (None, None)."""
    if not os.path.exists(BAND_BESTAND):
        return None, None
    try:
        with open(BAND_BESTAND, encoding="utf-8") as f:
            d = json.load(f)
        band = {k: (v[0], v[1]) for k, v in d["band"].items()}
        return band, f"bevroren band uit {os.path.basename(BAND_BESTAND)}"
    except (OSError, ValueError, KeyError, TypeError):
        return None, None


def referentieband():
    """Bereken de band uit de referentieposts; val terug op de bevroren band."""
    paden = sorted(glob.glob(REFERENTIE_GLOB))
    if paden:
        alle = [maten(p) for p in paden]
        band = {k: (min(m[k] for m in alle), max(m[k] for m in alle)) for k in alle[0]}
        return band, f"{len(paden)} gepubliceerde delen van de anatomie-reeks"
    band, herkomst = bevroren_band()
    return band, herkomst


def oordeel(waarde, lo, hi, hoger_is_beter=True):
    if lo <= waarde <= hi:
        return "binnen band"
    if waarde < lo:
        return "TE LAAG" if hoger_is_beter else "onder band (ok)"
    return "boven band" if hoger_is_beter else "TE HOOG"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Gebruik: python3 scripts/leesbaarheid.py <draft.md>")
    pad = sys.argv[1]
    if not os.path.exists(pad):
        raise SystemExit(f"Bestand niet gevonden: {pad}")

    m = maten(pad)
    band, herkomst = referentieband()

    print(f"Draft: {pad}")
    print(f"Zinnen: {m['n']}\n")

    if not band:
        print("WAARSCHUWING: geen referentieband beschikbaar. Noch de posts onder")
        print(f"posts/anatomie-agents-*/ noch {BAND_BESTAND} zijn leesbaar.")
        print("Er volgt geen oordeel, alleen ruwe maten.\n")
        rijen = [
            ("Gemiddelde zinslengte", f"{m['gem']:.1f}", "", ""),
            ("Standaarddeviatie", f"{m['sd']:.1f}", "", ""),
            ("Zinnen >= 25 woorden", f"{m['pct_lang']:.0f}%", "", ""),
            ("Zinnen <= 12 woorden", f"{m['pct_kort']:.0f}%", "", ""),
            ("Onderschikkend /1000w", f"{m['onder']:.1f}", "", ""),
        ]
    else:
        rijen = [
            ("Gemiddelde zinslengte", f"{m['gem']:.1f}",
             f"{band['gem'][0]:.1f} - {band['gem'][1]:.1f}",
             oordeel(m["gem"], *band["gem"])),
            ("Standaarddeviatie", f"{m['sd']:.1f}",
             f"{band['sd'][0]:.1f} - {band['sd'][1]:.1f}",
             oordeel(m["sd"], *band["sd"])),
            ("Zinnen >= 25 woorden", f"{m['pct_lang']:.0f}%",
             f"{band['pct_lang'][0]:.0f}% - {band['pct_lang'][1]:.0f}%",
             oordeel(m["pct_lang"], *band["pct_lang"])),
            ("Zinnen <= 12 woorden", f"{m['pct_kort']:.0f}%",
             f"{band['pct_kort'][0]:.0f}% - {band['pct_kort'][1]:.0f}%",
             oordeel(m["pct_kort"], *band["pct_kort"], hoger_is_beter=False)),
            ("Onderschikkend /1000w", f"{m['onder']:.1f}",
             f"{band['onder'][0]:.1f} - {band['onder'][1]:.1f}",
             oordeel(m["onder"], *band["onder"])),
        ]

    breedtes = [max(len(str(r[i])) for r in rijen + [("Maat", "draft", "reeks", "oordeel")])
                for i in range(4)]
    kop = ("Maat", "draft", "anatomie-reeks", "oordeel")
    breedtes = [max(breedtes[i], len(kop[i])) for i in range(4)]
    fmt = "  ".join("{:<%d}" % b for b in breedtes)
    print(fmt.format(*kop))
    print("  ".join("-" * b for b in breedtes))
    for r in rijen:
        print(fmt.format(*r))

    if band:
        print(f"\nReferentie: {herkomst}.")
        print("TE LAAG bij zinslengte, spreiding, lange zinnen of voegwoorden betekent:")
        print("de tekst is opsommerig geworden. Herschrijven, niet patchen.")


if __name__ == "__main__":
    main()
