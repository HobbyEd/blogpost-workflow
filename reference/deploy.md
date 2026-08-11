# Deploy naar edwinvandillen.nl (in-repo procedure)

Zelfstandige deploy-instructie voor de blogpost-workflow. De credentials staan **niet**
in dit bestand: de instellingen komen uit `.env` in de repo-root als `WP_APPLICATION_TOKEN`,
`WP_USERNAME` en `WP_SITE_URL`.

## De deploy loopt via een script — niet via ad-hoc code

De feitelijke deploy is een deterministisch script: **`scripts/deploy_post.py`**. Dat
zet de draft om naar **Gutenberg blok-markup** (niet klassieke HTML — anders moet de
post in wp-admin met de hand naar blokken worden omgezet), uploadt de visuals als media
en maakt of werkt de concept-post bij. Roep het script aan; schrijf geen eigen
conversie- of upload-code:

```bash
python scripts/deploy_post.py --post-dir posts/<slug>          # nieuw concept
python scripts/deploy_post.py --post-dir posts/<slug> --post-id <id>   # bestaand bijwerken
python scripts/deploy_post.py --post-dir posts/<slug> --dry-run        # alleen converteren + printen
```

Het script zet de post **altijd** op `status: draft` en heeft geen publiceer-optie.
Live zetten doet Edwin in wp-admin. De SVG→PNG-render loopt via het zusterscript
`scripts/render_svg.py`.

De rest van dit document is de referentie voor wat die scripts onder de motorkap doen
(REST-route, auth, block-vocabulaire) — nuttig bij onderhoud, maar je hoeft het niet
met de hand uit te voeren.

## Credentials laden

Lees `WP_APPLICATION_TOKEN` en `WP_USERNAME` uit `.env` (repo-root). Bouw de Basic-auth-header:

```bash
USER="$(grep -i '^WP_USERNAME' .env | sed "s/.*=[[:space:]]*//; s/['\"]//g" | tr -d '[:space:]')"
TOKEN="$(grep -i '^WP_APPLICATION_TOKEN' .env | sed "s/.*=[[:space:]]*//; s/['\"]//g")"
# USER fallback op 'edwin' indien afwezig
AUTH="$(printf '%s' "${USER:-edwin}:${TOKEN}" | base64)"
```

Let op: het token in `.env` kan spaties bevatten (`WP_APPLICATION_TOKEN`). WordPress accepteert het
applicatiewachtwoord met of zonder de spaties erin; codeer `<gebruikersnaam>:<token>` als Basic-auth.

## REST API route

WordPress op deze site reageert **niet** op `/wp-json/wp/v2/...` (geeft HTML terug).
Gebruik altijd de `?rest_route=`-variant:

```
BASE="https://edwinvandillen.nl/?rest_route=/wp/v2"
```

## Auth testen

```bash
curl -s -H "Authorization: Basic ${AUTH}" \
  "https://edwinvandillen.nl/?rest_route=/wp/v2/users/me"
```

## Afbeelding uploaden (SVG is geblokkeerd — upload PNG)

```bash
curl -s -X POST "https://edwinvandillen.nl/?rest_route=/wp/v2/media" \
  -H "Authorization: Basic ${AUTH}" \
  -H "Content-Disposition: attachment; filename=\"bestandsnaam.png\"" \
  -H "Content-Type: image/png" \
  --data-binary @"pad/naar/bestand.png"
```

De respons bevat `id` (media-id) en `source_url` (de URL om in de HTML te gebruiken).

## SVG → PNG (rsvg-convert ontbreekt op Windows → headless Chrome)

Wikkel de SVG in een klein HTML-bestand en render met headless Chrome op 2× scale:

```powershell
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
& $chrome --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=2 `
  "--window-size=960,640" --virtual-time-budget=4000 `
  --screenshot="visuals/naam.png" "file:///<absoluut-pad>/naam.src.html"
```

`--force-device-scale-factor=2` levert een 2× scherpe PNG (ruim boven de 1560px die
WordPress prettig vindt). De `--window-size` moet als één token met de komma erin.

**Gotcha's (bevestigd in de Fase C-testrun, 13 juli 2026):**
- **Gebruik absolute Windows-paden** voor zowel `--screenshot` als de `file:///`-URL.
  Relatieve paden falen op deze omgeving met "The system cannot find the path
  specified", door de spaties en haakjes in de mapnaam (`My Drive (edwinvandillen@…)`).
- **Controleer de PNG visueel, niet alleen op bestandsgrootte.** Een render-fout geeft
  geen foutmelding maar wel een onvolledig beeld.
