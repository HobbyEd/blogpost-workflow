#!/usr/bin/env python3
"""Deploy een blogpost-draft als WordPress-CONCEPT met Gutenberg-blokken.

Deterministische deploy-stap van de blogpost-workflow (fase 6). Zet markdown om
naar Gutenberg blok-markup (niet klassieke HTML — dat scheelt handmatig converteren
naar blokken), uploadt lokale afbeeldingen als media, en maakt of werkt een post bij.

De post krijgt ALTIJD `status: draft`. Er is bewust geen publiceer-optie: live zetten
blijft een handmatige actie van Edwin in wp-admin. Zo is de harde deploy-gate ook in
code afgedwongen.

Alleen de Python-standaardlibrary. Credentials uit `.env` in de repo-root
(`WP_APPLICATION_TOKEN`, `WP_USERNAME`, `WP_SITE_URL`), nooit in code of output.

Gebruik:
    python scripts/deploy_post.py --post-dir posts/<slug> [--post-id N] [--dry-run]
                                  [--allow-published]

--dry-run  : converteer en print de blok-HTML; geen upload, geen post. Voor testen.
--post-id N: werk een bestaand concept bij (PUT) i.p.v. een nieuw concept aanmaken.
             Weigert als de post al gepubliceerd is; forceer met --allow-published.
"""

import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error

# --------------------------- credentials & config ---------------------------

def find_up(filename, start):
    d = os.path.abspath(start)
    while True:
        cand = os.path.join(d, filename)
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_env_dict():
    """Laad sleutel-waarde paren uit .env in de repo root (indien aanwezig)."""
    env = {}
    path = find_up(".env", os.path.dirname(os.path.abspath(__file__)))
    if not path:
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'").strip('"')
            env[k] = v
    return env


_ENV = load_env_dict()


def get_env_val(key, default=None):
    """Haal waarde op uit echte os.environ of uit .env dictionary."""
    if os.environ.get(key):
        return os.environ[key]
    if key in _ENV:
        return _ENV[key]
    return default


SITE = get_env_val("WP_SITE_URL", "https://edwinvandillen.nl").rstrip("/")
POSTS_EP = SITE + "/?rest_route=/wp/v2/posts"
MEDIA_EP = SITE + "/?rest_route=/wp/v2/media"
USER = get_env_val("WP_USERNAME", "edwin")


def load_token():
    for key in ("WP_APPLICATION_TOKEN", "WORDPRESS_APPLICATION_TOKEN", "wordpress-application-token"):
        val = get_env_val(key)
        if val:
            return val
    raise RuntimeError("'WP_APPLICATION_TOKEN' of 'wordpress-application-token' ontbreekt in .env.")


def auth_header():
    token = load_token()
    raw = f"{USER}:{token}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


# --------------------------- markdown -> inline ---------------------------

def inline(text):
    """Zet inline-markdown om naar HTML. Escape eerst, dan opmaak toepassen."""
    text = html.escape(text, quote=False)
    # links: [tekst](url) — altijd in een nieuwe tab (target="_blank"), met
    # rel="noopener noreferrer" als veiligheidsstandaard bij target="_blank".
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
    # bold vóór italic
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


# --------------------------- blok-emitters ---------------------------

def b_paragraph(txt):
    return f"<!-- wp:paragraph -->\n<p>{inline(txt)}</p>\n<!-- /wp:paragraph -->"


def b_heading(txt, level):
    attr = "" if level == 2 else f' {{"level":{level}}}'
    return (f"<!-- wp:heading{attr} -->\n"
            f'<h{level} class="wp-block-heading">{inline(txt)}</h{level}>\n'
            f"<!-- /wp:heading -->")


def b_separator():
    return ('<!-- wp:separator -->\n'
            '<hr class="wp-block-separator has-alpha-channel-opacity"/>\n'
            '<!-- /wp:separator -->')


