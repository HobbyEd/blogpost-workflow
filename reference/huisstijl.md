# Huisstijl — edwinvandillen.nl

Dit is de in-repo, zelfstandige kopie van de schrijfstijl-, kalibratie- en
visuele-identiteitsregels voor blogposts op edwinvandillen.nl. De workflow leest
deze regels hiervandaan, zodat de repo niet afhankelijk is van een `CLAUDE.md` in
een hogere map. Houd dit bestand in sync als de huisstijl verandert.

---

## Schrijfstijl

**Kernkarakter: feitelijk, zakelijk, intellectueel — toegankelijk maar nooit
populair/populistisch.**

### Toon & register
- Nederlands, beschouwend en stellig. Spreekt de lezer aan met **je**; auteur soms
  **we/wij** (Edwin + Sogyo-context). Doelgroep: professionals (architecten, CTO's,
  engineers, directie).
- Feitelijk en onderbouwd. **Geen** marketingtaal, clickbait, superlatieven of
  hype-woorden ("game changer", "revolutionair", uitroeptekens). Geen emoji in
  lopende tekst.
- Vakinhoudelijk maar legt jargon altijd kort uit bij eerste gebruik (bv.
  Shapiro-ladder, ubiquitous language).
- Eerlijk over nuance en grenzen: secties als "de techniek en haar grenzen", "de
  paradox: je wilt dit niet volledig". Sterke claims worden afgezwakt waar nodig.

### Structuur
- **Titel** = een stelling of these. Beschrijvend en feitelijk, niet promotioneel.
- Direct onder de titel een **cursieve kernquote** tussen aanhalingstekens die de
  hele post samenvat.
- **Geen inhoudsopgave.** Na de kernquote begint direct de eerste sectie.
- **`---`** scheidingslijnen tussen alle secties.
- **H2-koppen** zijn kort en pakkend, vaak een stelling of intrigerende frase, niet
  droog-beschrijvend.
- Korte alinea's (1–4 zinnen). Veel witruimte.
- Sluit doorgaans af met een "Waar begin je?"-achtige praktische sectie.

### Zinsbouw & ritme
- Afwisseling van lange, genuanceerde zinnen met **korte, declaratieve
  nadrukszinnen**.
- **Antithese** als handtekening-stijlfiguur.
- **"De vraag is niet X. De vraag is Y."**-constructie komt terug.
- **Tricolon/herhaling** voor effect.

### Opmaak-conventies
- **Bold** voor dé kernstelling van een sectie — spaarzaam, gericht.
- *Cursief* voor nadruk op losse termen en voor begrippen/citaten.
- Bullets met **bold lead-in term — uitleg**.
- Tabellen spaarzaam, alleen waar ze echt verdichten.

### Inhoudelijke aanpak
- Opent vaak met een **gangbare aanname/misvatting** die vervolgens wordt genuanceerd.
- Ankert abstracte concepten met een **concrete metafoor** of een praktijkgeval.
- Bouwt voort op erkende denkers en frameworks en **citeert met precieze bron,
  altijd met de URL als klikbare markdown-link**: inline
  `*(bron: [Anthropic, "Building Effective AI Agents", 2024](https://www.anthropic.com/engineering/building-effective-agents))*`,
  of in lopende tekst. De URL komt uit de geverifieerde bronnenlijst; nooit een
  gegokte link.
- Concrete cijfers/data waar mogelijk.
- Verwijst naar eigen frameworks/sites met links: augmentedengineering.nl,
  edwinvandillen.nl.
- Reeks-posts openen/sluiten met een verwijzing naar de bredere reeks (Augmented
  Software Engineering).

### Vermijden
Hype, superlatieven, holle bullets, uitroeptekens, emoji in lopende tekst,
populaire/jolige toon, ongefundeerde claims zonder bron.

---

## Kalibratie (belangrijk — feedback juni 2026)

