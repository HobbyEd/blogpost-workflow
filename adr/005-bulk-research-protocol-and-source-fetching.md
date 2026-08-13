# ADR-005: Bulk Research Protocol & Local Source Fetching Tooling

* **Status**: Accepted
* **Datum**: 2026-08-12
* **Auteurs**: Edwin van Dillen

---

## 1. Context & Probleemstelling

Tijdens het brononderzoek (fase 1) en de factcheck (fase 5b) moeten agents externe webpagina's en academische PDF's inspecteren. Dit stuitte op twee grote knelpunten:
1. **PDF Compressie & Hallucinaties**: WebFetch levert op gecomprimeerde PDF-bestanden onbruikbare tekst ("binary data"), wat leidde tot onopgemerkte fantoomcitaten.
2. **Frictie bij Permissies**: Losse `WebFetch`-verzoeken per domein veroorzaakten continue toestemmingsvragen in de CLI/IDE interface.

---

## 2. Overwogen Alternatieven

1. **Vertrouwen op Standaard WebFetch**: Blijven proberen PDF's via WebFetch te lezen.
   - *Nadeel*: Veroorzaakte aantoonbaar foutieve citaten in productie.
2. **Losse HTTP Verzoeken per Bron**: Agents verzoeken een-voor-een toestemming per domein.
   - *Nadeel*: Veroorzaakt 5 tot 10 irritante prompts per onderzoekssessie.
3. **Bulk Protocol + Deterministisch Python Script + Domain Wildcards (Gekozen)**.

---

## 3. Beslissing

We voeren een drieledige oplossing in voor brononderzoek en factchecking:

1. **`scripts/haal_bron.py` Uitbreiding**:
   Een lokaal Python script dat meervoudige URL's en PDF's (via `pdftotext` / Poppler) in bulk kan ophalen en platte tekst opslaat in `posts/<slug>/bronnen/`.
2. **Bulk Research Protocol in Agents**:
   `blogpost-onderzoeker` en `bron-check` worden geïnstrueerd om eerst kandidaat-URL's te verzamelen en daarna in **één gebundelde Python-stap** op te halen.
3. **Domain Wildcards**:
   Permissieregel `"WebFetch(domain:*)"` in `.claude/settings.local.json` zodat bezochte bronnen automatisch worden goedgekeurd zonder prompts.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - Nul frictie door herhaalde toestemmingsvragen.
  - 100% betrouwbare PDF-tekstverwerking via `pdftotext`.
  - Alle geraadpleegde bronnen worden lokaal transparant gearchiveerd.
* **Negatief (-)**:
  - Vereist lokale installatie van `poppler` (`pdftotext`) op het systeem.