def b_list(items, ordered):
    tag = "ol" if ordered else "ul"
    attr = ' {"ordered":true}' if ordered else ""
    inner = []
    for it in items:
        inner.append("<!-- wp:list-item -->\n"
                     f"<li>{inline(it)}</li>\n"
                     "<!-- /wp:list-item -->")
    body = "\n\n".join(inner)
    return (f"<!-- wp:list{attr} -->\n"
            f'<{tag} class="wp-block-list">{body}</{tag}>\n'
            f"<!-- /wp:list -->")


def b_table(header, rows):
    def cells(tag, vals):
        return "".join(f"<{tag}>{inline(v)}</{tag}>" for v in vals)
    thead = f"<thead><tr>{cells('th', header)}</tr></thead>"
    body_rows = "".join(f"<tr>{cells('td', r)}</tr>" for r in rows)
    tbody = f"<tbody>{body_rows}</tbody>"
    return ("<!-- wp:table -->\n"
            '<figure class="wp-block-table">'
            f'<table class="has-fixed-layout">{thead}{tbody}</table></figure>\n'
            "<!-- /wp:table -->")


def b_image(url, alt, media_id):
    idattr = f'"id":{media_id},' if media_id else ""
    return (f'<!-- wp:image {{{idattr}"sizeSlug":"large","linkDestination":"none"}} -->\n'
            '<figure class="wp-block-image size-large">'
            f'<img src="{html.escape(url)}" alt="{html.escape(alt)}"'
            + (f' class="wp-image-{media_id}"' if media_id else "")
            + "/></figure>\n<!-- /wp:image -->")


def b_quote(lines):
    """lines: de tekstregels van een blockquote (zonder de '> '). Inline-opmaak geldt."""
    paras = "".join(f"<p>{inline(ln)}</p>" for ln in lines if ln.strip())
    return ("<!-- wp:quote -->\n"
            f'<blockquote class="wp-block-quote">{paras}</blockquote>\n'
            "<!-- /wp:quote -->")


def b_code(code):
    """code: letterlijke code (geen inline-opmaak), alleen HTML-escapen; newlines behouden."""
    escaped = html.escape(code, quote=False)
    return ("<!-- wp:code -->\n"
            f'<pre class="wp-block-code"><code>{escaped}</code></pre>\n'
            "<!-- /wp:code -->")


# --------------------------- markdown -> blokken ---------------------------

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HEAD_RE = re.compile(r"^(#{2,6})\s+(.*)$")
OL_RE = re.compile(r"^\d+\.\s+(.*)$")
UL_RE = re.compile(r"^[-*]\s+(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")


