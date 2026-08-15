# ADR-010: Workflow-topologie — waar de mens beslist en wat er opnieuw moet

* **Status**: Accepted
* **Datum**: 2026-08-15
* **Auteurs**: Edwin van Dillen
* **Gerelateerd**: [ADR-001 (Strikte control plane)](001-strict-deterministic-control-plane.md), [ADR-003 (Twee modi)](003-two-phase-interactive-yolo-workflow.md), [ADR-004 (Harde vs zachte gates)](004-hard-soft-quality-gates-strategy.md), [ADR-007 (Archief-consistentie)](007-archival-alignment-validation-agent.md)

---

## 1. Context & Probleemstelling

De keten telt elf fases met achter vrijwel elke fase een menselijke gate. Na dertien posts
laat het logboek zien dat die opzet niet doet wat hij belooft.

**49 gate-goedkeuringen, nul afwijzingen.** Het reject-pad bestaat in de CLI, de engine en
de UI en is tot 15 augustus 2026 nooit gebruikt. Dat betekent niet dat er niets mis was:
deel 1 van de intentie-reeks stond live met een citaat dat niet in de aangehaalde paper
voorkomt, en deel 2 bevatte twee misquotes die de feitencheck van 12 augustus had
goedgekeurd. De gates stonden dus open op momenten waarop er wél iets mis was.

**Het echte oordeel valt buiten de keten.** De inhoudelijke opmerkingen op deel 2 kwamen
pas nadat het concept in WordPress stond: de Sinek-behandeling moest eruit, de visuals
tekenden lagen als zuilen, en het slot gaf geen antwoord op de vraag uit de titel. Geen van
die drie is de uitkomst van een check. Het zijn oordelen over het stuk als geheel, en ze
konden pas ontstaan toen de tekst leesbaar op het scherm stond.

**Een correctie is nu een replay, geen lus.** Voor drie gerichte ingrepen liep deel 2
opnieuw door draft, style, series, visuals, factcheck en alignment. De Grok-fase is met de
hand overgeslagen, omdat een tweede kritiekronde de sectie zou terugbouwen die net was
geschrapt. Dat "met de hand" is het probleem: de keten weet niet wélke artefacten door een
wijziging ongeldig worden.

**Twee verschillende dingen heten "gate".**

| | machinecontrole | auteursoordeel |
|---|---|---|
| vraag | is deze stap correct uitgevoerd? | is dit het stuk dat ik wil? |
| uitkomst | bevindingen, of niets | richting, schrappen, herformuleren |
| kosten | goedkoop en herhaalbaar | duur, vraagt de tekst in leesbare vorm |
| frequentie nu | elf keer per post | één keer, ná deploy |

Achter elke machinecontrole staat een menselijke gate. Wie elf keer per post "akkoord" moet
klikken, klikt de vijftigste keer ook akkoord. Tegelijk staat het ene moment waarop de
auteur werkelijk oordeelt helemaal niet in het systeem.

---

## 2. Overwogen Alternatieven

### Alternatief A: laten zoals het is

De gates staan er, ze kosten weinig, en de discipline om ze te lezen kan groeien.

*Nadeel*: de meting spreekt dit tegen. Nul afwijzingen op 49 goedkeuringen is geen
groeiende discipline maar een gate die geen functie heeft. En het leesmoment blijft achter
de deploy hangen, waar een correctie het duurst is.

### Alternatief B: voorwaardelijke gates plus een leesmoment vóór de deploy

De volgorde van de fases blijft, maar:

- een gate stopt alleen nog bij een bevinding, zoals de alignment-gate sinds ADR-007;
- de losse rapporten worden gebundeld tot één bevindingenoverzicht per post;
- de web-UI krijgt een leesweergave van de gerenderde draft, met de mogelijkheid per
  sectie een opmerking achter te laten;
- de fases worden geclusterd in drie blokken met drie echte gates.

*Nadeel*: de keten blijft lineair. Een correctieronde loopt nog steeds langs alle fases,
ook langs de fases die door de wijziging niet zijn geraakt.

### Alternatief C: een afhankelijkheidsgraaf in plaats van een volgorde

Bovenop B: elk artefact draagt de vingerafdruk van de invoer waaruit het is afgeleid.
`next` berekent daaruit wat verouderd is. De keten wordt een build-graaf.