De stijlfiguren hierboven (antithese, tricolon, korte nadrukszinnen, bold one-liners)
zijn **kruiden, geen hoofdgerecht**. In de praktijk schrijft Edwin **feitelijker en
soberder** dan een mechanische toepassing van die figuren suggereert. Concreet:

- **Eén** prikkelende/scherpe stelling per artikel is genoeg; niet elke sectie hoeft
  met een bold aforisme af te sluiten.
- Elke scherpe zin moet **direct feitelijk worden onderbouwd** (data, bron, concreet
  mechanisme) — anders is hij decoratief en moet hij weg.
- **Geen clichés/beeldspraak** als "slapeloze nachten", "brandjes blussen", "van de
  plank". **Geen anaforastapeling** ("Grip op X. Grip op Y. Grip op Z."). **Geen
  hyperbool** ("oneindig veel beter"). Voor "voor het eerst" en andere kwantoren: zie
  regel 2 van de tweede augustusronde hieronder, die er de bronplicht aan koppelt.
- **Titels zijn beschrijvend en feitelijk**, niet promotioneel.
- Bij twijfel: kies de feitelijke formulering boven de pakkende. De inhoud/these
  draagt het stuk, niet de retoriek.

**Aanvulling (juli 2026):**
- **De "X, niet/geen Y"-staart is vervangen.** Deze regel is opgegaan in regel 1 en regel 7
  van de augustusrondes hieronder, die over volgorde gaan in plaats van over de
  constructie. Houd die aan; hier staat alleen nog de verwijzing, zodat er niet twee
  formuleringen van dezelfde regel naast elkaar leven.
- **Leg jargon uit bij eerste gebruik.** Introduceer een term als "agency" niet
  zonder definitie; benoem kort wat je ermee bedoelt voordat je erop voortbouwt.
- **Geen zwaktemarkeerders als "eerlijk gezegd".** Vermijd inleidingen als "eerlijk
  gezegd", "om eerlijk te zijn" of "eigenlijk". Ze suggereren dat de rest van de tekst
  níét eerlijk is, en dat is nooit zo: we schrijven altijd feitelijk. Laat de
  bewering voor zichzelf spreken en schrap de markeerder.

**Aanvulling (augustus 2026):**
- **Geen komma + "en" tussen twee hoofdzinnen.** *(Let op: deze regel is in de derde
  augustusronde hieronder geherformuleerd. Bij een oorzakelijk verband hoort een
  onderschikkend voegwoord in plaats van een punt. Lees beide.)* De constructie `..., en ...` waarbij
  het deel ná de komma een eigen onderwerp en persoonsvorm heeft, rekt een zin op zonder
  dat het verband sterker wordt. Het leest niet vloeiend. Maak er twee zinnen van, of
  schrap het voegwoord.
  Fout: *"Die as staat, en deel 4 gaf er ook een richtlijn bij."*
  Beter: *"Die as staat. Deel 4 gaf er ook een richtlijn bij."*
  Fout: *"Welk gereedschap pak je erbij, en waarop baseer je die keuze."*
  Beter: *"Welk gereedschap pak je erbij? En waarop baseer je die keuze?"*
  **Wel toegestaan:** een opsomming van zinsdelen zonder eigen persoonsvorm
  (*"model, tools, en geheugen"*), en een bijzin die niet zelfstandig kan staan.
  Let bij het redigeren ook op dezelfde oprekking met `, maar`, `, want` en `, dus`:
  die zijn niet verboden, maar als er drie of meer van dit soort koppelingen in één
  alinea staan, is dat een signaal dat de zinnen te lang zijn.

**Aanvulling (augustus 2026, tweede ronde) — feitelijkheid.**