- **SVG-gradient op een horizontale lijn:** een `linearGradient` met het impliciete
  `gradientUnits="objectBoundingBox"` op een volledig horizontale `<line>` (bounding-box
  hoogte 0) rendert blanco in Chrome. Gebruik `gradientUnits="userSpaceOnUse"` met
  expliciete coördinaten.

## Post aanmaken als concept

```python
import json, urllib.request, base64, re, os

# token en username uit .env of os.environ
username = os.environ.get("WP_USERNAME", "edwin")
token = os.environ.get("WP_APPLICATION_TOKEN", "")
if not token and os.path.exists(".env"):
    for line in open(".env", encoding="utf-8"):
        if line.strip().startswith("WP_APPLICATION_TOKEN="):
            token = line.split("=", 1)[1].strip().strip("'").strip('"')

auth = base64.b64encode(f"{username}:{token}".encode()).decode()

url = "https://edwinvandillen.nl/?rest_route=/wp/v2/posts"
payload = json.dumps({
    "title":   "Titel van de post",
    "content": "<p>HTML inhoud...</p>",
    "status":  "draft",          # ALTIJD draft; nooit "publish"
    "excerpt": "Korte samenvatting...",
    "featured_media": 0,
}).encode()

req = urllib.request.Request(url, data=payload,
    headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    d = json.loads(r.read())
    print("ID:", d["id"])
    print("Edit:", f"https://edwinvandillen.nl/wp-admin/post.php?post={d['id']}&action=edit")
```

Een bestaande concept-post bijwerken: vervang `POST` door `method="PUT"` en voeg het
post-id toe aan de URL (`.../wp/v2/posts/{POST_ID}`).

## Markdown → Gutenberg-blokken (wat het script produceert)

De post-content moet **blok-markup** zijn, geen klassieke HTML. Elk blok is HTML tussen
`<!-- wp:TYPE -->` en `<!-- /wp:TYPE -->`, blokken gescheiden door een lege regel. Dit
is het vocabulaire dat `deploy_post.py` uitspuugt, gemodelleerd op de bestaande live
posts:

- **Titel** (`# ...`, eerste regel) → de post-`title`, niet in de body.
- **Kop** (`## ` / `### `) → `<!-- wp:heading -->` met `<hN class="wp-block-heading">`
  (voor h3+ met `{"level":N}`).
- **Alinea** → `<!-- wp:paragraph --><p>…</p><!-- /wp:paragraph -->`.
- **Scheiding** (`---`) → `<!-- wp:separator --><hr class="wp-block-separator has-alpha-channel-opacity"/><!-- /wp:separator -->`.
- **Lijst** (`- ` of `1. `) → `<!-- wp:list -->` (met `{"ordered":true}` voor genummerd),
  `<ul|ol class="wp-block-list">`, elk item `<!-- wp:list-item --><li>…</li><!-- /wp:list-item -->`.
- **Tabel** (`| … |`) → `<!-- wp:table --><figure class="wp-block-table"><table class="has-fixed-layout"><thead>…<tbody>…</table></figure><!-- /wp:table -->`.
- **Afbeelding** (`![alt](visuals/x.png)`) → `<!-- wp:image {"id":N,"sizeSlug":"large",…} --><figure class="wp-block-image size-large"><img src="MEDIA-URL" alt="alt"/></figure><!-- /wp:image -->`,
  met de **geüploade WordPress media-URL**.
- **Blockquote** (`> tekst`) → `<!-- wp:quote --><blockquote class="wp-block-quote"><p>…</p></blockquote><!-- /wp:quote -->` (inline-opmaak blijft gelden).
- **Codeblok** (```` ``` ```` … ```` ``` ````) → `<!-- wp:code --><pre class="wp-block-code"><code>…</code></pre><!-- /wp:code -->` (letterlijk, alleen HTML-escaped, geen inline-opmaak).
- **Inline:** `**vet**`→`<strong>`, `*cursief*`→`<em>`, `` `code` ``→`<code>`,
  `[tekst](url)`→`<a href="url" target="_blank" rel="noopener noreferrer">tekst</a>`
  (links openen altijd in een nieuwe tab; `rel="noopener noreferrer"` is de
  veiligheidsstandaard bij `target="_blank"`).
- **Excerpt:** de cursieve kernquote (`*"…"*`) wordt platgemaakt als post-excerpt.

Een generieke markdown-library (pandoc, `markdown`) helpt hier niet: die produceert
klassieke HTML, geen Gutenberg-blokken. Daarom een kleine stdlib-converter in het script.

## WordPress admin

- Posts: https://edwinvandillen.nl/wp-admin/edit.php
- Media: https://edwinvandillen.nl/wp-admin/upload.php
- Post bewerken: https://edwinvandillen.nl/wp-admin/post.php?post={ID}&action=edit