def parse_blocks(body, image_urls):
    """image_urls: dict lokaal-pad -> (url, media_id). body: markdown zonder titel."""
    lines = body.split("\n")
    blocks = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # scheiding
        if stripped == "---":
            blocks.append(b_separator())
            i += 1
            continue

        # kop
        m = HEAD_RE.match(stripped)
        if m:
            blocks.append(b_heading(m.group(2).strip(), len(m.group(1))))
            i += 1
            continue

        # losse afbeelding
        im = IMG_RE.match(stripped)
        if im and stripped == im.group(0):
            src, alt = im.group(2), im.group(1)
            url, mid = image_urls.get(src, (src, None))
            blocks.append(b_image(url, alt, mid))
            i += 1
            continue

        # tabel (regels beginnen met |)
        if stripped.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            header = [c.strip() for c in tbl[0].strip("|").split("|")]
            rows = []
            for row in tbl[2:]:  # tbl[1] is de |---|-scheider
                rows.append([c.strip() for c in row.strip("|").split("|")])
            blocks.append(b_table(header, rows))
            continue

        # codeblok (``` ... ```)
        if stripped.startswith("```"):
            i += 1  # openingsfence overslaan
            code_lines = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])  # ruwe regel, inspringing behouden
                i += 1
            i += 1  # sluitfence overslaan
            blocks.append(b_code("\n".join(code_lines)))
            continue

        # blockquote (> ...)
        if QUOTE_RE.match(stripped):
            q = []
            while i < n and QUOTE_RE.match(lines[i].strip()):
                q.append(QUOTE_RE.match(lines[i].strip()).group(1).strip())
                i += 1
            blocks.append(b_quote(q))
            continue

        # geordende lijst
        if OL_RE.match(stripped):
            items = []
            while i < n and OL_RE.match(lines[i].strip()):
                items.append(OL_RE.match(lines[i].strip()).group(1).strip())
                i += 1
            blocks.append(b_list(items, ordered=True))
            continue

        # ongeordende lijst
        if UL_RE.match(stripped):
            items = []
            while i < n and UL_RE.match(lines[i].strip()):
                items.append(UL_RE.match(lines[i].strip()).group(1).strip())
                i += 1
            blocks.append(b_list(items, ordered=False))
            continue

        # paragraaf: verzamel opeenvolgende gewone regels
        para = []
        while i < n and lines[i].strip() and not _is_special(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        blocks.append(b_paragraph(" ".join(para)))

    return "\n\n".join(blocks)


def _is_special(s):
    return (s == "---" or HEAD_RE.match(s) or s.startswith("|")
            or s.startswith("```") or QUOTE_RE.match(s)
            or OL_RE.match(s) or UL_RE.match(s)
            or (IMG_RE.match(s) and s == IMG_RE.match(s).group(0)))


# --------------------------- titel / excerpt ---------------------------

def split_title(md):
    lines = md.split("\n")
    title = None
    rest_start = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith("# ") and title is None:
            title = line.strip()[2:].strip()
            rest_start = idx + 1
            break
    body = "\n".join(lines[rest_start:])
    return title, body


def find_excerpt(body):
    """Eerste cursieve kernquote (*"..."*) als excerpt, plat gemaakt."""
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("*") and s.endswith("*") and len(s) > 2:
            plain = s.strip("*").strip().strip('"').strip("“”")
            return plain
    return ""


# --------------------------- REST ---------------------------

def rest(url, payload=None, method="GET", ctype="application/json"):
    headers = {"Authorization": auth_header()}
    data = None
    if payload is not None:
        headers["Content-Type"] = ctype
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} op {method} {url}: "
                           f"{e.read().decode('utf-8', 'replace')[:300]}") from e


def find_existing_media(fname, blob):
    """Zoek media die al op de site staat met deze bestandsnaam en inhoud.

    Zonder deze check uploadt elke her-deploy dezelfde visual opnieuw; WordPress
    hangt er dan een -1, -2 achter en de mediabibliotheek loopt vol met kopieen.
    We hergebruiken alleen bij een exacte match op grootte en inhoud, zodat een
    gewijzigde visual met dezelfde naam wel een nieuwe upload wordt.
    """
    stem = os.path.splitext(fname)[0]
    try:
        q = urllib.parse.quote(stem)
        hits = rest(f"{MEDIA_EP}&search={q}&per_page=20&_fields=id,source_url")
    except Exception:
        return None
    for m in hits or []:
        url = m.get("source_url", "")
        if url.rsplit("/", 1)[-1] != fname:
            continue
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                if r.read() == blob:
                    return m["id"], url
        except Exception:
            continue
    return None