Deze vijf regels vervangen en verscherpen de eerdere "X, niet/geen Y"-regel. Ze zijn
opgesteld naar aanleiding van deel 1 van de reeks Intentie-gedreven engineering, waar de
oude formulering een overtreding liet passeren omdat de check hem "informatief" vond. De
kern van de correctie: **beoordeel de volgorde en de onderbouwing, niet de intentie van de
schrijver.** Feitelijk schrijven is soms saaier. Dat is de bedoeling.

1. **Positief eerst. Contrast pas daarna, en alleen als het draagt.**
   Een zin of alinea mag niet openen met wat iets *niet* is. Zet de bewering neer, en
   voeg het contrast er hooguit achteraan toe. Er is geen uitzondering voor een
   "informatieve" ontkenning: dat een negatie informatie draagt, maakt de volgorde niet
   goed. De vraag is niet óf de ontkenning iets zegt, maar of de zin ervoor al zegt wat
   het wél is.
   Fout: *"Wat deze vier delen is niet één mechanisme. De middelen verschillen
   fundamenteel."*
   Beter: *"Deze vier delen een probleemstelling. De middelen waarmee ze hem oplossen
   verschillen: training, een specificatietaal en een meetlus zijn niet uitwisselbaar."*
   Fout: *"Het probleem is niet nieuw."* Beter: *"Het probleem is oud."*

2. **Een kwantor is een claim en heeft een bron nodig.**
   Woorden die een meting suggereren tellen als scherpe claim, ook zonder cijfer:
   *overal, nergens, altijd, nooit, vrijwel nooit, de meeste, het vaakst, zelden,
   iedereen, niemand, voor het eerst, al decennia, in de praktijk blijkt.* Zet er een
   bron bij, of vervang de kwantor door de waarneming die je wél kunt onderbouwen. Een
   eigen observatie mag, mits je hem als zodanig benoemt.
   Fout: *"Assurance en optimization ontbreken bij de meeste organisaties."*
   Beter: *"Ik kom assurance en optimization zelden tegen"*, of een bron erbij.

3. **Een causaal verband benoemt het mechanisme, of vervalt.**
   Schrijf geen oorzaak-gevolg op grond van aannemelijkheid. Als je het mechanisme niet
   kunt benoemen, geef dan alleen de waarneming. Let op gangbare uitdrukkingen die een
   verband suggereren dat nooit is vastgesteld.
   Fout: *"Iets bouwen was lang duur genoeg om vooraf na te denken over wat je bouwde."*
   Beter: alleen wat je kunt vaststellen, bijvoorbeeld dat de kosten per regel code zijn
   gedaald, met een bron.

4. **Beweren in plaats van aankondigen.**
   Geen zinnen die alleen beloven dat er iets komt. Als het antwoord er is, geef het. Als
   het verderop staat, zeg dat in dezelfde zin als de bewering.
   Fout: *"Wat er feitelijk is veranderd, ligt ergens anders."* / *"De reden ligt
   elders."* / *"Dat heeft een keerzijde."*
   Beter: benoem de verandering, de reden of de keerzijde meteen.

5. **Geen oordeel over het eigen betoog.**
   De tekst kwalificeert zichzelf niet. Laat weg dat een tegenwerping "de scherpste" is,
   dat een formulering "scherp genoeg is om te herhalen", dat een lijn "er een van
   toenemend ongemak" is. De lezer bepaalt dat.

**Versterkers zonder inhoud.** Schrap: *ineens, meteen, precies, feitelijk, eigenlijk,
gewoon, daadwerkelijk, echt, simpelweg, natuurlijk, uiteraard, overduidelijk.* Ze voegen
nadruk toe zonder informatie. Uitzondering: als het woord een betekenisverschil maakt dat
zonder het woord verdwijnt.

**Aanvulling (augustus 2026, derde ronde) — leesbaarheid.**