*Nadeel*: meer bewegende delen, en de graaf moet kloppen. Een fout in de
afhankelijkheidsdefinitie levert stil overgeslagen controles op, en dat is precies de
klasse fout die deze codebase al twee keer heeft laten zien.

---

## 3. Beslissing

**We voeren B nu uit en groeien incrementeel naar C**, te beginnen bij de artefacten die op
15 augustus met de hand moesten worden overgeslagen.

### 3.1 Drie blokken, drie gates in plaats van elf

| blok | fases | gate |
|---|---|---|
| **Richten** | intake, outline | **echte gate**: onderwerp, invalshoek, bronnen |
| **Bouwen** | draft, Grok-kritiek, visuals, stijl, leesbaarheid, reeks, feiten, archief | **alleen bij bevindingen** |
| **Oordelen** | concept-deploy, lezen in WordPress, opmerkingen, synthese, herzien | **echte gate**, met lus terug naar Bouwen |

Live zetten valt buiten het systeem: dat is en blijft handwerk in wp-admin.

De Richten-gate is vandaag de meest verwaarloosde en de goedkoopste. Een verkeerde
invalshoek corrigeren kost daar tien minuten en na de draft twee uur. Bij deel 2 stond de
Sinek-sectie al in de outline; daar had de vraag "moet dit erin" thuisgehoord.

**Maken en Toetsen zijn samengevoegd tot Bouwen.** Ze waren in het eerste voorstel twee
blokken, maar er zit geen menselijk besluit tussen: de checks lopen op wat de schrijver
oplevert, en beide stoppen alleen bij een bevinding. Twee blokken zonder gate ertussen is
één blok.

### 3.2 Grok blijft staan waar hij staat

Overwogen is de kritiekfase naar voren te halen, omdat Grok bij deel 2 de Sinek-sectie
langer maakte in plaats van korter. Die conclusie wordt niet overgenomen. Grok deed zijn
werk: hij signaleerde een ontbrekende tegenwerping. Het probleem zat in de verwerking.

### 3.3 De synthese wordt een beslismoment, geen weegstap

Dit is de kern van de wijziging.

De synthese-agent levert per kritiekpunt een advies met alternatieven. Bij deel 2 werd
schrappen wel degelijk aangeboden: punt 1 noemde expliciet *"Alternatief C: sectie 7
helemaal schrappen (scheelt circa 250 woorden)"*. Het advies luidde A, behouden en
herkaderen, en dat is overgenomen. De optie ontbrak dus niet; het advies boog naar
behouden, en de auteur volgde het advies.

Daar komt een systematische groeidruk uit voort. Grok becommentarieert per sectie, dus zijn
punten gaan over hoe een sectie beter kan, niet over of ze moet bestaan. De synthese vertaalt
dat in aanpassingen. Het resultaat is dat elke ronde de tekst langer maakt.

Daarom:

1. **De auteur beslist per punt, en die beslissing wordt vastgelegd** in de web-UI, met de
   gekozen variant en één regel motivering. Niet een akkoord op het geheel.
2. **De synthese-agent adviseert niet meer één variant**, maar legt de varianten neutraal
   voor met hun gevolg in woorden. Het advies was het scharnier waarlangs de tekst groeide.
3. **Bij elk punt is "verwerpen" een even zichtbare optie als aannemen**, met de vraag erbij
   of het punt de sectie raakt of het bestaansrecht ervan.
4. **De synthese verhuist naar het Oordelen-blok** en verwerkt in één ronde zowel de
   Grok-punten, de machinebevindingen als de opmerkingen van de auteur. Eén mechanisme voor
   alle openstaande punten.

Let op: de synthese is aantoonbaar de plek waar fouten binnenkomen. Twee keer op rij stond
er een verkeerd deelnummer in een vooruitwijzing, beide keren ontstaan bij het verwerken van
de synthese. De hertoetsing na deze stap is daarom niet optioneel.

### 3.4 Het WordPress-concept ís de leesweergave

Overwogen is een leesweergave in de web-UI te bouwen, zodat het oordeel vóór de deploy zou
vallen. Dat doen we niet.

