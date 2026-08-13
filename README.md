# Blogpost Workflow

Een hybride, deterministisch en agentisch systeem voor het gestructureerd, versneld en kwalitatief hoogwaardig schrijven van vakinhoudelijke blogposts.

De workflow scheidt de **Control Plane** (strikte fasevolgorde, status en poortbewaking in Python-code) van de **Content Plane** (creatieve analyse, schrijven en oordeelsvorming door gespecialiseerde LLM-subagents). Dit garandeert dat het proces nooit hallucineert over de status, terwijl de auteur (Edwin) via strategische **mens-gates** de volledige redactionele controle behoudt.

---

## 🎯 Doel van de Blogpost Workflow

Het doel van deze workflow is het ondersteunen van de auteur als een betrouwbare *co-pilot*:
- **Elimineren van mechanisch werk**: Automatische SVG-rendering naar PNG via Headless Chrome, geautomatiseerde stijl- en leesbaarheidscontroles, en het compileren van markdown naar WordPress Gutenberg-blokken.
- **Verhogen van de inhoudelijke scherpte**: Inzet van een kritische Grok-persona voor tegenspraak, bron- & feitenchecks van citaten tegen de originele PDF-/webdocumenten, en reeks-consistentiecontroles.
- **Borgen van de menselijke stem**: Drie onafzetbare **harde gates** (Synthese, Factcheck, Deploy) zorgen ervoor dat inhoudelijke en redactionele keuzes altijd expliciet door de mens worden goedgekeurd.

---

## 🏗️ Architectuur & Agent-keten

Het systeem bestaat uit twee lagen:

### 1. Control Plane (Deterministische state machine)
* **`scripts/orchestrate.py`**: Strikte Python CLI State Machine. Houdt de status bij in `posts/<slug>/state.json` (de enige machinale bron van waarheid) en blokkeert illegale fase-overgangen.
* **`scripts/deploy_post.py`**: Zet markdown om naar Gutenberg blok-markup en uploadt concepten via de WordPress REST API.
* **`scripts/render_svg.py`**: Rendert SVG-diagrammen naar Retina PNG's via Headless Chrome.
* **`scripts/haal_bron.py`**: Extraheert tekst uit webpagina's en PDF's t.b.v. de feitencheck.
* **`scripts/leesbaarheid.py` & `scripts/stijl_lexicaal.py`**: Berekenen leesbaarheidsindices en lexicale regels.

### 2. Content Plane (Gespecialiseerde Subagents)
* 🧠 **`blogpost-onderzoeker` (Claude Opus)**: Verkent de context, verrijkt het onderwerp met bronnen en stelt de `outline.md` op. Weegt in Fase 4 ook de Grok-kritiek af voor `synthese.md`.
* ✍️ **`blogpost-schrijver` (Claude Sonnet)**: Vertaalt de goedgekeurde outline naar een lopende draft (`draft.md`) in de authentieke huisstijl.
* 🔍 **`stijl-check` & `leesbaarheid-check` (Claude Haiku / Grep / Python)**: Geautomatiseerde dubbele kwaliteitscontrole op superlatieven, zinslengte, ritme en houterigheid.
* 📚 **`reeks-consistentie-check` (Claude Haiku)**: Toetst titel-overlap, terminologie en onderlinge verwijzingen binnen de reeks.
* 🤖 **`grok-reviewer` (xAI Grok-4.3 via MCP)**: Legt het concept voor aan een kritische persona voor scherpe inhoudelijke tegenspraak (`grok-feedback.md`).
* 🎨 **`blogpost-visuals` (Claude Sonnet)**: Ontwerpt spaarzame SVG-diagrammen in het huisstijl-palet.
* 🛡️ **`bron-check` (Claude Haiku / Sonnet)**: Verifieert citaten en bewerende claims tegen de originele brondocumenten (`feitencheck.md`).
* 🚀 **`blogpost-deploy` (Claude Haiku)**: Aanroeper van het deploy-script na expliciet akkoord (`approve --deploy`).

---

## 🔄 Functionele Workflow (Stap-voor-stap)