De regels hierboven zijn allemaal verboden, en een tekst die er perfect op scoort kan
onleesbaar zijn. Dat is één keer gebeurd: bij deel 1 van de intentie-reeks daalde de
gemiddelde zinslengte naar 14,7 woorden met 48% korte zinnen, tegen 16 tot 20 woorden en
30 tot 36% in de gepubliceerde anatomie-reeks. Het resultaat las als een opsomming van
losse beweringen. **Feitelijk en vloeiend zijn geen tegenpolen; als ze botsen, is de
oplossing herschrijven, niet inleveren op een van beide.** Bij twijfel: liever meer tekst
die loopt dan minder tekst die hakkelt.

Onderstaande eisen zijn **positief**: ze moeten aanwezig zijn, niet afwezig.

1. **Variatie in zinslengte.** Wissel lange en korte zinnen af. Een lange zin ontwikkelt
   een gedachte, een korte laat hem landen. Drie of meer korte zinnen achter elkaar is een
   signaal, geen doel.
   **De norm staat niet hier maar in `scripts/leesbaarheid.py`.** Dat script leidt de
   bandbreedte af uit de gepubliceerde delen van de anatomie-reeks en velt het oordeel.
   Eerder stonden er ook getallen in deze tekst, en die weken af van wat het script
   berekende: een draft met een spreiding van 7,8 was "binnen band" volgens het script en
   te laag volgens deze regel. Eén bron volstaat.

2. **Onderschikkende voegwoorden zijn gewenst.** *Doordat, waardoor, zodat, terwijl,
   omdat, hoewel, zolang, zoals.* Ze maken het verband tussen twee beweringen expliciet.
   Een tekst met weinig voegwoorden dwingt de lezer het verband zelf te reconstrueren.

3. **Alinea's haken aan.** Een nieuwe alinea opent met een woord of zinsdeel dat
   terugverwijst naar de vorige. Alinea's die koud beginnen met een nieuw onderwerp maken
   van een betoog een lijst.

4. **Concreet boven abstract.** Een waarneembaar geval zegt meer dan een abstractie, en is
   bovendien beter te controleren. Fout: *"de schaarste verplaatst zich van het bouwen
   naar het bepalen."* Beter: benoem wat er schaars is en bij wie.

5. **Geen stellagewerk.** Geef de waarneming, niet het voorbehoud eromheen. *"In mijn
   praktijk zie ik dat …"*, *"het signaal dat ik erbij noteer"* en *"de organisaties waar
   ik kom"* zijn constructies die feitelijkheid nabootsen zonder iets toe te voegen. Een
   observatie mag als observatie worden gepresenteerd, maar in één keer en zonder
   omhaal.

**Herformulering van de komma+en-regel.** Het doel van die regel is de **opgerekte zin**,
niet het voegwoord. Een punt zetten is alleen goed als de twee beweringen los van elkaar
staan. Is het verband oorzakelijk of gevolgtrekkend, gebruik dan een onderschikkend
voegwoord in plaats van een punt.
Fout: *"De kosten daalden, en het volume steeg."*
Zwak: *"De kosten daalden. Het volume steeg."* (verband verdwenen)
Goed: *"Doordat de kosten daalden, steeg het volume."*

**Werkwijze bij redigeren.** Levert een controle meer dan vijf bevindingen op in één
sectie, herschrijf die sectie dan in plaats van hem te patchen. Losse ingrepen stapelen tot
houterigheid: elke splitsing haalt een voegwoord weg, elke schrapping een scharnier.

**Aanvulling (augustus 2026, vierde ronde) — de lezer en de vorm.**

Aanleiding is de kernquote van deel 1 van de intentie-reeks: *"AI heeft intentie niet
belangrijk gemaakt. Het heeft de laatste smoes weggenomen om er niet mee te beginnen."*
Die zin was uitgezonderd van de controle omdat hij de dragende stelling was, en juist daar
bleek de zwaarste overtreding te zitten.