De auteur leest in WordPress, in de opmaak van de eigen site, en dat is geen slechte
gewoonte maar de juiste: daar staat de tekst zoals de lezer hem krijgt, met de visuals op
ware grootte en de typografie van het thema. Een preview in de web-UI zou daar altijd net
naast zitten, en een preview die net naast zit wordt niet gebruikt.

Daarmee verandert de betekenis van de deploy-stap. Hij is niet langer het sluitstuk maar de
**renderstap van het Oordelen-blok**: hij maakt lezen mogelijk. Dat is ook hoe hij feitelijk
al werd gebruikt, want de inhoudelijke opmerkingen op deel 2 kwamen pas na de concept-deploy.

Gevolgen:

1. **De deploy-gate wordt goedkoop en voorwaardelijk.** Deployen naar concept mag zodra alle
   controles groen en actueel zijn; daar hoeft geen mens meer voor te tekenen. De
   vingerafdruk uit `state.deploy_approval` blijft, maar bewaakt voortaan of de controles bij
   de tekst horen, niet of de auteur wil publiceren. Deployen wordt iets wat je vaak doet.
2. **De echte beslissing valt ná het lezen.** Twee uitkomsten: klaar, of een lijst
   opmerkingen. Die opmerkingen worden vastgelegd in `revisie.md`, met dezelfde status als de
   bevinding van een check, en zijn daarmee input voor de synthese.
3. **Live zetten blijft handmatig en buiten het systeem.** Dat is de enige echte
   publicatiehandeling, en die hoort bij de auteur in wp-admin.

**Openstaand punt: wijzigingen die in WordPress zelf worden gemaakt.** `deploy_post.py`
overschrijft de concept-post. Redigeert de auteur tijdens het lezen in wp-admin, dan gaat dat
werk verloren bij de volgende deploy. Dat is geen theorie: bij deel 1 is de lokale draft
teruggezet naar de live formulering, juist om te voorkomen dat een volgende deploy de tekst
ongemerkt zou veranderen. Nu deployen vaker gaat gebeuren, wordt dit scherper. Mogelijke
antwoorden, nog te kiezen: tijdens het lezen niet in wp-admin redigeren maar opmerkingen
verzamelen, of de gepubliceerde tekst voor een deploy terughalen en verschillen melden.
Zolang dat niet is opgelost, geldt de eerste regel als werkafspraak.

### 3.5 Groeipad naar de afhankelijkheidsgraaf

Het mechanisme bestaat al. `state.deploy_approval` legt de sha256 van `draft.md` vast waaraan
de deploy-goedkeuring hangt, en `engine.deploy_approval_valid` laat de goedkeuring vervallen
zodra de tekst wijzigt. Diezelfde constructie wordt uitgebreid naar de controlerende
artefacten:

| artefact | verouderd zodra |
|---|---|
| `stijlcheck.md`, `leesbaarheid.md` | `draft.md` wijzigt |
| `reeks-check.md` | `draft.md` wijzigt |
| `feitencheck.md` | `draft.md` wijzigt |
| `archief-consistentie.md` | `draft.md` wijzigt |
| `grok-feedback.md` | **niet automatisch**; een tweede kritiekronde is een keuze van de auteur |
| visuals | de beeldverwijzingen of hun bijschriften wijzigen |

De uitzondering voor Grok is bewust en is de reden dat de graaf niet volledig mechanisch kan
zijn. Hij bevestigt de beslissing onder 3.2: het oordeel wanneer er opnieuw kritiek nodig is,
hoort bij de auteur.

Eerst `feitencheck.md` en `archief-consistentie.md`, want dat zijn de twee die op 15 augustus
met de hand opnieuw moesten en waar het misgaan het duurst is.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**
  - Van elf stempels naar drie beslissingen, elk op een moment waarop er iets te beslissen
    valt.
  - Het oordeelsmoment staat eindelijk in het systeem, op de plek waar het feitelijk al
    plaatsvond: na de concept-deploy, bij het lezen in WordPress.
  - Geen nieuwe leesomgeving te bouwen en te onderhouden.
  - De groeidruk van de synthese wordt zichtbaar gemaakt en bij de auteur belegd.
  - De vingerafdrukken maken "wat moet opnieuw" een berekening in plaats van een
    herinnering, en dekken het geval waar op 15 augustus met de hand omheen is gewerkt.