def upload_media(path):
    fname = os.path.basename(path)
    with open(path, "rb") as fh:
        blob = fh.read()
    bestaand = find_existing_media(fname, blob)
    if bestaand:
        print(f"  hergebruikt bestaande media: {fname} (id {bestaand[0]})", file=sys.stderr)
        return bestaand
    headers = {
        "Authorization": auth_header(),
        "Content-Disposition": f'attachment; filename="{fname}"',
        "Content-Type": "image/png",
    }
    req = urllib.request.Request(MEDIA_EP, data=blob, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["id"], d["source_url"]


# --------------------------- main ---------------------------

def main():
    # Windows-console is standaard cp1252; forceer UTF-8 zodat --dry-run met tekens als
    # de em-dash of pijl (→) niet crasht. De echte deploy stuurt sowieso UTF-8 via urllib.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Deploy blogpost als WordPress-concept (blokken).")
    ap.add_argument("--post-dir", required=True, help="pad naar posts/<slug>/")
    ap.add_argument("--post-id", type=int, default=None, help="bestaand concept bijwerken")
    ap.add_argument("--allow-published", action="store_true",
                    help="sta bijwerken van een REEDS GEPUBLICEERDE post toe (standaard geweigerd)")
    ap.add_argument("--dry-run", action="store_true", help="alleen converteren + printen")
    args = ap.parse_args()

    draft_path = os.path.join(args.post_dir, "draft.md")
    md = open(draft_path, encoding="utf-8").read()
    title, body = split_title(md)
    if not title:
        print("FOUT: geen titel (# ...) gevonden in de draft.", file=sys.stderr)
        sys.exit(1)
    excerpt = find_excerpt(body)

    # lokale afbeeldingen verzamelen (pad relatief aan post-dir)
    local_imgs = []
    for m in IMG_RE.finditer(body):
        src = m.group(2)
        full = src if os.path.isabs(src) else os.path.join(args.post_dir, src)
        if os.path.isfile(full):
            local_imgs.append((src, full))

    # Veiligheidsklep, vóór elke upload: nooit ongemerkt een live post overschrijven
    # met een lokale draft. Die kan afwijken van wat gepubliceerd is, en een
    # overschrijving is niet terug te draaien. De check staat bewust vóór de
    # media-afhandeling, anders upload je nog een afbeelding en weiger je daarna.
    bestaande_status = None
    if args.post_id and not args.dry_run:
        try:
            huidig = rest(f"{POSTS_EP}/{args.post_id}&_fields=status,title,modified")
        except Exception as e:
            raise SystemExit(f"Kan status van post {args.post_id} niet ophalen: {e}")
        bestaande_status = huidig.get("status")
        if huidig.get("status") == "publish" and not args.allow_published:
            titel = (huidig.get("title") or {}).get("rendered", "?")
            raise SystemExit(
                f"GEWEIGERD: post {args.post_id} is GEPUBLICEERD ({titel}).\n"
                f"Laatst gewijzigd: {huidig.get('modified')}.\n"
                "Bijwerken zou de live tekst vervangen door de lokale draft, die kan "
                "afwijken van wat er gepubliceerd staat.\n"
                "Weet je het zeker? Gebruik dan --allow-published."
            )

    image_urls = {}
    media = []
    if not args.dry_run:
        for src, full in local_imgs:
            mid, url = upload_media(full)
            image_urls[src] = (url, mid)
            media.append({"src": src, "id": mid, "url": url})

    content = parse_blocks(body, image_urls)
    featured = media[0]["id"] if media else 0

    if args.dry_run:
        print(f"# TITEL: {title}\n# EXCERPT: {excerpt}")
        print(f"# LOKALE AFBEELDINGEN: {[s for s, _ in local_imgs]}")
        print("# --- BLOK-HTML ---")
        print(content)
        return

    # Nieuwe posts worden ALTIJD een concept; publiceren blijft handwerk in wp-admin.
    # Werk je met --allow-published een reeds gepubliceerde post bij, dan blijft die
    # gepubliceerd: "draft" forceren haalde de live post offline als bijwerking, wat
    # niemand vraagt bij een tekstcorrectie.
    doelstatus = "draft"
    if args.allow_published and bestaande_status == "publish":
        doelstatus = "publish"
        print("post blijft GEPUBLICEERD (--allow-published op een live post)")

    payload = {
        "title": title,
        "content": content,
        "status": doelstatus,
        "excerpt": excerpt,
        "featured_media": featured,
    }
    if args.post_id:
        result = rest(f"{POSTS_EP}/{args.post_id}", payload, method="POST")
    else:
        result = rest(POSTS_EP, payload, method="POST")

    pid = result["id"]
    out = {
        "post_id": pid,
        "status": result.get("status"),
        "title": title,
        "featured_media": featured,
        "media": media,
        "edit_url": f"{SITE}/wp-admin/post.php?post={pid}&action=edit",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