6. **Geen motieftoeschrijving aan de lezer.** Schrijf niet waaróm de lezer iets tot nu toe
   niet deed. Woorden als *smoes, excuus, uitvlucht, gemakzucht, onwil*, en constructies
   als "wie dat nog niet doet, durft niet", leggen de lezer een beweegreden in de mond die
   je niet kunt kennen. Beschrijf de toestand; laat het motief weg.
   Fout: *"Het heeft de laatste smoes weggenomen om er niet mee te beginnen."*
   Beter: benoem wat er verandert en wat dat oplevert.
   Onderscheid: een waargenomen gedraging beschrijven mag (*"teams vieren releases waarvan
   de impact niet aanwijsbaar is"*). Verklaren waarom ze dat doen, niet.

7. **Geen antithese als bouwvorm.** De eerdere regel verbood de "X, niet Y"-staart binnen
   één zin. Hetzelfde geldt voor een passage die om een tegenstelling heen is gebouwd:
   opzet, omkering, klap. Zo'n constructie ontleent zijn kracht aan de symmetrie en niet
   aan wat er staat, en hij is daardoor niet te toetsen. Test: schrap de tegenstelling en
   kijk wat er aan bewering overblijft. Blijft er niets over, dan was er ook niets.
   **Dit geldt ook voor de kernquote en voor H2-koppen.**

**De kernquote valt onder alle regels.** Er is geen uitzondering voor de cursieve stelling
onder de titel, ook niet als hij de reeks draagt. Een quote kan zijn eigen bron niet
meedragen; de toets is daarom dat het artikel eronder exact die claim levert en onderbouwt.
Levert het stuk de claim niet, dan is de quote een belofte in plaats van een samenvatting.

---

## Visuele identiteit — kleurstelling voor diagrammen en visuals

**Standaardpalet voor alle visuals/diagrammen** (WOOSH5 / augmentedorganisation.nl-
stijl). Gebruik dit palet, niet ad-hoc kleuren. Er is een donker (default) en een
licht thema.

**Drie zone-kleuren** (kern van de merkidentiteit — Mens/Machine/Managementstijl):
- Machine (groen): `#27ae60`
- Mens (amber/peach): `#f5a623`  ← tevens het accent
- Managementstijl (blauw): `#4a90e2`
- Soft-varianten = dezelfde kleur op `rgba(...,0.16)` voor vlakvullingen

**Donker thema (default):**
- achtergrond `#0d1b2a` · `#0f1e30` · kaart `#142840`
- tekst `#dde6f0` · gedempt `#9ab0c4` · lijn `rgba(255,255,255,.12)`
- accent `#f5a623` · accent-tekst `#ffc56b`
- schaduw `0 18px 50px rgba(0,0,0,.45)`

**Licht thema:**
- achtergrond `#f4f7fb` · `#e9eef5` · kaart `#ffffff`
- tekst `#102132` · gedempt `#52647a` · lijn `#d8e0ea`
- accent `#e08a1e` · accent-tekst `#b5611f`
- schaduw `0 18px 50px rgba(20,40,70,.10)`

**Typografie & vormtaal:**
- Font: systeem-stack `'Segoe UI',-apple-system,BlinkMacSystemFont,Roboto,'Helvetica Neue',Arial,sans-serif`.
  DM Serif Display mag als kop blijven, maar Segoe UI is de huisstijl-basis.
- Koppen: zwaar (700–800), strakke letter-spacing (`-.02em`).
- "Kicker"-label: uppercase, `letter-spacing:.18em`, kleur = accent-ink, met een
  gekleurde dot ervoor.
- Kaarten: ruime `border-radius` (14–18px), 1px lijn-border, zachte schaduw.

**Sequentiële/categorische schaal:** maroon `rgba(150,60,75)` → oranje
`rgba(225,130,80)` → geel `rgba(235,205,110)` → lichtgroen `rgba(150,200,150)` →
groen `rgba(90,165,105)` → blauwgrijs `rgba(80,120,135)`. Risico-rood lijn `#c0392b`,
risico-tekst `#d9756f`.