| Fase | Naam | Type & Model | Uitvoerder / Script | Tussenartefact | Gate Type |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **0** | **Intake** | Deterministisch (Opus) | `scripts/orchestrate.py init` | `state.json` + `state.md` | Menselijke Gate |
| **1** | **Outline & verrijking** | Agentisch (Opus) | `blogpost-onderzoeker` | `outline.md` | Menselijke Gate |
| **2** | **Draft schrijven** | Agentisch (Sonnet) | `blogpost-schrijver` | `draft.md` | Menselijke Gate |
| **2b** | **Stijl & Leesbaarheid** | Agentisch / Code (Haiku) | `stijl-check` + `leesbaarheid-check` | 2x rapport in beslislog | Menselijke Gate |
| **2c** | **Reeks-consistentie** | Agentisch (Haiku) | `reeks-consistentie-check` | rapport in beslislog | Menselijke Gate |
| **3** | **Kritiek (Grok)** | Agentisch (Grok-4.3 MCP) | `grok-reviewer` | `grok-feedback.md` | Menselijke Gate (uitstelbaar) |
| **4** | **Synthese** | Agentisch (Opus) | `blogpost-onderzoeker` | `synthese.md` | 🔴 **HARDE GATE** |
| **5** | **Visuals** | Agentisch (Sonnet) | `blogpost-visuals` + `render_svg.py` | `visuals/*.svg` + `.png` | Menselijke Gate |
| **5b** | **Bron- & Feitencheck** | Agentisch (Haiku/Sonnet) | `bron-check` + `haal_bron.py` | `feitencheck.md` | 🔴 **HARDE GATE** |
| **★** | **Post-synthese Herkeuring** | Code / Agentisch | `stijl-check` + `leesbaarheid-check` | herkeuringsrapport | Interne Hercontrole |
| **6** | **Deploy (concept)** | Deterministisch (Haiku) | `blogpost-deploy` + `deploy_post.py` | WP Concept ID & Edit URL | 🔴 **HARDE GATE** |

> [!IMPORTANT]
> **Drie Harde Gates (altijd menselijk akkoord):** Fasen **4 (Synthese)**, **5b (Feitencheck)** en **6 (Deploy)** zijn harde veiligheidspoorten. Zelfs in `yolo_mode: true` stopt de CLI hier altijd voor expliciet menselijk akkoord.

---

## 💻 Benodigdheden & Vereisten

Om de blogpost workflow uit te voeren heb je het volgende nodig:

1. **Host Engine / AI-Client**:
   - **Anthropic Claude Code CLI** (`claude`) OF
   - **Google Antigravity CLI** (`agy`) / Gemini Host Engine OF
   - **Grok-Builder** (Agent Client Protocol).
2. **xAI / Grok Account**:
   - Een geldige xAI API Key voor **Grok-4.3** is vereist voor Fase 3 (Kritiek via de lokale MCP server `.claude/mcp/grok_review_server.py`).
3. **WordPress Omgeving & Credentials**:
   - Een WordPress-installatie met REST API toegang.
   - Een **Application Wachtwoord** (gegenereerd in WordPress via `wp-admin` &rarr; *Gebruikers* &rarr; *Profiel* &rarr; *Applicatiewachtwoorden*).
4. **Python 3.9+**:
   - Standaard Python-omgeving voor het uitvoeren van `scripts/orchestrate.py` en hulpscripts.

---

## ⚙️ Omgevingsconfiguratie (`.env`)

Geheimen en omgevingsspecifieke variabelen worden opgeslagen in een lokaal `.env` bestand (dat ge-ignored wordt door Git).

### 1. Maak een lokaal `.env` bestand aan:
Kopieer het meegeleverde sjabloonbestand:
```bash
cp .env_template .env
```

### 2. Vul de variabelen in in `.env`:
```env
# Grok / xAI API Configuration
GROK_API_KEY=xai-your-api-key-here
GROK_MODEL=grok-4.3

# WordPress Configuration & Credentials
WP_SITE_URL=https://edwinvandillen.nl
WP_USERNAME=edwin
WP_APPLICATION_TOKEN=abcd efgh ijkl mnop
```

---

## 🚀 Gebruik & CLI Commando's

De workflow wordt aangestuurd via de `orchestrate.py` CLI:

### Nieuwe post starten (Intake):
```bash
python3 scripts/orchestrate.py init --slug mijn-nieuwe-post --title "Mijn Werktitel"
```

### Status opvragen:
```bash
python3 scripts/orchestrate.py status --post-dir posts/mijn-nieuwe-post
python3 scripts/orchestrate.py table --post-dir posts/mijn-nieuwe-post
```

### Volgende toegestane actie opvragen:
```bash
python3 scripts/orchestrate.py next --post-dir posts/mijn-nieuwe-post
```

### Fase uitvoeren of goedkeuren:
```bash
python3 scripts/orchestrate.py run outline --post-dir posts/mijn-nieuwe-post
python3 scripts/orchestrate.py approve --post-dir posts/mijn-nieuwe-post
python3 scripts/orchestrate.py approve --deploy --post-dir posts/mijn-nieuwe-post
```

---

## 🏛️ Architectuur & Architectural Decision Records (ADR)

Alle architectuurbesluiten, het visiedocument en de ontwerpkeuzes zijn vastgelegd in de [`adr/`](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/README.md) map:

- 📄 [`adr/00-overall-design-blogpost-webui.md`](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/00-overall-design-blogpost-webui.md): Het overkoepelende ontwerpdocument (Web UI, 3-laags architectuur, Socratische Chat & Stepper Executie).
- 📋 [`adr/README.md`](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/README.md): Index van alle individuele ADR's (ADR-001 t/m ADR-008).

---

## 📖 Visuele Documentatie

Zie [opzet_blogpost_workflow.html](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/opzet_blogpost_workflow.html) voor het volledige, interactieve visuele dashboard met uitgebreide toelichtingen per fase, de directory opbouw en reflectie op de executie-engine.

