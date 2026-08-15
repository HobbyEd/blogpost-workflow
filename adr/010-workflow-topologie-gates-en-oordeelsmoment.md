# ADR-010: Workflow-topologie — waar de mens beslist en wat er opnieuw moet

* **Status**: Proposed
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

### 3.1 Nieuwe clustering: drie gates in plaats van elf

| blok | fases | gate |
|---|---|---|
| **Richten** | intake, outline | **echte gate**: onderwerp, invalshoek, bronnen |
| **Maken** | draft, Grok-kritiek, visuals | geen |
| **Toetsen** | stijl, leesbaarheid, reeks, feiten, archief | **alleen bij bevindingen** |
| **Oordelen** | lezen, becommentariëren, synthese, herzien | **echte gate**, met lus terug naar Maken en Toetsen |
| **Publiceren** | deploy | **echte gate** |

De Richten-gate is vandaag de meest verwaarloosde en de goedkoopste. Een verkeerde
invalshoek corrigeren kost daar tien minuten en na de draft twee uur. Bij deel 2 stond de
Sinek-sectie al in de outline; daar had de vraag "moet dit erin" thuisgehoord.

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

### 3.4 Leesweergave en opmerkingen in de web-UI

Na Maken en Toetsen toont de UI de gerenderde draft, met de visuals op hun plek, plus de
gebundelde bevindingen per sectie. De auteur kan per sectie een opmerking achterlaten. Die
opmerkingen worden een artefact (`revisie.md`) met dezelfde status als een bevinding van een
check, en zijn daarmee input voor de synthese.

Daarmee verschuift het oordeelsmoment van ná de deploy naar ervoor. De deploy-gate wordt wat
hij hoort te zijn: "zet dit klaar in WordPress", niet "laat mij eindelijk lezen wat er staat".

**Risico dat we accepteren en moeten meten:** de leesweergave lost het probleem alleen op als
hij ook gebruikt wordt. De huidige gewoonte is lezen in WordPress, in de opmaak van de eigen
site. Een preview die er net anders uitziet, nodigt uit tot "ik kijk straks wel in WP".

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
  - Het oordeel over de inhoud valt vóór publicatie in plaats van erna.
  - De groeidruk van de synthese wordt zichtbaar gemaakt en bij de auteur belegd.
  - De vingerafdrukken maken "wat moet opnieuw" een berekening in plaats van een
    herinnering, en dekken het geval waar op 15 augustus met de hand omheen is gewerkt.
* **Negatief (-)**
  - Minder gates betekent minder gelegenheid om er per ongeluk een fout uit te vissen. De
    compensatie moet uit de controles komen, niet uit het aantal stopmomenten.
  - Een leesweergave in de UI is nieuw werk dat naast WordPress komt te staan en de
    bestaande leesgewoonte moet verslaan.
  - Vier bestaande ADR's raken hierdoor deels achterhaald op het punt van de gate-indeling;
    ADR-004 vraagt een bijwerking zodra dit is aangenomen.
* **Risico's**
  - Een fout in de verouderingsregels levert stil overgeslagen controles op. Dat is dezelfde
    klasse fout als de omgekeerde score-regel in ADR-007 en het vastgelegde indexpad in
    ADR-006. Elke regel krijgt daarom een test die het verouderen aantoont, niet alleen het
    doorlaten.
  - Als de auteur in het Oordelen-blok net zo snel akkoord geeft als bij de elf gates,
    verandert er niets. Dat is te meten: hoe vaak leidt het Oordelen-blok tot een
    revisieronde, en hoe vaak wordt een Grok-punt verworpen.

---

## 5. Wat er nodig is om deze ADR te accepteren

1. Een besluit over de leesweergave: in de web-UI, of accepteren dat WordPress het
   leesmoment blijft en de lus daarop inrichten.
2. Een besluit over de omvang van de eerste stap: alleen voorwaardelijke gates en de
   gebundelde bevindingen, of meteen inclusief de clustering in drie blokken.

De uitbreiding van de vingerafdruk naar `feitencheck.md` en `archief-consistentie.md` kan
vooruitlopend hierop, want die staat los van de gate-indeling.