* **Negatief (-)**
  - Minder gates betekent minder gelegenheid om er per ongeluk een fout uit te vissen. De
    compensatie moet uit de controles komen, niet uit het aantal stopmomenten.
  - Deployen wordt een routinehandeling in plaats van een eindpunt. De concept-post wisselt
    daardoor vaker van inhoud, en de mediabibliotheek loopt vol met eerdere renders van
    dezelfde visual. Deel 2 heeft er nu twee paar staan.
  - Vier bestaande ADR's raken deels achterhaald op het punt van de gate-indeling. ADR-004
    (harde en zachte gates) vraagt een bijwerking; ADR-003 beschrijft de stepper als een
    lineaire bolletjesketen en moet de drie blokken gaan tonen.
* **Risico's**
  - **Redigeren in wp-admin tijdens het lezen gaat verloren** bij de volgende deploy. Zie
    3.4; zolang dat niet is opgelost geldt de werkafspraak dat opmerkingen worden verzameld
    en niet ter plekke doorgevoerd.
  - Een fout in de verouderingsregels levert stil overgeslagen controles op. Dat is dezelfde
    klasse fout als de omgekeerde score-regel in ADR-007 en het vastgelegde indexpad in
    ADR-006. Elke regel krijgt daarom een test die het verouderen aantoont, niet alleen het
    doorlaten.
  - Als de auteur in het Oordelen-blok net zo snel akkoord geeft als bij de elf gates,
    verandert er niets. Dat is te meten: hoe vaak leidt het Oordelen-blok tot een
    revisieronde, en hoe vaak wordt een Grok-punt verworpen.

---

## 5. Genomen besluiten

1. **Geen leesweergave in de web-UI.** WordPress blijft het leesmoment; de concept-deploy is
   de renderstap die dat mogelijk maakt (3.4).
2. **Meteen de clustering in drie blokken**, niet eerst alleen voorwaardelijke gates (3.1).

## 6. Uitvoeringsvolgorde

1. ~~Vingerafdruk uitbreiden naar `feitencheck.md` en `archief-consistentie.md`.~~
   **Uitgevoerd 2026-08-15.** `state.derived_from` legt bij `complete` vast van welke draft
   elk rapport is afgeleid; `run deploy` weigert zolang de feitencheck of de archiefcheck
   bij een oudere tekst hoort. Stijl- en reeksrapport worden wel geregistreerd maar
   blokkeren nog niet.

   Eén ontwerpkeuze daarbij: een fase **zonder** vastgelegde vingerafdruk telt niet als
   verouderd. Anders zou elke post van vóór deze registratie meteen vastlopen, ook als de
   rapporten prima klopten. Die gevallen leveren een informatieve melding in `doctor`, geen
   blokkade. Prijs: de eerste ronde na invoering is nog niet beschermd.
2. ~~Gates voorwaardelijk maken: alleen stoppen bij een bevinding.~~ **Uitgevoerd
   2026-08-15.** `style`, `series`, `factcheck` en `alignment` schuiven door zodra hun
   rapport geen `blocking`-bevinding bevat. Elk rapport opent met een json-blok met
   `findings`; `complete` weigert een rapport zonder dat blok, zodat de gate niet terugvalt
   op vertrouwen.

   Kernpunt: de twee zwaartes. De stijl-check vindt in vrijwel elke ronde kandidaten die
   geen overtreding zijn. Zonder het onderscheid tussen `blocking` en `advisory` zou de
   gate altijd afgaan en verandert er niets aan de 49 stempels. `factcheck` is daarmee geen
   onvoorwaardelijk harde gate meer; de bescherming komt nu uit drie eisen samen: het
   rapport moet bestaan, een leesbaar verdict hebben, en actueel zijn (stap 1).
3. De bevindingen van de vijf controles bundelen tot één overzicht per post.
4. De fases hergroeperen tot de drie blokken, met de stepper mee.
5. De synthese omzetten naar een beslismoment per punt, met vastlegging van de keuze en de
   motivering (3.3).
6. `revisie.md` invoeren als artefact voor de opmerkingen na het lezen.

Stap 1 tot en met 3 zijn losstaand bruikbaar; vanaf stap 4 verandert de zichtbare vorm van
de workflow.
