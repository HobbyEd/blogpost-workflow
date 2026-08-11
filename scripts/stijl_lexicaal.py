#!/usr/bin/env python3
"""Vind de lexicale huisstijl-kandidaten in een blogpost-draft.

De stijl-check had zeven greppatronen in zijn prompt staan. Dat maakte de instructie
groot (ruim 2.500 est. tokens) en de uitkomst modelafhankelijk: bij een lange lijst
zette de agent twijfelgevallen weg als "geen overtreding". Deterministisch zoeken hoort
in code, oordelen bij het model.

Dit script vindt alleen kandidaten. Voor drie categorieen (komma+en, versterkers,
kwantoren) is een menselijk of model-oordeel nodig; die worden als kandidaat gemeld,
niet als overtreding.

Gebruik:
    python3 scripts/stijl_lexicaal.py posts/<slug>/draft.md
"""

import re
import sys

# (sleutel, kop, patroon, harde overtreding?, advies)
PATRONEN = [
    ("emdash", "Gedachtestreep (em/en-dash)", r"[—–]", False,
     "Toegestaan in de reeks-titelregel en in een bullet-leadin. Elders: dubbelepunt, "
     "komma, haakjes of een nieuwe zin."),
    ("uitroep", "Uitroepteken", r"!", False,
     "Markdown-beeldsyntax `![` telt niet. Elk uitroepteken in lopende tekst is fout."),
    ("emoji", "Emoji", "[\U0001F000-\U0001FAFF☀-➿]", True,
     "Verwijderen."),
    ("zwakte", "Zwaktemarkeerder", r"(?i)eerlijk gezegd|om eerlijk te zijn", True,
     "Schrap de markeerder en laat de bewering staan."),
    ("komma_en", "Komma + 'en'", r", en ", False,
     "Overtreding als het deel erna een eigen onderwerp en persoonsvorm heeft. "
     "Bij een oorzakelijk verband: doordat/waardoor/zodat in plaats van een punt."),
    ("versterker", "Versterker zonder inhoud",
     r"(?i)\b(ineens|meteen|precies|feitelijk|eigenlijk|gewoon|daadwerkelijk|echt|"
     r"simpelweg|natuurlijk|uiteraard|overduidelijk)\b", False,
     "Schrappen, tenzij het woord een betekenisverschil maakt dat zonder het woord "
     "verdwijnt."),
    ("kwantor", "Kwantor (claim, vraagt bron)",
     r"(?i)\b(overal|nergens|altijd|nooit|vrijwel nooit|de meeste|het vaakst|zelden|"
     r"iedereen|niemand|voor het eerst|al decennia|in de praktijk blijkt)\b", False,
     "Bron erbij, of vervang door de waarneming die wel te onderbouwen is. Een eigen "
     "observatie mag, mits als zodanig benoemd."),
]

KNIP = 90  # tekens context rond een match


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Gebruik: python3 scripts/stijl_lexicaal.py <draft.md>")
    pad = sys.argv[1]
    try:
        regels = open(pad, encoding="utf-8").read().split("\n")
    except OSError as e:
        raise SystemExit(f"Kan {pad} niet lezen: {e}")

    print(f"Draft: {pad}\n")
    totaal = 0
    for sleutel, kop, patroon, hard, advies in PATRONEN:
        treffers = []
        for i, regel in enumerate(regels, 1):
            for m in re.finditer(patroon, regel):
                if sleutel == "uitroep" and m.start() > 0 and regel[m.start() - 1] == "!":
                    continue
                if sleutel == "uitroep" and regel[m.start():m.start() + 2] == "![":
                    continue
                if sleutel == "emdash" and regel.strip() == "---":
                    continue
                a = max(0, m.start() - KNIP)
                b = min(len(regel), m.end() + KNIP)
                treffers.append((i, ("…" if a else "") + regel[a:b] + ("…" if b < len(regel) else "")))
        totaal += len(treffers)
        merk = "OVERTREDING" if hard else "kandidaat, jouw oordeel"
        print(f"## {kop} — {len(treffers)} ({merk})")
        if not treffers:
            print("   geen\n")
            continue
        for nr, ctx in treffers:
            print(f"   r.{nr}: {ctx}")
        print(f"   Advies: {advies}\n")

    print(f"Totaal aantal kandidaten: {totaal}")
    print("Harde categorieen zijn overtredingen. De rest beoordeel je zelf en rapporteer")
    print("je met je oordeel erbij, ook de niet-overtredingen, met een woord waarom.")


if __name__ == "__main__":
    main()
