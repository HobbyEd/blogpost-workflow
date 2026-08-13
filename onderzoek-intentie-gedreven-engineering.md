# Onderzoek — intentie-gedreven engineering en de rol van AI

Status: **open verkenning**, geen intake. Doel: een structuur vinden waar intentie-gedrevenheid
aan opgehangen kan worden, als fundament voor de volgende reeks. Aangemaakt 2026-08-08.

Bronnen: eigen materiaal (intentdriven.nl, augmentedorganisation.nl, edwinvandillen.nl) plus
externe theorie. Alle externe URL's zijn op 2026-08-08 opgehaald en gelezen tenzij anders vermeld.

---

## 1. Waarom dit onderwerp ertoe doet

### 1.1 Eén delegatieprobleem, vier oplossingen

Vier vakgebieden hebben onafhankelijk van elkaar hetzelfde probleem opgelost, en geen ervan verwijst
naar de andere. Het probleem: **hoe delegeer je werk aan een uitvoerder die het "hoe" zelf invult,
zonder de grip op het resultaat te verliezen?**

| Vakgebied | Oplossing | Het middel waarmee grip wordt behouden |
|---|---|---|
| Militaire doctrine (1800s) | Auftragstaktik / mission command | training en onderling vertrouwen, plus een expliciet *waarom* |
| Requirements engineering (1990s) | Goal-Oriented RE (KAOS, i*) | formalisering en traceerbaarheid van doel naar eis |
| Netwerkinfrastructuur (2010s) | Intent-Based Networking | continue meting; de gewenste toestand wordt bewaakt |
| AI-agents (2026) | context engineering na Claude 5 | modeloordeel, plus verificatie achteraf |

**Let op wat hier wél en niet geclaimd wordt.** De vier delen niet één mechanisme. Auftragstaktik
werkt via hiërarchie en gedeelde training, GORE via formele modellen, IBN via meetbare toestanden, en
context engineering via inferentie zonder formele garantie. Wie zegt dat ze "hetzelfde zeggen" doet
aan patroonherkenning op de formulering *zeg wat, niet hoe*, en die is te dun om iets op te bouwen.

Wat ze wél delen is de **probleemstelling** en de **randvoorwaarde**: delegeren aan een uitvoerder met
eigen oordeelsvermogen, en dus de noodzaak om de bedoeling over te dragen in plaats van de handeling.
Elk vakgebied heeft daar een ander middel voor gevonden om de grip te behouden.

Dat is bruikbaarder dan een convergentie-claim, want het levert een vraag op in plaats van een
constatering: **welk van die vier middelen past bij een AI-agent?** Vertrouwen en training laten zich
niet zomaar overzetten op een model. Formalisering botst met de reden dat je een agent inzet.
Continue meting is waarschijnlijk het meest overdraagbaar, en dat is precies waarom Intent-Based
Networking verderop het bruikbaarste leenmateriaal levert (§4.3).

**De consequentie die overeind blijft:** intentie-gedreven werken is geen AI-uitvinding, maar een
terugkerend antwoord op een oud delegatieprobleem. Dat geeft de reeks een fundament dat niet
meebeweegt met de volgende modelrelease.

### 1.2 De waardevraag: intentie is het enige dat waarde draagt

De vier tradities uit §1.1 verklaren waarom intentie *nu* actueel is. Ze verklaren niet waarom het
*ertoe doet*. Dat argument is ouder en harder, en het staat los van AI.

**Output zonder intentie is per definitie verspilling.** Dat is geen retoriek maar de kern van lean
denken: werk dat geen waarde toevoegt voor de ontvanger is waste, hoe efficiënt het ook is
uitgevoerd. Een feature factory kan tien features per sprint opleveren en netto negatieve waarde
produceren, doordat elke feature onderhoudslast en complexiteit toevoegt zonder dat iemand meet of
er iets veranderd is. intentdriven.nl noemt dat signaal expliciet: "Teams die releases vieren die
geen duidelijke zakelijke impact hebben."

**Eric Ries levert de scherpste formulering van het meetprobleem eronder.** Zijn begrip **vanity
metrics** beschrijft cijfers die stijgen zonder iets te bewijzen; ze laten mensen "form false
conclusions and live their own private realities". Daartegenover zet hij **validated learning**:
de enige echte voortgang is bewezen kennis over of je hypothese klopt, en **innovation accounting**:
voortgang meten aan leer-mijlpalen in plaats van aan bruto-output *(Ries, The Lean Startup, 2011)*.

Dat is precies de Output/Outcome-as uit het kwadrantmodel, vijftien jaar eerder en met een
meetmechanisme erbij. Velocity is een vanity metric. Story points zijn een vanity metric. Ze meten
of de fabriek draait, niet of er iets veranderd is.

**Chris Argyris verklaart waarom organisaties hierin blijven hangen.** Zijn onderscheid tussen
single-loop en double-loop learning is bijna letterlijk over dit onderwerp geschreven: single-loop
learning treedt op wanneer men "mismatches between intentions and outcomes" corrigeert "by changing
actions without questioning or altering the governing values"; double-loop learning corrigeert door
éérst die onderliggende waarden te onderzoeken *(bron:
[infed.org, "Chris Argyris: theories of action, double-loop learning and organizational
learning"](https://infed.org/dir/welcome/chris-argyris-theories-of-action-double-loop-learning-and-organizational-learning/);
[Wikipedia, "Double-loop learning"](https://en.wikipedia.org/wiki/Double-loop_learning))*.

**Een organisatie die alleen single-loop leert, kan uitsluitend optimaliseren wat ze al doet.** Dat
is de theoretische onderbouwing van "we doen dit omdat we het altijd zo deden": geen gebrek aan
intelligentie of inzet, maar een lus die nooit bij de aanname komt. Argyris schreef dit in de jaren
zeventig. Het is dus geen AI-probleem en ook geen nieuw probleem.

**Design thinking zet hetzelfde in ruimtelijke vorm.** Het Double Diamond-model van de Britse Design
Council (2005) verdeelt het werk in twee ruiten: Discover en Define vormen de *probleemruimte*,
Develop en Deliver de *oplossingsruimte*. De eerste ruit is intentiewerk. En de kritiek die het veld
op zichzelf heeft is veelzeggend: ontwerpers besteden aandacht aan onderzoek en prototyping, maar
"less on the problem definition itself", terwijl juist daar de innovatie zit
*(bron: [Designorate, "The Double Diamond Design Thinking Process"](https://www.designorate.com/the-double-diamond-design-thinking-process-and-how-to-use-it/))*.

Twee dingen vallen daarbij op die de reeks kan gebruiken. De Double Diamond legt zich vrijwel
naadloos over het Centrale Dogma van intentdriven.nl: Problem Space en Mental Models vormen de
eerste ruit, Solution Space en Implementation Space de tweede. Dat is externe bevestiging van een
eigen model. En de zelfkritiek van het ontwerpveld is dezelfde als die van engineering: de
probleemdefinitie is de fase die iedereen overslaat.

**Waar AI dan wél binnenkomt.** Niet als reden, maar als versneller en als ontnuchtering:

1. **De bouwkosten storten in.** Toen bouwen duur was, was tijd besteden aan intentie een luxe die
   je moest verdedigen. Nu bouwen goedkoop is, is weten wát je moet bouwen de enige overgebleven
   schaarse input. Kief Morris' bottleneck-argument is hiervan de empirische kant: agents genereren
   sneller dan mensen kunnen inspecteren, en een deel van de teleurstellende productiviteitscijfers
   komt doordat mensen "more time specifying and reviewing code than they save" besteden (§6.4).
2. **Verkeerd bouwen wordt goedkoper en dus onzichtbaarder.** Verspilling die vroeger pijn deed
   omdat ze maanden kostte, kost nu dagen. Daarmee verdwijnt het natuurlijke correctiemechanisme:
   de pijn die je dwong om na te denken.
3. **Declaratief aansturen wordt pas nu mogelijk.** Dat is §5: modellen met genoeg oordeelsvermogen
   kunnen met een bedoeling werken in plaats van met een instructie.

**Kandidaat-openingsstelling voor de reeks:** *AI heeft intentie niet belangrijk gemaakt. Het heeft
alleen de laatste smoes weggenomen om er niet mee te beginnen.*


### 1.3 Waarom nu wél, terwijl Ries en Argyris nooit breed zijn omarmd

Dit is de scherpste tegenwerping tegen de hele reeks, en hij moet vooraan beantwoord worden.
Validated learning is vijftien jaar oud, double-loop learning vijftig. Beide zijn breed bekend en
smal toegepast. Waarom zou intentie-gedrevenheid nu wél landen?

Het antwoord is niet dat het idee beter is geworden, en ook niet dat andere continenten slimmer
zijn. Het is dat het **vertaalprobleem** oplosbaar is geworden.

Dat onderscheid is belangrijk, want de voor de hand liggende redenering is een drogreden. "China en
de VS innoveren sneller, dus intentie-gedreven werken loont" veronderstelt causaliteit die niet is
aangetoond: kapitaal, schaal, demografie en regulering verklaren dat verschil minstens zo goed.
Europa heeft bovendien al decennia intentie-gedreven kaders, van Europese normalisatie tot
systeemengineering-standaarden. Het idee ontbreekt hier niet.

**Wat wel ontbreekt is de vertaallaag: van gedeclareerde bedoeling naar toetsbare uitvoering.** Dat
is een preciezere diagnose, hij is met eigen waarneming te onderbouwen, en hij geldt evengoed binnen
één organisatie als tussen continenten.

**De demografische intentie is hard en meetbaar.** China telde eind 2024 310 miljoen mensen van 60
jaar en ouder, met een verwachting van meer dan 400 miljoen in 2035, en de beroepsbevolking krimpt
er met 7 à 8 miljoen per jaar
*(bron: [Xinhua, "As China tackles aging, elderly-care robots hit fast
track"](https://english.news.cn/20250314/d7d55e23492046019900e57d77dc9fb9/c.html))*. Japan gaat
volgens de OESO tussen 2023 en 2060 nog eens 31% van zijn beroepsbevolking verliezen. Dat is geen
technologievraagstuk maar een intentie: er moet zorg en productie geleverd blijven worden met
structureel minder mensen.

**China vertaalt die intentie naar beleid.** Het Ministerie van Industrie en Informatietechnologie
heeft samen met het Ministerie van Civiele Zaken een landelijk pilotprogramma opgezet voor robotica
in de ouderenzorg, met richtlijnen die humanoïde robots, brain-computer interfaces en exoskeletten
expliciet noemen
*(bron: [SCMP, "China turns to robots for elderly care with national pilot
programme"](https://www.scmp.com/tech/policy/article/3313739/china-turns-robots-elderly-care-national-pilot-programme);
[gov.cn, "China to promote use of humanoid robots for elderly
care"](https://english.www.gov.cn/policies/latestreleases/202501/07/content_WS677d340ac6d0868f4e8ee95d.html))*.

**In de VS gebeurt hetzelfde via de fabrieksvloer.** BMW zet Figure 02-robots in bij zijn fabriek in
Spartanburg voor onderdelenafhandeling en kwaliteitsinspectie; Mercedes-Benz test Apptronik Apollo
voor zwaar materiaaltransport. De achterliggende cijfers zijn van dezelfde soort: circa 600.000
onvervulde productiebanen in de VS, en een tekort in de ouderenzorg dat richting een miljoen gaat
in 2030.

**En Europa?** Op 16 juni 2026 stemde het Europees Parlement definitief in met aanpassing van de
AI-verordening; op 27 juli 2026 trad de AI Omnibus in werking, met verlenging van de deadline voor
standalone hoog-risicosystemen naar 2 december 2027 en voor ingebouwde systemen naar 2 augustus 2028
*(bron: [Europees Parlement, "Digital Omnibus on
AI"](https://www.europarl.europa.eu/RegData/etudes/BRIE/2026/782651/EPRS_BRI(2026)782651_EN.pdf);
[Europese Commissie, "AI Omnibus enters into
force"](https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force))*.

**Hier zit een nuance die het verhaal beter maakt dan de gangbare lezing.** Het uitstel is niet
primair een beleidsmatige koerswijziging omdat men inzag dat de regels innovatie smoorden. De
belangrijkste reden is dat de **Europese technische normen die de nalevingsroute moeten definiëren
zelf vertraagd zijn** en niet vóór eind 2027 worden verwacht.

Dat is precies het faalpatroon uit §4.3, en het is bijna te mooi om te laten liggen: **Europa heeft
een intentie gedeclareerd zonder werkende vertaallaag naar implementatie.** In IBN-termen: intent
zonder translation, en dus ook zonder assurance. De regels bestaan, maar niemand kan aantonen dat
hij eraan voldoet, want de meetlat is er niet. Dat is geen overregulering; het is een onafgemaakte
intentielus.

**De stelling die hieruit volgt:** het onderscheid dat telt is niet wie de beste bedoeling heeft,
maar wie de lus sluit. China vertaalt een demografische intentie naar beleid, pilots en meetbare
inzet. Europa heeft de intentie op papier en de meetlat nog niet. Binnen organisaties werkt dat
precies zo: iedereen kan een outcome formuleren, en bijna niemand kan aantonen of hij hem haalt.

Waarom dit nú telt en bij Ries en Argyris niet: zij beschreven de lus zonder dat de vertaalslag
betaalbaar was. Elke uitkomstmeting kostte handwerk. Wat er veranderd is, is dat het declareren,
uitvoeren en toetsen van intentie voor het eerst grotendeels geautomatiseerd kan worden. Dat maakt
van een goed idee een uitvoerbare praktijk.

**Redactionele waarschuwing bij dit uitstapje.** Dit blijft een uitstapje, geen hoofdmoot, en het
heeft drie valkuilen. Het mag niet vervallen in een klaagzang over Brussel: de omnibus is deels een
correctie op een uitvoeringsprobleem, niet op de ambitie zelf. Het mag ook niet terugvallen op de
post-hoc-redenering dat andere continenten sneller gaan omdát ze intentie-gedreven zijn; die
causaliteit is niet aangetoond en een criticus prikt er meteen doorheen. En het gewapende-robot-voorbeeld
hoort er niet in. Dat dient een heel andere intentie dan vergrijzing, het is niet met primaire
bronnen te onderbouwen, en "China is op de goede weg" naast bewapening laat zich niet lezen zoals
bedoeld. Het ondergraaft juist het punt, want het bewijst dat intentie-gedreven handelen op zichzelf
niets zegt over de *waarde* van de intentie. Als dat punt wél gemaakt moet worden, hoort het in een
eigen alinea: intentie-gedreven werken maakt richting expliciet, en daarmee ook bespreekbaar of het
de juiste richting is.

### 1.4 Drie lussen, en waarom de meeste organisaties er maar één hebben

Uit het bovenstaande komt een kader dat de hele reeks kan dragen. **Het is nadrukkelijk een
integratiekader en geen nieuw model:** lus 1 is gewone verificatie, lus 2 combineert validated
learning met IBN-assurance, en lus 3 is Argyris' double-loop. De waarde zit in de stapeling, de
volgorde-eis en de diagnose per kwadrant, niet in een nieuw mechanisme. Dat expliciet zeggen is
sterker dan het verzwijgen, want een lezer die Argyris kent prikt er anders doorheen.

| Lus | Vraag | Herkomst | Wie heeft hem |
|---|---|---|---|
| 1. Bouwlus | Hebben we het goed gebouwd? | tests, review, CI | iedereen |
| 2. Uitkomstlus | Heeft het opgeleverd wat we bedoelden? | assurance (IBN), validated learning (Ries) | weinigen |
| 3. Intentielus | Was dat wel de juiste bedoeling? | double-loop learning (Argyris) | zeldzaam |

De diagnose die hieruit volgt is scherper dan "stuur op outcome in plaats van output":

- De **Feature Factory** heeft alleen lus 1 en noemt het klaar bij deploy.
- De **Korte-termijn Optimizer** heeft lus 1 en 2, maar lokaal: hij ziet zijn eigen uitkomst en niet
  het effect elders.
- De **Over-Engineered Architect** heeft lus 1 en een verbeelde lus 3: hij bevraagt de intentie wel,
  maar zonder toetsing, en vult de open ruimte speculatief in.
- De **Strategische Orchestrator** heeft alle drie, en cruciaal: lus 3 gevoed door lus 2, dus
  bevraging van de bedoeling op grond van waargenomen uitkomst in plaats van op grond van mening.

**En hier zit het punt over leren van je eigen voortbrengsel.** Lus 3 heeft brandstof nodig, en die
brandstof is wat je gebouwd hebt. Het artefact laat zien wat je werkelijk bedoelde: dat is het
prototype-als-spiegel-argument uit §4.2, het is Naur's theorie die zichtbaar wordt in code (§8), en
het is Ries' validated learning. Innovatie ontstaat niet door beter vooraf na te denken, maar door
het gebouwde terug te lezen als uitspraak over je eigen intentie.

Dat maakt de volgorde bovendien onomkeerbaar: je kunt lus 3 niet draaien zonder lus 2, want dan
bevraag je je aannames op basis van niets.

**Hoe houd je lus 2 en 3 in de praktijk uit elkaar?** Dit is een reële lacune, want zonder scherpe
scheiding vallen ze samen of vervalt lus 3 in meningsvorming. Drie criteria die het onderscheid
operationeel maken:

- **Wat er ter discussie staat.** Lus 2 neemt de bedoeling als gegeven en toetst de uitkomst. Lus 3
  neemt de uitkomst als gegeven en toetst de bedoeling. Zodra beide tegelijk bewegen, weet je niets.
- **Het ritme.** Lus 2 draait per release of per periode en hoort geautomatiseerd te zijn. Lus 3
  draait zelden, is per definitie mensenwerk, en hoort een expliciet moment te zijn in plaats van een
  permanente twijfel. Een organisatie die haar intentie continu bevraagt heeft geen intentie.
- **Wie hem draait.** Lus 2 hoort bij het team dat levert. Lus 3 hoort bij wie de intentie mag
  wijzigen. Vallen die samen, dan is lus 3 een slager die zijn eigen vlees keurt.

Zonder deze scheiding is het onderscheid retorisch. Dat is een punt om in deel 8 expliciet te maken,
niet om impliciet te laten.


---

## 2. Wat is intentie eigenlijk?

### 2.1 De definitie die het scherpst is

Goal-Oriented Requirements Engineering geeft de bruikbaarste formele definitie. Een doel is
"a prescriptive statement of intent the system should satisfy through cooperation of its agents"
*(bron: van Lamsweerde, "Requirements Engineering: From Craft to Discipline", FSE'08, §2.1,
https://webperso.info.ucl.ac.be/~avl/files/avl-fse08.pdf)*. Dat het hoe daarbij openblijft volgt
uit de tegenstelling die hij elders maakt: doelen zijn "abstract, declarative, and make intended
properties explicit", terwijl scenario's "concrete, narrative, procedural" zijn en de bedoeling
impliciet laten *(bron: van Lamsweerde, "Goal-Oriented Requirements Engineering: A Guided Tour",
RE'01, https://webperso.info.ucl.ac.be/~avl/files/RE01.pdf)*.

> **Correctie 2026-08-11.** Hier stond eerder het citaat *"one can state a goal without having
> to specify how it is to be achieved"*, toegeschreven aan RE'01. Die zin staat in geen van beide
> papers; ik heb de volledige tekst van RE'01 en FSE'08 doorzocht. De definitie stond bovendien
> aan het verkeerde paper toegeschreven en week af van de letterlijke formulering ("intention"
> in plaats van "intent", "the cooperation of agents" in plaats van "cooperation of its agents").
> Deel 1 nam het foute citaat over en is gecorrigeerd.

Twee dingen zitten daarin die de hele reeks kunnen dragen:

- **Intentie is scheidbaar van uitvoering.** Je kunt hem volledig formuleren zonder één
  implementatiebesluit te nemen. Dat is precies wat een specificatie *niet* is.
- **Intentie veronderstelt samenwerkende agents.** De definitie noemt letterlijk "cooperation of
  agents". Geschreven in 2001 over mensen en systemen; nu bruikbaar zonder één woord aanpassing.

### 2.2 Een werkbare laagindeling

Uit het materiaal komt een consistente trap, van vaag naar hard. Dit is kandidaat-nummer één voor
de structuur waar je naar zoekt:

1. **Motief** — waarom iemand iets wil. Zit in de mens, vaak onuitgesproken, soms voor de persoon
   zelf niet toegankelijk.
2. **Intentie** — welke verandering in de wereld beoogd is. Declaratief, toetsbaar op uitkomst,
   nog vrij van oplossing.
3. **Doel / outcome** — dezelfde intentie, maar meetbaar gemaakt. Hier komt de meetvraag binnen.
4. **Specificatie** — wat het systeem moet doen. Nog steeds niet hoe.
5. **Implementatie** — hoe.

Het Vibe · Spec · Harness-frame legt hier direct overheen: Vibe = laag 1 en 2, Spec = laag 3 en 4,
Harness = de begrenzing waarbinnen laag 5 mag bewegen. Dat is een sterke aanhaking, want het
verbindt de nieuwe reeks met bestaand eigen werk zonder het te herhalen.

### 2.3 Commander's intent als het rijkste bestaande model

De militaire variant is 200 jaar ouder en verder uitgedacht dan alles in software. Auftragstaktik
is "the doctrine of communicating what needs to be accomplished and why, then trusting
subordinates to determine how". De kern die voor ons telt: intent is expliciet ontworpen om
**bruikbaar te blijven als de omstandigheden veranderen**. Het klassieke argument is dat de
oorspronkelijke opdracht achterhaald raakt door onverwachte ontwikkelingen, en dat de ondergeschikte
dan alsnog het juiste kan doen omdat hij de bedoeling kent *(bron: Wikipedia, "Mission-type
tactics", https://en.wikipedia.org/wiki/Mission-type_tactics; US Army, "Mission command requires
sharp commander's intent", https://www.army.mil/article/215297/mission_command_requires_sharp_commanders_intent)*.

**Dit is het sterkste argument vóór intentie-gedreven werken met agents,** en het is geen
AI-argument. Een agent die alleen de instructie heeft, faalt zodra de situatie afwijkt. Een agent
die de bedoeling kent, kan afwijken op de juiste manier. Precies het verschil dat Anthropic
empirisch tegenkwam (zie §5).

Let op de eerlijke tegenwerping: mission command werkt in het leger alleen bij **hoge training en
hoog onderling vertrouwen**. De AUSA-publicatie stelt expliciet dat het Amerikaanse leger er
decennia mee worstelt en dat de doctrine breed verkeerd begrepen wordt
*(https://www.ausa.org/publications/misinterpretation-and-confusion-what-mission-command-and-can-us-army-make-it-work)*.
Dat is een waarschuwing die één-op-één overzet: intentie-gedreven werken is geen instelling die je
aanzet, het is een competentie die je opbouwt. Dat is ook precies wat de kwadranten in §7 zeggen.

### 2.4 De Golden Circle: bruikbaar frame, zwak fundament, en één belangrijke correctie

Sineks Golden Circle (why → how → what) is de formulering die het publiek van deze reeks al kent,
en hij zegt precies wat §2.1 formeel zegt: begin bij de bedoeling, niet bij het ding. Als
gemeenschappelijke vocabulaire is hij daarom bruikbaar. Als fundament niet, om twee redenen die je
beter zelf benoemt dan dat een lezer ze aandraagt.

**De onderbouwing die Sinek erbij levert, houdt geen stand.** Hij koppelt de drie ringen aan
hersenanatomie (het *what* aan de neocortex, het *how* en *why* aan het limbisch systeem) en stelt
daarbij expliciet: "None of this is my opinion. It is all firmly grounded in the tenets of
biology." Dat is precies de claim die niet klopt. Het idee van een anatomisch en functioneel
afgebakend limbisch systeem is achterhaald in de moderne neurowetenschap, en de scheiding tussen
"emotionele" en "rationele" beslissingen over aparte hersengebieden bestaat zo niet
*(bron: [Praise & Criticism: The Golden Circle (Sinek)](https://blog.hptbydts.com/praise-criticism-the-golden-circle-sinek);
[The Lizard Brain Myth, Shortform](https://www.shortform.com/blog/lizard-brain-myth/))*.
Gebruik de Golden Circle dus als taal, en laat het gewicht dragen door Polanyi (§3.1), Naur en
GORE (§2.1). Eén zin volstaat: de Golden Circle populariseerde een onderscheid dat in requirements
engineering al langer geformaliseerd was.

**De inhoudelijke correctie is interessanter dan de kritiek.** Sinek gaat ervan uit dat het *why*
er is en alleen gecommuniceerd hoeft te worden; zijn hele model is een communicatiemodel. Het
materiaal in §3 zegt iets anders en scherper: het *why* is vaak niet gekend door degene die het
zou moeten uitspreken. Dat is Polanyi, en het is precies waarom kenniselicitatie op intentdriven.nl
"een archeologische handeling" heet en geen communicatieoefening.

**Daarmee is dit een kandidaat voor de scherpe stelling van het openingsdeel:** *begin bij het
waarom is een onvolledig advies, want het waarom ligt er meestal niet.* Dat corrigeert een bekend
model zonder het af te serveren, en het zet meteen de rest van de reeks op (als het waarom er niet
ligt, is de vraag hoe je het bovengraaft, en dat is §4).

---

## 3. Waarom intentie bijna altijd impliciet is

### 3.1 Polanyi, en waarom het geen retoriek is

"We can know more than we can tell" (Polanyi, 1966) staat al in
[?p=384](https://edwinvandillen.nl/?p=384) en is daar goed geplaatst: het is een beschrijving van
het mechanisme, geen aforisme. De domeinexpert weet wat het systeem moet doen, maar die kennis is
zo ingebed in routine dat ze niet als kennis herkend wordt.

intentdriven.nl formuleert dezelfde beweging als een verplaatsing: van **onbewuste bekwaamheid**
(de staat van de expert) naar **bewust modelleren**. Kenniselicitatie heet daar "een
archeologische handeling": je graaft naar het waarom achter het hoe.

### 3.2 De grens die je eerlijk moet benoemen

Hier zit de belangrijkste theoretische vondst, en hij gaat tegen de intuïtieve ambitie in.

Nonaka's SECI-model (socialisatie, externalisatie, combinatie, internalisatie) is het standaard-
model voor tacit → explicit. Maar de kritiek erop is substantieel en relevant: Nonaka behandelt
tacit en explicit als **scheidbaar en converteerbaar**, terwijl Polanyi's oorspronkelijke idee is
dat tacit kennis deels of geheel **inherent** tacit is. Gourlay en Nurse vatten de kritiek van
Griffin, Shaw en Stacey (1999) zo samen: "Nonaka has subordinated Polanyi's (1969a, 1969b)
concept of tacit knowledge to an objectivist strategic management theory". Over de kern van het
model zijn ze zelf stelliger: de externalisatie-stap rust op de hypothese dat tacit kennis via
metaforen en analogieën naar buiten komt, en dat is "a hypothesis that is not supported by
evidence or theory" *(bron: Gourlay en Nurse, "Flaws in the engine of knowledge creation",
https://realkm.com/wp-content/uploads/2023/11/Flaws_in_the_engine_of_knowledge_creation.pdf)*.

> **Correctie 12 augustus 2026.** Hier stond eerder het citaat *"much more complex and less prone
> to be managed"*. Die zin komt in de bron niet voor; ik heb de volledige PDF doorzocht. Het
> citaat over "subordinated to an objectivist strategic management theory" stond bovendien in een
> vorm die niet letterlijk is en zonder de attributie aan Griffin, Shaw en Stacey. De
> scispace-URL geeft 403 en is verwijderd. Dit is de tweede fantoomcitaat-vondst in dit document,
> na de van Lamsweerde-zin in §2.1.

**Consequentie voor de reeks:** volledige explicitering van intentie is niet haalbaar, en een
reeks die dat belooft is onhoudbaar. Wat wel kan is de expliciete laag *snel genoeg* en *rijk
genoeg* maken om te handelen, met een mechanisme dat corrigeert waar de impliciete rest je inhaalt.
Dat maakt de meetlus uit §4.3 geen bijzaak maar een noodzaak: hij vangt op wat de explicitering
principieel mist.

Dit sluit ook aan bij het eigen materiaal: intentdriven.nl zegt over mentale modellen dat afwijking
tussen mensen "de standaard" is en "geen fase die je doorloopt op weg naar volledig begrip. Het is
een permanente conditie."

### 3.3 Een derde categorie die vaak wordt overgeslagen

Explicit / tacit is een tweedeling die te grof is voor dit onderwerp. Bruikbaarder is een drietrap:

- **Expliciet** — opgeschreven, overdraagbaar.
- **Impliciet** — niet opgeschreven maar wél vertelbaar zodra iemand ernaar vraagt. Dit is de
  grootste categorie in de praktijk, en de goedkoopste om te winnen.
- **Tacit** — niet vertelbaar, alleen zichtbaar in gedrag. Alleen te bereiken via observatie,
  voorbeelden of samen doen.

Het onderscheid is operationeel, want elke categorie vraagt een **andere techniek** (§4). De fout
die je in de praktijk ziet is dat teams interviewtechnieken inzetten op tacit kennis, waar
observatie nodig was.

### 3.4 Cynefin, en waarom Disorder hier het interessante domein is

Cynefin verklaart iets wat het kwadrantmodel in §7 alleen constateert: *waarom* bepaalde mensen
declaratieve intenties terugduwen naar opdrachten. Dat is geen karaktertrek maar een gedocumenteerd
mechanisme.

**Het mechanisme.** Disorder is de toestand waarin je niet weet in welk domein je zit. Snowden en
Boone beschrijven daarbij expliciet wat er dan gebeurt: het is "the state of not knowing what type
of causality exists, in which state people will revert to their **own comfort zone** in making a
decision" *(bron: Snowden & Boone, "A Leader's Framework for Decision Making", HBR november 2007,
https://hbr.org/2007/11/a-leaders-framework-for-decision-making)*. Wie gewend is aan
Clear-terrein valt dus terug op best practices en een opdrachtenlijst, ook als het terrein dat niet
toelaat.

**Waarom dat hier precies landt.** Een intentiegesprek speelt zich per definitie af in Complex
terrein: in dat domein "cause and effect can only be deduced in retrospect", en de passende houding
is *probe → sense → respond*. In Clear is dat *sense → categorise → respond*, met vaste constraints
*(bron: [Cynefin Domains, cynefin.io](https://cynefin.io/wiki/Cynefin_Domains))*. Iemand die een
ambigue intentie als Clear behandelt, categoriseert hem dus: hij herkadert "welke verandering
willen we bereiken" naar "welke tickets horen hierbij". De intentie gaat verloren in de vertaling,
en dat is geen onwil maar de juiste reflex in het verkeerde domein.

**Dit is de verklaring onder jouw kwadrant-observatie.** Feature Factory (Output × Lineair) is
Clear-gedrag. Dat verklaart waarom declaratieve intentie-explicitatie daar niet aanslaat, en ook
waarom trainen op "beter luisteren" niet werkt: het probleem zit in de domeininschatting, niet in
de gespreksvaardigheid.

**De begrenzing voor het meten (§4.3).** In Complex terrein is causaliteit alleen achteraf
zichtbaar. Een intentie die je vooraf volledig in KPI's vangt, heb je daarmee impliciet als
Complicated behandeld. De assurance-lus uit intent-based networking blijft bruikbaar, maar alleen
voor het deel van de intentie dat je hebt kunnen formaliseren. Dat is dezelfde grens als de
Nonaka-kritiek in §3.2, nu vanuit een tweede richting bevestigd. Twee onafhankelijke tradities die
op dezelfde muur uitkomen, is een sterker argument dan één.

**Detail dat goed rijmt met eigen materiaal.** Snowden heeft Disorder later gesplitst in
**confused** en **aporetic**: "authentic disorder becoming 'aporetic' and inauthentic disorder
'confused'", waarbij confused "the result of a failure to see past one's own biases, habits, and
entrained patterns" is, en aporia een bewuste, productieve staat van niet-weten
*(bron: [Aporetic Turn, cynefin.io](https://cynefin.io/wiki/Aporetic_Turn))*. Dat is precies de
uitspraak op intentdriven.nl dat leiders een cultuur moeten koesteren waarin "ik begrijp het nog
niet" een respectabele positie is. Het onderscheid is bruikbaar: de Feature Factory zit in
*confused* disorder, het goede intentiegesprek begint in *aporetic* disorder.

**Naamgeving, let op bij schrijven.** Het eenvoudigste domein heet sinds 2015 **Clear**; daarvoor
Obvious (2014) en Simple (2007), oorspronkelijk Known (2003). Gebruik Clear, en noem de oude naam
hooguit één keer tussen haakjes.

---

## 4. Technieken: hoe kom je zo snel mogelijk bij de echte intentie?

### 4.1 Wat er al is, geordend naar kennissoort

| Kennissoort | Techniek | Werkt omdat |
|---|---|---|
| Impliciet | Socratisch doorvragen, Three Amigos, Discovery workshops | de expert kán het vertellen, er wordt alleen nooit gevraagd |
| Impliciet → expliciet | Example Mapping, Specification by Example | voorbeelden liggen dichter bij de ervaring dan regels |
| Tacit (collectief) | Event Storming, gezamenlijk modelleren | botsing tussen mentale modellen maakt aannames zichtbaar |
| Tacit (individueel) | observatie, meelopen, prototype als spiegel | gedrag toont wat taal niet bereikt |

intentdriven.nl heeft hier al een scherpe formulering voor de Solution Space die het waard is te
hergebruiken: *"Een diagram waar niemand het mee oneens was, is waardeloos."* De waarde zit in het
argument dat een model uitlokt, niet in het model.

### 4.2 Wat AI hieraan toevoegt, in drie verschillende rollen

Dit is het punt waar de reeks nieuw kan zijn, want de rollen worden meestal op één hoop gegooid.

**Rol 1 — AI als interviewer (actief, synchroon).** Dit is [?p=384](https://edwinvandillen.nl/?p=384):
socratisch doorvragen dat niet meer afhangt van de beschikbaarheid van een ervaren requirements
engineer. De winst is schaal en consistentie, niet kwaliteit-per-gesprek.

**Rol 2 — AI als observator (passief, asynchroon).** Dit is nieuw en het is jouw Claude Tag-punt.
Anthropic lanceerde op 23 juni 2026 Claude Tag, met een configureerbare **ambient mode** waarin
Claude meeleest in Slack-kanalen en proactief signaleert wat relevant is en welke draden zijn
doodgelopen *(bron: Anthropic, "Introducing Claude Tag",
https://www.anthropic.com/news/introducing-claude-tag; TechCrunch, 23 juni 2026,
https://techcrunch.com/2026/06/23/anthropics-claude-tag-is-learning-your-company-one-slack-message-at-a-time/)*.
De oude Claude-in-Slack-app is per 3 augustus 2026 uitgefaseerd.

Waarom dit theoretisch interessant is: observatie is precies de techniek die de literatuur
voorschrijft voor **tacit** kennis, en het is de techniek die tot nu toe het slechtst schaalde. Een
mens kan niet in twintig kanalen meelezen. Dit is dus geen versnelling van bestaande elicitatie
maar een nieuwe elicitatiemodus.

Waarom je er meteen een kanttekening bij moet zetten: passief meelezen is een surveillance-vraag
zodra het over mensen gaat, en de kwaliteit van wat je zo wint is ongetoetst. Dit verdient in de
reeks een eerlijke behandeling, niet een enthousiaste.

**Rol 3 — AI als spiegel (genererend).** Het prototype dat toont wat je gevraagd hebt, waardoor je
ziet wat je bedoelde. Zit al in [?p=384](https://edwinvandillen.nl/?p=384) met de opdrachtgeefster
die dacht dat ze wist wat ze wilde. Dit is de snelste route naar tacit kennis die er bestaat, want
het omzeilt taal.

Er is ook academisch werk dat SECI expliciet met generatieve AI verbindt: "Tacit Knowledge
Management with Generative AI: Proposal of the GenAI SECI Model" (arXiv 2603.21866,
https://arxiv.org/pdf/2603.21866). **Nog niet gelezen**; kandidaat voor verdieping als de reeks
deze kant op gaat.

### 4.3 Meten: de lus die het vakgebied al heeft uitgevonden

Je vroeg hoe je meet of de intentie ook bereikt wordt. Het beste bestaande antwoord komt uit een
onverwachte hoek: **Intent-Based Networking**. Dat vakgebied heeft een gesloten lus met vier fasen
die één-op-één overzet naar software-engineering:

1. **Translation** — declaratieve intentie omzetten naar beleid en configuratie. "The translation
   element enables the operator to focus on *what* they want to accomplish, and not *how*."
2. **Activation** — uitrollen.
3. **Assurance** — "continuous verification that the network is operating as intended", dus
   doorlopend toetsen of het werkelijke gedrag de intentie nog dekt.
4. **Optimization** — bijsturen bij afwijking.

*(bron: HPE, "What is Intent-Based Networking?", https://www.hpe.com/us/en/what-is/intent-based-networking.html;
Cisco, https://blogs.cisco.com/analytics-automation/why-is-intent-based-networking-good-news-for-software-defined-networking)*

Het bijbehorende begrip dat je kunt lenen is **intent drift**: de situatie waarin het systeem nog
draait zoals geconfigureerd, maar niet meer doet wat bedoeld was. Er is recent werk dat dit
detecteert door laag-niveau gedrag tegen hoog-niveau intentie te leggen (arXiv 2606.05076,
https://arxiv.org/pdf/2606.05076). **Nog niet gelezen**, maar de term alleen al is bruikbaar:
intent drift is het meetbare falen van intentie-gedreven werken, en het is precies wat een
feature-factory nooit opmerkt omdat die op output stuurt.

**Assurance is de zwakste schakel in de meeste organisaties.** Translation doet iedereen (dat heet
een backlog), activation ook (dat heet een release). Assurance en optimization worden overgeslagen,
en dat is waarom output-sturing blijft bestaan: het is de enige lus die wél sluit.

Er bestaat inmiddels ook een expliciet meetbegrip: **intent alignment**, gebruikt door Thoughtworks
in hun SPDD-methode (zie §6.3). Dat het begrip bestaat is bruikbaar; het gepubliceerde getal rust op
één casus.

Aanvullend uit de AI-hoek: Anthropic beschrijft **rubrics** als beoordelingscriteria die
verifier-agents gebruiken om "smaak" te toetsen (wat is goed API-design). Dat is assurance op een
kwaliteit die je niet in een test kunt vangen, en het is een concreet mechanisme om een deel van de
tacit laag toch toetsbaar te maken.

---

## 5. De declaratieve wending in de modellen zelf

Dit is jouw scherpste observatie en hij houdt stand.

Anthropic verwijderde **meer dan 80% van het system prompt van Claude Code** voor Opus 5 en Fable 5
zonder meetbaar verlies op coding-evaluaties. De reden: ze hadden het model *overconstrained*, en
tegenstrijdige regels botsten binnen één verzoek ("documenteer waar relevant" tegenover "voeg GEEN
commentaar toe"). Oudere modellen hadden harde regels nodig om worst-case-gedrag te voorkomen;
nieuwere hebben genoeg oordeelsvermogen om zonder te kunnen
*(bron: Thariq Shihipar, "The new rules of context engineering for Claude 5 generation models",
24 juli 2026, https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)*.

De verschuiving die daaruit volgt, in hun eigen woorden: van *"never write multi-paragraph
docstrings"* naar *"write code matching its comment density, naming, and idiom"*. Dat is exact het
verschil tussen imperatief en declaratief. Het tweede beschrijft een **gewenste toestand** en laat
het hoe open.

Twee van hun zes verschuivingen zijn extra relevant voor de intentie-lijn:

- **Voorbeelden → interface-ontwerp.** Voorbeelden geven bleek het model te *beperken* tot een
  smalle exploratieruimte. Beter is een expressiever ontworpen tool, waarbij een enum
  (`pending|in_progress|completed`) het gedrag stuurt zonder uitleg. Vertaald naar intentie: **de
  vorm waarin je de intentie giet stuurt het gedrag sterker dan de instructie erbij.** Dat is een
  ontwerpprincipe, geen prompt-truc.
- **Simpele specs → rijke referenties.** Verwijzen naar testsuites, HTML-artefacten en rubrics in
  plaats van naar beschrijvingen. Hogere fidelity. Dit is het prototype-als-spiegel-argument uit
  §4.2, nu vanuit de andere kant.

**De brug die de reeks kan slaan:** dit is commander's intent, herontdekt door een AI-lab, met
dezelfde logica (uitvoerder met oordeelsvermogen krijgt bedoeling in plaats van instructie) en
dezelfde randvoorwaarde (het werkt alleen bij voldoende bekwaamheid aan de uitvoerende kant). Dat
Anthropic dit empirisch tegenkwam en niet uit de doctrine haalde, maakt het sterker, niet zwakker.

---

## 6. Spec-driven development: de schijnbare tegenspraak, en hoe hij oplost

§5 roept een tegenwerping op die je moet beantwoorden voordat de reeks staat. Als Anthropic 80% van
zijn instructies weggooit, waarom is de markt dan tegelijk vol van **spec-driven development**, waar
je juist méér vastlegt? Thoughtworks levert het onderscheid dat dit oplost.

### 6.1 Böckelers driedeling

Birgitta Böckeler onderscheidt drie niveaus, en dat is de bruikbaarste ordening die er ligt
*(bron: [Böckeler, "Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl", 15 oktober
2025](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html))*:

- **Spec-first** — spec vooraf, daarna weggegooid.
- **Spec-anchored** — spec blijft leven en evolueert mee met de feature.
- **Spec-as-source** — spec is het hoofdartefact; mensen bewerken alleen de spec, nooit de code.

Haar eigen formulering: *"All SDD approaches [...] are spec-first, but not all strive to be
spec-anchored or spec-as-source."*

### 6.2 De oplossing van de tegenspraak

**Anthropic bestrijdt het imperatieve deel; spec-anchored SDD legt het declaratieve deel vast.**
Regels, verboden en voorbeelden die de exploratieruimte vernauwen gaan eruit. Wat er bereikt moet
worden en waaraan je dat afmeet blijft, en wordt juist belangrijker.

Böckelers kritiek bevestigt dat langs dezelfde lijn: Kiro inzetten op een kleine bug is *"using a
sledgehammer to crack a nut"* (vier user stories, zestien acceptatiecriteria voor één bug), en
*"I'd rather review code than all these markdown files."* Haar scherpste historische parallel is dat
spec-as-source dreigt *"the downsides of both MDD and LLMs"* te combineren: *"Inflexibility and
non-determinism."* Dat is het over-engineering-kwadrant uit §7, nu in specvorm.

De Technology Radar zegt hetzelfde vanuit een andere hoek. Spec-driven development stond op
**Assess** in vol. 33, met zorgen dat workflows *"elaborate and opinionated"* zijn, dat sommige
*"lengthy spec files that are hard to review"* genereren, en met de fundamentele twijfel dat
*"handcrafting detailed rules for AI ultimately doesn't scale"*
*(bron: [Thoughtworks Radar, Spec-driven development](https://www.thoughtworks.com/en-us/radar/techniques/spec-driven-development))*.
Bij OpenSpec staat de nuance die het scherpst is: *"as models and coding agents continue to grow
more powerful"* moeten teams *"revisit native capabilities and re-evaluate the need for SDD
tooling"*
*(bron: [Thoughtworks Radar, OpenSpec](https://www.thoughtworks.com/en-us/radar/tools/openspec))*.

Thoughtworks zegt daarmee zelf dat een deel van de SDD-tooling een tijdelijke krukkenoplossing kan
zijn: hulpmiddelen die het gebrek aan modeloordeel compenseerden en overbodig worden naarmate dat
oordeel groeit. Dat is exact dezelfde beweging als Anthropic's unhobbling, van de andere kant
beschreven.

**Let op een datumkwestie:** de blip-pagina's geven tegenstrijdige informatie over welke volume
wanneer verscheen (vol. 33 = november 2025, vol. 34 = april 2026 is de waarschijnlijke lezing, met
SDD niet meegegaan naar vol. 34). Vóór publicatie verifiëren.

### 6.3 "Intent alignment" als bestaand meetbegrip

Thoughtworks heeft een eigen methode: **Structured-Prompt-Driven Development**, waarin prompts
*"first-class delivery artifacts"* zijn (versiebeheerd, gereviewd, herbruikbaar), met het
REASONS-raamwerk: Requirements, Entities, Approach, Structure, Operations, Norms, Safeguards
*(bron: [Zhang & Xia, "Structured-Prompt-Driven Development", 28 april
2026](https://martinfowler.com/articles/structured-prompt-driven/))*. Böckeler categoriseert het
als spec-anchored.

Voor de meetvraag uit §4.3 is dit de vondst: ze claimen *"a business logic implementation with
exceptionally high intent alignment (~99%)"*. Het begrip **intent alignment** bestaat dus al als
meeteenheid. De onderbouwing is één uitgewerkt facturatie-voorbeeld, dus n=1; bruikbaar als
vindplaats van het begrip, niet als bewijs van het getal.

### 6.4 De mens hoort bij de lus, niet bij de output

Kief Morris levert een formulering die direct onder het kwadrantenverhaal past: *"The right place
for us humans is to build and manage the working loop rather than either leaving the agents to it
or micromanaging what they produce."* Met het bottleneck-argument erbij: *"Agents can generate code
faster than humans can manually inspect it"*, en de observatie dat gemengde productiviteitscijfers
deels komen doordat mensen *"more time specifying and reviewing code than they save"* besteden
*(bron: [Morris, "Humans and Agents in Software Engineering Loops", 4 maart
2026](https://martinfowler.com/articles/exploring-gen-ai/humans-and-agents.html))*.

Dat is een empirisch haakje onder het Output×Lineair-kwadrant: **wie imperatief blijft
specificeren, wordt zelf de bottleneck.** Niet als moreel verwijt maar als doorstroomprobleem. Het
verbindt de kwadranten met de assurance-lus uit §4.3: de mens verschuift van het beoordelen van
output naar het inrichten en bewaken van de lus.


### 6.5 Wat dit met de rol van de engineer doet

Hier komen de declaratieve wending (§5), de spec-discussie (§6) en de assurance-lus (§4.3) samen op
één plek: het werk van de engineer zelf. Dit is waarschijnlijk het meest concrete en het meest
ongemakkelijke deel van het hele onderwerp.

**De implementatie is niet langer de hoofdzaak.** Als een agent code schrijft die veilig is en de
intentie vervult, maar anders is opgebouwd dan de engineer had bedacht, dan is die code goed. Het
oordeel verschuift van *"is dit hoe ik het zou schrijven"* naar *"doet dit wat we bedoelden, en is
het veilig"*. Dat is een aanzienlijke identiteitsverandering, want vakmanschap zat voor veel
engineers precies in dat *hoe*.

Twee dingen blijven wél hard, en die moeten scherp benoemd worden zodat dit geen pleidooi voor
laksheid wordt:

- **Veiligheid en correctheid** zijn geen smaak. Die blijven onverkort de verantwoordelijkheid van
  de engineer.
- **Leesbaarheid en onderhoudbaarheid** blijven tellen, maar als eigenschap van het systeem, niet
  als overeenstemming met de voorkeur van één auteur. Anthropic formuleert dat zelf al als
  richtlijn: "write code matching its comment density, naming, and idiom" (§5), dus aansluiten bij
  de omgeving in plaats van bij een persoonlijke stijl.

**De consequentie is dat toetsing zwaarder wordt, niet lichter.** Als je het *hoe* loslaat, is de
enige overgebleven greep de vraag of de intentie bereikt is. Dat verplaatst het zwaartepunt van
code-review naar intentie-verificatie, en het maakt Kief Morris' bottleneck-argument acuut: agents
genereren sneller dan mensen kunnen inspecteren (§6.4), dus regel-voor-regel lezen schaalt niet.
Wat wél schaalt is een expliciete formulering van de bedoeling waar je tegenaan kunt toetsen.

**Tests als uitvoerbare intentie, met één principe erboven.** Hier lost ook de schijnbare tegenspraak
van de hele reeks op: we bepleiten minder voorschrijven én zwaardere toetsing. Een criticus wijst er
terecht op dat een test óók een specificatie van gewenst gedrag is, dus prescriptief.

Het antwoord is het onderscheid dat de hele reeks draagt, nu toegepast op verificatie: **leg het
*wat* vast en laat het *hoe* vrij.** Een test die zegt "gegeven X moet het resultaat Y zijn"
schrijft een uitkomst voor en laat elke implementatie toe. Een test die mockt op interne structuur of
assert op de volgorde van aanroepen schrijft de implementatie voor. De eerste is declaratief, de
tweede is imperatief vermomd als verificatie. Zwaardere toetsing en minder voorschrijven zijn dus
alleen tegenstrijdig als je die twee soorten tests op één hoop gooit.

Met dat principe op zijn plek wordt de testsuite geen kwaliteitsnet achteraf maar de **primaire
drager van de intentie**:

- Specification by Example en BDD deden dit al lang: het voorbeeld is de intentie, de test is de
  vastlegging ervan. Wat verandert is de reden. Vroeger was dat om misverstanden tussen mensen te
  voorkomen; nu is het de vorm waarin je een agent aanstuurt en verifieert.
- Anthropic's aanbeveling om naar **rijke referenties** te verwijzen (testsuites, rubrics) in plaats
  van naar beschrijvingen wijst dezelfde kant op: hogere fidelity, minder ruimte voor
  interpretatiedrift.
- **Rubrics** vullen aan waar tests niet komen: kwaliteitsoordelen die je niet in een assert vangt.
  Dat is de toetsbare vorm van een deel van de tacit laag.

**De nieuwe kernvaardigheid is dus: een intentie zo formuleren dat hij toetsbaar is.** Dat is een
andere vaardigheid dan code schrijven, en het ligt dichter bij het werk van een requirements
engineer of een domeinmodelleur. Het verbindt dit deel rechtstreeks met §4 (elicitatie) en met de
kwadranten (§7): dit is precies wat een Feature Factory-engineer nooit heeft hoeven leren, en wat
een Strategische Orchestrator al doet.

**Eerlijke tegenwerping.** Niet alles is in tests te vangen, en een testsuite die alles probeert
vast te leggen wordt zelf de over-specificatie waar §6 tegen waarschuwt. Ook een declaratieve test
kan over-specificeren: honderd assertions op randgevallen die niemand heeft doordacht leggen een
intentie vast die nooit is geformuleerd. Het principe *wat vastleggen, hoe vrijlaten* begrenst de
vorm, niet de hoeveelheid.

---


## 7. De organisatorische voorwaarde: waarom dit niet voor iedereen werkt

Dit is jouw punt over de kwadranten, en het is de scherpste these van het hele onderzoek.

### 7.1 De matrix

Op augmentedorganisation.nl (zone Managementstijl) staat een 2×2 met de assen **Output ↔ Outcome**
(verticaal) en **Lineair ↔ Systeem** (horizontaal):

| | Lineair | Systeem |
|---|---|---|
| **Outcome** | Korte-termijn Optimizer | **Strategische Orchestrator** ★ |
| **Output** | Feature Factory | Over-Engineered Architect |

De begeleidende tekst bij de zone: *"Niet de feature of de technische architectuur staat centraal,
maar de vraag: welke gedragsverandering willen we realiseren, en hoe hangen onze keuzes samen in
een groter systeem?"* Bij de doelpositie staat expliciet dat AI daar fungeert als **co-denker**:
"niet alleen code-generator, maar partner in systeemontwerp en impactanalyse".

### 7.2 De these die hieruit volgt

**Declaratieve intentie is alleen bruikbaar voor wie in outcomes en systemen denkt.** Dat is geen
karakterkwestie maar een structurele:

- De **Feature Factory** (output × lineair) kan een declaratieve intentie niet verwerken, want zijn
  hele werkeenheid is het ticket. intentdriven.nl formuleert dat scherp: "Jouw wereld is het ticket.
  Code komt binnen, code gaat eruit." Geef zo iemand een intentie in plaats van een specificatie en
  hij vraagt om verduidelijking tot het weer een specificatie is. Het signaal dat de site noemt is
  meetbaar: "Engineers kunnen de bedrijfsproblemen die hun systeem oplost niet beschrijven."
- De **Over-Engineered Architect** (output × systeem) verwerkt de intentie wél, maar te ruim: hij
  bouwt voor tien eisen die niemand gesteld heeft. Systeemdenken zonder outcome-toets leidt tot
  speculatieve invulling van de open ruimte die de intentie laat.
- De **Korte-termijn Optimizer** (outcome × lineair) is outcome-gedreven maar mist de
  neveneffecten. Hij bereikt de intentie lokaal en breekt hem elders.
- Alleen de **Strategische Orchestrator** (outcome × systeem) kan de open ruimte tussen intentie en
  implementatie verantwoord invullen.

**En hier zit de aansluiting op §5 die het geheel interessant maakt.** Anthropic verwijderde de
harde regels omdat het model genoeg oordeelsvermogen kreeg. Dezelfde redenering geldt voor mensen:
je kunt pas declaratief aansturen wat genoeg oordeelsvermogen heeft om de open ruimte goed in te
vullen. **De verschuiving van imperatief naar declaratief is dus dezelfde beweging, of de
uitvoerder nu een agent of een engineer is, en hij stelt aan beide dezelfde eis.** Dat is een
sterke, verdedigbare stelling voor de reeks.

Met de bijbehorende ongemakkelijke consequentie: organisaties die hun engineers als feature factory
hebben ingericht, kunnen hun **agents** ook niet declaratief aansturen. Ze zullen agents
overconstrainen op precies de manier die Anthropic bij zichzelf als antipatroon herkende. De
volwassenheid van je aansturing van mensen voorspelt de volwassenheid van je aansturing van agents.

### 7.3 Naamgeving: één inconsistentie om op te lossen

Dezelfde matrix heeft op je twee sites verschillende namen. Voordat hier een reeks op gebouwd wordt,
is het verstandig dit gelijk te trekken:

| augmentedorganisation.nl | intentdriven.nl |
|---|---|
| Strategische Orchestrator | Strategische Meedenker |
| Over-Engineered Architect | Over-engineer |
| Korte-termijn Optimizer | Short-term Optimizer |
| Feature Factory | Feature Factory |

De assen en de kwadrantindeling zijn wél identiek, dus het is puur naamgeving.

---

## 8. Waar Eric Evans en DDD in passen

DDD levert het **mechanisme** waarmee intentie overdraagbaar wordt, en dat is een preciezere rol
dan "DDD is ook belangrijk".

- **Ubiquitous language** is het instrument dat voorkomt dat intentie bij elke overdracht vervormt.
  intentdriven.nl: "Als je jezelf betrapt op het vertalen tussen hun woorden en jouw code, ben je nog
  niet volledig in het domein binnengedrongen."
- **Bounded context** is de grens waarbinnen een intentie eenduidig is. Dat is al uitgewerkt in
  [Context Matters](https://edwinvandillen.nl/?p=441), inclusief de vondst dat Farley in *Modern
  Software Engineering* (2021) zelf de brug naar Evans legt. De formulering daar is direct
  herbruikbaar: de feature-denker ordent rond de deliverable, de context-denker rond het domein; de
  eerste vraagt "wat ga ik bouwen", de tweede "wat moet ik begrijpen".
- **Domeinmodel als strenge selectie.** intentdriven.nl: modelleren is "een daad van resolutie",
  je kiest waarop je focust en wat je negeert. Dat is precies wat een intentie ook doet.

Er is bovendien een aanhaking die de reeks een fundament geeft dat dieper ligt dan DDD: **Naur,
"Programming as Theory Building" (1985)**, die op intentdriven.nl al expliciet wordt aangehaald.
De stelling daar is dat de software effectief dood is zodra de theorie verloren gaat, ook als hij
nog draait. Vertaald naar dit onderwerp: **intentie is de theorie, code is het bijproduct.** De
kernquote van intentdriven.nl zegt dat al letterlijk: "Working software is a by-product of shared
theory."

Dat is waarschijnlijk het sterkste filosofische anker dat er ligt, en het is nog nauwelijks
uitgewerkt op de blog.

---

## 8b. Wiens intentie? Theorie voor arbitrage bij conflict

Dit was de grootste lacune in de opzet, aangewezen door de Grok-review: de reeks behandelde
intentie als iets van één partij. Deze leesronde vult hem. Er blijken **vier tradities** te
zijn die het probleem elk op een ander niveau aanpakken, en samen dekken ze deel 9.

### 8b.1 Het conflict benoemen: divergentie (van Lamsweerde)

Van Lamsweerde behandelde dit al in 1998, in hetzelfde KAOS-kader waar §2.1 de
intentiedefinitie vandaan haalt. Zijn bijdrage die het meest bruikbaar is, is een
**onderscheid in scherpte**: naast regelrecht conflict introduceert hij **divergentie**,
"a frequent, weaker form of conflict" waarbij doelen niet logisch onverenigbaar zijn maar
onder bepaalde omstandigheden niet samen gehaald kunnen worden
*(bron: [van Lamsweerde, Darimont & Letier, "Managing Conflicts in Goal-Driven Requirements
Engineering", IEEE TSE 1998](https://www.semanticscholar.org/paper/Managing-Conflicts-in-Goal-Driven-Requirements-Lamsweerde-Darimont/c2ffaa1f203bfeab1618230f77d22beedf9716c2))*.

Dat onderscheid telt voor de reeks, want de meeste praktijkgevallen zijn divergenties en
geen conflicten. Twee stakeholders willen zelden het tegenovergestelde; ze willen dingen die
in de meeste gevallen samengaan en in het randgeval botsen. Wie dat als conflict behandelt,
escaleert te vroeg. Zijn resolutiestrategieën lopen bovendien niet via onderhandeling maar
via **hermodellering**: een nieuw, hoger doel introduceren of de doelspecificaties zo
herschrijven dat de botsing verdwijnt.

**Waarom dit eerst komt in deel 9:** het is de enige traditie die zegt dat je een deel van
je conflicten kunt *wegontwerpen* in plaats van beslechten.

### 8b.2 Het conflict onderhandelen: Theory W en WinWin (Boehm)

Boehm en Ross formuleerden in 1989 Theory W: een onderneming slaagt wanneer al haar
**success-critical stakeholders** winnaars zijn. Het bijbehorende WinWin-proces laat elke
partij haar **win conditions** formuleren; waar die botsen wordt dat vastgelegd als een
**issue**, waarna **options** worden verkend die uitmonden in **agreements**. Het
WinWin-spiralmodel zet die onderhandeling aan het begin van elke cyclus
*(bron: [Boehm et al., "Using the WinWin Spiral Model: A Case Study", IEEE Computer, juli
1998](https://www.nyu.edu/classes/jcf/g22.2440-001_sp09/handouts/UsingTheSpiralModel.pdf))*.

De formulering die het scherpst is voor de reeks: **win-lose-situaties tussen stakeholders
ontwikkelen zich doorgaans tot lose-lose.** Dat is een empirische claim over
softwareprojecten, geen morele.

Let op de aanhaking op §1.4: WinWin plaatst de onderhandeling aan het *begin* van elke
cyclus, dus het is een lus-3-mechanisme dat periodiek draait, niet een eenmalige
projectstart.

### 8b.3 Het conflict structureren: Context Mapping (Evans)

Dit is de vondst die deel 9 samenhangend maakt, want het verbindt de semantische en de
politieke grens die het deel wil samennemen. Context Mapping is bij Evans expliciet "the
strategic practice of understanding and **governing the relationships** among the different
bounded contexts". De patronen coderen machtsverhoudingen tussen de teams die die contexten
bezitten *(bron: [ddd-crew, Context Mapping](https://github.com/ddd-crew/context-mapping);
[Open Group, DDD Strategic Patterns](https://pubs.opengroup.org/architecture/o-aa-standard/DDD-strategic-patterns.html))*:

- **Partnership** — twee modellen evolueren samen; wederzijdse afhankelijkheid, gezamenlijke
  besluitvorming.
- **Customer/Supplier** — gestructureerde co-afhankelijkheid waarin de ene kant de andere
  meer nodig heeft; de prioriteiten van de afnemer tellen mee in de planning van de
  leverancier. Arbitrage is hier ingebouwd in de relatie.
- **Conformist** — de afnemer past zich aan het model van de leverancier aan, met minimale
  aanpassing; flexibiliteit wordt ingeruild voor snelheid. Dit is een *bewuste capitulatie*.
- **Separate Ways** — de contexten worden niet geïntegreerd. Ook dat is een geldige uitkomst
  van een intentieconflict, en de goedkoopste.
- **Anticorruption Layer** — integreren zonder het eigen model te laten vervuilen door dat
  van de ander.

**Waarom dit sterk is voor Edwins reeks:** het antwoord op "wiens intentie wint" is bij Evans
geen bestuurlijke maar een **architectuurbeslissing**, en die is zichtbaar in de code. Een
Conformist-relatie betekent dat één team zijn intentie structureel ondergeschikt maakt, en
dat zie je terug in elke integratie. Dat sluit rechtstreeks aan op Naur (§8): de theorie,
inclusief de machtsverhouding, zit in het artefact.

### 8b.4 Het conflict beslechten: beslisrechten (RAPID, DACI)

Als hermodelleren niet lukt en onderhandelen niet convergeert, moet iemand beslissen. Daar
bestaan expliciete kaders voor. RAPID (Bain, jaren 2000) verdeelt vijf rollen: **Recommend**,
**Agree** (met vetorecht), **Perform**, **Input** en **Decide**, met als kernregel dat er
precies **één** Decider is. DACI is de eenvoudiger variant: Driver, Approver (exact één),
Contributors, Informed
*(bron: [Bain RAPID-raamwerk](https://umbrex.com/resources/frameworks/strategy-frameworks/rapid-decision-rights-framework/);
[vergelijking RACI/DACI/RAPID](https://dectrack.com/en/blog/decision-models-raci-daci-rapid))*.

Voor de reeks is één element hiervan direct bruikbaar en de rest overbodig detail: het
onderscheid tussen **input hebben** en **beslissen**. Veel intentieconflicten in de praktijk
zijn geen conflicten over de inhoud maar over de vraag wie mag beslissen, en dat blijft
onbesproken. RAPID's "Agree"-rol (veto zonder beslisrecht) is bovendien precies de positie
waarin een securityteam of een architect vaak zit.

**Koppeling terug naar lus 3 (§1.4):** de vraag "was dit de juiste bedoeling" heeft een
eigenaar nodig, en de scheidingscriteria uit §1.4 zeiden al dat lus 3 hoort bij *wie de
intentie mag wijzigen*. Dat is precies de Decide-rol. Zonder benoemde Decider is lus 3
niet te sluiten, wat de theoretische onderbouwing is van de bewering in deel 9.

### 8b.5 Hoe de vier zich verhouden

Ze zijn geen alternatieven maar een **escalatietrap**, en dat is de structuur die deel 9 kan
dragen:

| Stap | Vraag | Traditie | Uitkomst |
|---|---|---|---|
| 1 | Is het echt onverenigbaar, of alleen in een randgeval? | van Lamsweerde: divergentie | vaak wegontworpen |
| 2 | Kunnen beide partijen winnen? | Boehm: WinWin | agreement |
| 3 | Wat is de structurele verhouding? | Evans: Context Mapping | een patroon, zichtbaar in de architectuur |
| 4 | Wie hakt de knoop door? | RAPID/DACI | één benoemde beslisser |

De volgorde is de boodschap: **wie bij stap 4 begint, heeft de eerste drie overgeslagen.** In
de praktijk gebeurt precies dat, en dat is de scherpe stelling die deel 9 nog miste.

### 8b.6 Wat hier nog ontbreekt

Eerlijk benoemen: alle vier de tradities gaan over conflicten tussen **mensen**. De reeks
gaat ook over agents, en de vraag wat er gebeurt bij onverenigbare intenties tussen
*geautomatiseerde* partijen is met deze bronnen niet beantwoord. Deel 6 van de vorige reeks
raakte dit al aan met conflictresolutie over de contextgrens. Kandidaat voor een extra alinea
in deel 9, niet voor een eigen deel; het is speculatiever dan de rest.

---


## 8c. De C-laag: beter worden in expliciteren

Dit lost de zwaarste spanning in de opzet op. Deel 3 stelt dat volledige explicitering niet
bestaat; de rest van de reeks reikt een instrument aan om intentie te toetsen. Onverzoend
leest dat als "dit is onmogelijk, en hier is gereedschap". De verzoening zit in een laag die
in het lussenmodel nog ontbrak.

### 8c.1 De grens is niet vast, hij beweegt

Toyota Kata levert de formulering die deel 3 nodig heeft: de **threshold of knowledge**, de
grens tussen wat je werkelijk weet en wat je speculeert. Rothers methode zet de *target
condition* bewust **net voorbij** die grens, juist omdat het pad ernaartoe niet te
voorspellen is; experimenten schuiven de grens vervolgens incrementeel op
*(bron: [Rother, The Improvement Kata Handbook](https://public.websites.umich.edu/~jmondisa/TK/Handbook/About_the_IK.pdf))*.

Daarmee verandert de uitspraak van deel 3 van een muur in een bewegende grens:

> Er is altijd een grens aan wat je van je intentie kunt uitspreken. Die grens ligt niet vast.
> Het werk bestaat eruit hem te verleggen, en de enige manier om te weten waar hij ligt is er
> overheen stappen en zien wat er misgaat.

Zelfde inhoud, maar een startpunt in plaats van een capitulatie. En het maakt de lus geen
compensatie voor onvolledigheid maar **het antwoord erop**.

### 8c.2 Engelbart: het kader onder "de machine die de machine bouwt"

Musk formuleerde in 2016: *"what really matters is the machine that builds the machine — the
factory. And that is at least two orders of magnitude harder than the vehicle itself"*, in
2020 aangescherpt tot *"1000% to 10,000% harder than making a few prototypes"*
*(bron: [Fortune, september 2016](https://fortune.com/2016/09/16/elon-musk-epiphany);
[Musk op X, september 2020](https://x.com/elonmusk/status/1308284091142266881))*.

Het onderliggende kader is ouder en preciezer. Douglas Engelbart onderscheidde drie niveaus:

- **A-activiteit** — het werk doen.
- **B-activiteit** — verbeteren hoe je dat werk doet.
- **C-activiteit** — verbeteren hoe je verbetert.

Zijn claim: *"establishing an ongoing C Activity offers the highest leverage of any activity
an organization can pursue."* Zijn essay uit 2003 heet letterlijk *Improving Our Ability to
Improve* *(bron: [Engelbart, "Improving Our Ability to Improve",
2003](https://worrydream.com/refs/Engelbart_2003_-_Improving_Our_Ability_to_Improve.pdf);
[Collective IQ Review over het A/B/C-model](https://collectiveiq.wordpress.com/2017/11/01/what-is-the-bootstrapping-methodology/))*.

Dat plaatst Musk scherper dan hij zichzelf plaatst: de fabriek als product is **B**. Engelbart
zegt dat de hefboom een niveau hoger ligt, bij het steeds beter worden in het bouwen van
fabrieken.

### 8c.3 De Model 3 als correctie op de eerste lezing

Een eerdere versie van deze redenering stelde dat de fabrieksmetafoor hier maar half opgaat,
"want Musk wist wat een Model 3 is, en bij intentie is de specificatie zelf wat je ontdekt".
**Dat is onjuist, en de correctie maakt de metafoor juist sterker.**

Musk wist wat hij wilde *bereiken*: een software-defined car, in massa geproduceerd, met hoge
kwaliteit. Wat dat concreet betekende was niet bekend, en de kernvraag (hoe bereik je massa
én kwaliteit tegelijk) was onopgelost. Hij had een intentie, geen specificatie.

Wat er in de praktijk gebeurde is bruikbaar als illustratie van precies dit hoofdstuk:

1. De eerste Model 3's werden gebouwd om **massa** te halen.
2. Massa leverde niet vanzelf kwaliteit; die twee doelen bleken in de praktijk te botsen. In
   de termen van §8b.1 is dat een **divergentie**: geen logisch onverenigbare doelen, maar
   doelen die onder reële omstandigheden niet samengaan.
3. De oplossing kwam niet uit herspecificeren maar uit het terugleggen van elke
   kwaliteitsbevinding **in de productie**, niet alleen in het product. Kleine verbeteringen,
   telkens opnieuw.
4. Omdat elke verbetering op de volgende voortbouwt, stapelt dat niet lineair maar
   samengesteld.

Dat is B- en C-activiteit in bedrijf, en het is een concreet geval waarin de
expliciteringsgrens productief werd gemaakt in plaats van als belemmering behandeld.

**Waar de metafoor dan wél zijn grens heeft.** Een fabriek reproduceert; het apparaat dat je
voor intentie bouwt moet de vraag scherper stellen. Toyota Kata is daarom een preciezere
metafoor dan Gigafactory, omdat Kata expliciet gaat over navigeren wanneer het pad onbekend
is. Wie de fabrieksmetafoor te ver doortrekt belandt bij spec-as-source uit §6.1, het idee dat
je de specificatie zo goed kunt maken dat de uitvoering vanzelf volgt.

### 8c.4 De C-laag in het lussenmodel

De drie lussen uit §1.4 blijken op Engelbarts A en B te zitten. De C ontbreekt:

| Lus | Vraag | Engelbart |
|---|---|---|
| 1. Bouwlus | Hebben we het goed gebouwd? | A |
| 2. Uitkomstlus | Heeft het opgeleverd wat we bedoelden? | B |
| 3. Intentielus | Was dat de juiste bedoeling? | B, aan de rand van C |
| **4. Methodelus** | **Worden we beter in het vinden van intentie?** | **C** |

Alle drie de bestaande lussen gaan over *deze* intentie, dit product, dit project. De C-vraag
is een andere: welke soorten intentie blijven in onze organisatie structureel impliciet, en
welke techniek werkt in ons domein?

Elke toetsing levert daarmee twee dingen op. Een antwoord op de vraag of je de bedoeling
haalde, en een observatie over waar jouw expliciteringsapparaat tekortschoot. Het eerste
verwerk je in het product; het tweede in je manier van werken. Vrijwel niemand doet het
tweede.

**Op welke frequentie draait de methodelus?** Dit is een reële valkuil, aangewezen bij de tweede
Grok-review: lus 3 heet zeldzaam en mensenwerk, dus hoe kun je er systematisch beter in worden? Een
C-laag heeft feedback nodig, en lus 3 levert per ontwerp weinig gebeurtenissen.

Het antwoord is dat **de methodelus zich niet op lus 3 voedt maar op lus 2**. De observatie "hier
schoot onze explicitering tekort" komt vrij bij elke uitkomstmeting, dus per release, en niet pas
wanneer iemand de bedoeling zelf ter discussie stelt. Lus 3 blijft daarmee zeldzaam; de methodelus
draait mee met de uitkomstlus en heeft genoeg waarnemingen om iets van te leren.

Dat maakt het model bovendien consistent met §1.4: de scheidingscriteria zeiden al dat lus 2 per
release draait en geautomatiseerd hoort te zijn. De C-laag erft die frequentie.

### 8c.5 De consequentie voor AI-investeringen

Als Engelbart gelijk heeft dat C de grootste hefboom is, volgt hieruit een ongemakkelijke
observatie: de meeste organisaties zetten AI in op **A** (sneller bouwen), een enkele op **B**
(beter achterhalen wat er gebouwd moet worden), en vrijwel niemand op **C**.

Dat is een verklaring voor de teleurstellende productiviteitscijfers die ook Kief Morris
noemt (§6.4): men versnelt de A-laag van een systeem waarvan de B- en C-laag ontbreken.

### 8c.6 De Chinese auto-industrie: het mechanisme klopt, het scorebord beweegt

Edwin bracht in dat de Chinese benadering deze denkwijze fundamenteel heeft omarmd. Dat is
verifieerbaar op het punt dat telt, met één kanttekening.

**Het mechanisme is goed onderbouwd.** Duitse fabrikanten hebben gemiddeld 48 tot 54 maanden
nodig van eerste schets tot start van productie; Chinese concurrenten doen dat in 24 tot 30
maanden, en BYD haalt in gevallen 18 maanden. Volkswagen bracht de ID Polo en ID Cross terug
naar 36 maanden, een forse verbetering maar nog geen gelijke tred. Een deel van de verklaring
is verticale integratie: BYD maakt tot circa 75% van zijn componenten zelf (batterijen, chips,
motoren, software), waar Duitse fabrikanten van externe leveranciers afhangen, wat elke
wijziging trager maakt.

**De kanttekening.** De sprong van "sneller itereren" naar "dus groeien ze harder" is op dit
moment niet houdbaar als marktclaim. BYD nam in 2024 de eerste plaats van Volkswagen over in
China en hield die in 2025, maar zakte in de eerste twee maanden van 2026 naar de vierde
plaats met 7,1% marktaandeel, terwijl de joint ventures van Volkswagen terugkeerden naar de
eerste plek.

**Advies voor de reeks:** gebruik de **cyclustijd** als illustratie en laat het marktaandeel
weg. Het punt is het vermogen om snel te itereren en te leren, niet de stand op het scorebord;
die beweegt en zou de post binnen een kwartaal kunnen achterhalen.

**Doseren.** Edwin gaf expliciet aan dit niet te overbelichten. Het hoort thuis als één
alinea-illustratie bij het C-deel, niet als eigen sectie, en zeker niet als geopolitieke
these bovenop die van deel 1.

---


## 9. De reeks: twaalf delen

Werktitel: **"Intentie-gedreven engineering"**. Elf delen, waarvan tien inhoudelijk en één recap.
Deze opzet is herzien na de Grok-review van 2026-08-08; de weging staat in
`grok-review-intentie-ontwerp.md`.

**Het vertrekpunt is de waardevraag, niet de AI-ontwikkeling.** Begin je bij AI, dan is de reeks over
drie modelreleases verouderd. Begin je bij waarde, dan blijft hij staan.

### De ruggengraat

Het lussenkader uit §1.4, uitgebreid met de C-laag uit §8c.4 en expliciet gepresenteerd als
**integratiekader**, niet als nieuw model:

1. **Bouwlus** — hebben we het goed gebouwd? (Engelbart: A)
2. **Uitkomstlus** — heeft het opgeleverd wat we bedoelden? (B)
3. **Intentielus** — was dat wel de juiste bedoeling? (B, aan de rand van C)
4. **Methodelus** — worden we beter in het vinden van intentie? (C)

De eerste drie gaan over dít project; de vierde over de methode. Deel 10 voert hem in, en het is
de lus die de grens uit deel 3 productief maakt in plaats van beperkend.

### De delen

**1 — Waarom intentie het enige is dat waarde draagt**
*Stelling:* AI heeft intentie niet belangrijk gemaakt; het heeft de laatste smoes weggenomen om er
niet mee te beginnen.
Ries' vanity metrics tegenover validated learning; Argyris als theorie onder "we doen het zo omdat we
het altijd zo deden"; de Double Diamond met de zelfkritiek dat probleemdefinitie de overgeslagen fase
is. De vier tradities als **vier oplossingen voor één delegatieprobleem** (§1.1), niet als
convergentie. En het antwoord op "waarom nu wél": niet omdat andere continenten slimmer zijn, maar
omdat de **vertaallaag** van bedoeling naar toetsbare uitvoering voor het eerst betaalbaar is (§1.3).
Eindigt in het drie-lussen-kader plus een korte introductie van de kwadranten, zodat de lezer zich
vroeg kan plaatsen.
*Waarom niet vanzelfsprekend:* het argument is vijftig jaar oud; wat veranderd is, is de
uitvoerbaarheid, niet het inzicht.

**2 — Wat intentie is, en waarom "begin bij het waarom" onvolledig is**
*Stelling:* het waarom ligt er meestal niet, dus ermee beginnen slaat een stap over.
Laagindeling motief → intentie → outcome → specificatie → implementatie; de GORE-definitie;
commander's intent. Naast Sinek in plaats van erachter.

**3 — Waarom intentie zich verstopt, en waarom die grens beweegt**
*Stelling:* er is altijd een grens aan wat je van je intentie kunt uitspreken, en die grens ligt
niet vast; het werk bestaat eruit hem te verleggen.
Polanyi; de drietrap expliciet/impliciet/tacit; de SECI-kritiek dat tacit kennis deels inherent
tacit is. Maar niet als muur: met Toyota Kata's **threshold of knowledge** als kernbegrip, de grens
tussen wat je weet en wat je speculeert, die je alleen leert kennen door eroverheen te stappen.
Dit deel maakt de rest geloofwaardig én bruikbaar: juist omdat explicitering onvolledig blijft, is
de lus geen luxe maar de enige correctie die je hebt.
*Eindigt diagnostisch, niet in een inzicht:* hoe stelt de lezer vast waar zijn **eigen** grens
ligt? Dat is de brug naar de rest van de reeks.
*Waarom niet vanzelfsprekend:* de markt belooft volledige explicitering; de vakliteratuur zegt
driemaal onafhankelijk dat die niet bestaat. Het antwoord is niet opgeven maar de grens verleggen.

**4 — Elicitatie: de techniek kiezen bij de kennissoort**
*Stelling:* de gangbare fout is interviewtechniek inzetten op tacit kennis.
De tabel uit §4.1, en per kennissoort meteen de AI-rol die erbij hoort: de interviewer (socratisch
doorvragen) voor impliciete kennis, de spiegel (prototype) en de observator (ambient meelezen, Claude
Tag) voor tacit kennis. De surveillance-afweging staat waar hij hoort, namelijk bij de techniek die
hem oproept.
*Waarom niet vanzelfsprekend:* technieken worden meestal geordend naar populariteit of fase, niet
naar het soort kennis waarop ze werken. En observatie is de techniek die de literatuur al
voorschreef maar die niet schaalde.

**5 — Van intentie naar vorm: declaratief vastleggen zonder dicht te timmeren**
*Stelling:* het imperatieve deel van een specificatie kan weg, het declaratieve deel wordt juist
belangrijker.
Anthropic's unhobbling; Böckelers spec-first / spec-anchored / spec-as-source als het onderscheid dat
de tegenspraak met spec-driven development oplost; "voorbeelden → interface-ontwerp".

**6 — De rol van de engineer verandert: van hoe naar of**
*Stelling:* leg het *wat* vast en laat het *hoe* vrij. Dat principe geldt ook voor je tests.
Als de code veilig is en de intentie vervult, is het goed dat een agent hem anders opbouwde.
Veiligheid en correctheid blijven hard. Toetsing wordt zwaarder in plaats van lichter. Hier wordt ook
de schijnbare tegenspraak van de hele reeks opgelost: minder voorschrijven én zwaarder toetsen kan,
mits je declaratieve tests (uitkomst) onderscheidt van imperatieve (implementatie vastgepind).
*Waarom niet vanzelfsprekend:* dit raakt de beroepsidentiteit, want vakmanschap zat voor veel
engineers juist in het *hoe*.

**7 — Lus 2: heb je bereikt wat je bedoelde?**
*Stelling:* organisaties doen translation en activation en slaan assurance over; daarom blijft
output-sturing bestaan, want dat is de enige lus die sluit.
De vier fasen uit Intent-Based Networking; intent drift; intent alignment; rubrics. Met de
Cynefin-begrenzing op meten in Complex terrein. **En expliciet: hoe houd je lus 2 gescheiden van lus
3** (wat staat ter discussie, welk ritme, wie draait hem) — zonder die scheiding is het onderscheid
retorisch.

**8 — Lus 3: was het de juiste bedoeling?**
*Stelling:* innovatie ontstaat niet door beter vooraf na te denken, maar door het gebouwde terug te
lezen als uitspraak over je eigen intentie.
Argyris; build-measure-learn; Naur's theoriebouw. Met de volgorde-eis: lus 3 zonder lus 2 is aannames
bevragen op basis van niets.

**9 — Wiens intentie, en waar houdt hij op**
*Stelling:* wie begint met de vraag "wie beslist", heeft drie stappen overgeslagen.
De **semantische grens** eerst: een intentie is alleen eenduidig binnen één bounded context, met
Evans en Farley (?p=441) en ubiquitous language. Daarna de **politieke grens**, als escalatietrap
(§8b.5):
1. *Is het echt onverenigbaar, of alleen in een randgeval?* Van Lamsweerdes **divergentie** (1998):
   de meeste botsingen zijn geen conflicten maar doelen die in het randgeval niet samengaan, en een
   deel daarvan is weg te ontwerpen door een hoger doel te introduceren.
2. *Kunnen beide partijen winnen?* Boehms **Theory W**: een project slaagt als alle
   success-critical stakeholders winnen, met win conditions, issues, options en agreements. Zijn
   empirische claim: win-lose ontwikkelt zich doorgaans tot lose-lose.
3. *Wat is de structurele verhouding?* Evans' **Context Mapping**: Partnership, Customer/Supplier,
   Conformist, Separate Ways, Anticorruption Layer. Het antwoord op "wiens intentie wint" is hier
   geen bestuurlijke maar een architectuurbeslissing, en die is zichtbaar in de code. Dit is de
   scharnier die de semantische en de politieke grens verbindt.
4. *Wie hakt de knoop door?* Beslisrechten (RAPID/DACI), waarvan alleen het onderscheid tussen
   **input hebben** en **beslissen** de post in hoeft. Zonder benoemde beslisser is lus 3 niet te
   sluiten, want dan mag niemand vaststellen dat de bedoeling verkeerd was.
*Waarom niet vanzelfsprekend:* het vakgebied behandelt intentie als iets van één partij, en in de
praktijk begint de discussie meteen bij stap 4.
*Eerlijke grens:* alle vier de tradities gaan over conflicten tussen mensen. Wat er gebeurt bij
onverenigbare intenties tussen agents is hiermee niet beantwoord; één alinea, geen belofte.

**10 — De machine die de machine bouwt: beter worden in expliciteren**
*Stelling:* de meeste organisaties zetten AI in om sneller te bouwen, een enkele om beter te
achterhalen wát te bouwen, en vrijwel niemand om beter te worden in dat achterhalen zelf.
Engelbarts A/B/C-model (werk doen, het werk verbeteren, het verbeteren verbeteren), met zijn claim
dat een doorlopende C-activiteit de grootste hefboom is die een organisatie heeft. Musk's "machine
die de machine bouwt" als herkenbare maar onvolledige illustratie: hij had een intentie
(software-defined car, massa én kwaliteit), geen specificatie, en de oplossing kwam uit het
terugleggen van elke kwaliteitsbevinding in de *productie* in plaats van alleen in het product.
Eén alinea over cyclustijd in de auto-industrie als illustratie van itereervermogen; het
marktaandeel blijft eruit, dat beweegt te snel. Voegt de vierde lus toe: **worden we beter in het
vinden van intentie?** Met de frequentie erbij, want daar zit een valkuil: **de methodelus voedt
zich op lus 2, niet op lus 3.** Elke uitkomstmeting levert twee dingen op, of de bedoeling gehaald
is én waar het expliciteringsapparaat tekortschoot. Dat tweede is per release waarneembaar, terwijl
lus 3 zeldzaam en mensenwerk blijft. Zonder die precisering lijkt het alsof je systematisch beter
wordt in iets wat je nauwelijks doet.
*Waarom niet vanzelfsprekend:* de eerste drie lussen gaan alle drie over dít project. Deze gaat
over de methode, en dat is de enige investering met samengesteld rendement.
*Grens van de metafoor:* een fabriek reproduceert, dit apparaat moet de vraag scherper stellen.
Wie de metafoor te ver doortrekt belandt bij spec-as-source uit deel 5.

**11 — Wie hiermee kan werken, en waarom dat geen karakterkwestie is**
*Stelling:* je kunt agents niet volwassener aansturen dan je mensen.
De kwadranten, nu te lezen als: welke lussen heeft dit kwadrant. Kief Morris' bottleneck-argument.
Cynefin-Disorder als verklaring: wie in Clear-terrein thuis is categoriseert een ambigue intentie naar
tickets, de juiste reflex in het verkeerde domein. Dat maakt van een oordeel over mensen een diagnose
van een situatie.

**12 — Recap**
De rode draad expliciet, met de terugkoppelingen die pas zichtbaar worden als je de elf voorgaande
delen achter elkaar leest. Bruggen naar Vibe · Spec · Harness en naar de anatomie-reeks.

### Volgorde

*Advies:* bovenstaande volgorde. De kwadranten worden in deel 1 kort geïntroduceerd zodat de lezer
zich vroeg kan plaatsen, en pas in deel 11 volledig behandeld, omdat ze daar gelezen worden als
"welke lussen heeft dit kwadrant" en dat de lussen veronderstelt.

**Compressie naar tien** als delen dun uitvallen: voeg 2 en 3 samen (wat intentie is en waarom hij
zich verstopt), en 5 en 6 (vorm en de rol van de engineer). De delen 1, 7, 8, 9, 10 en 11 zijn
dragend; deel 10 lost bovendien de spanning met deel 3 op en kan daarom niet vervallen.

### Wat de reeks bewust niet doet

- **Geen tooling-vergelijking.** Kiro, spec-kit, Tessl en OpenSpec alleen als illustratie in deel 5.
- **Geen promptadvies.** Andere reeks, en het veroudert per modelrelease.
- **Geen volledige DDD- of Lean-introductie.** Beide worden gebruikt, niet uitgelegd.

### Risico's

1. **Deel 1 kan als management-essay gaan lezen.** Het moet eindigen in het drie-lussen-kader, dus in
   iets bruikbaars, niet in een pleidooi.
2. **Deel 7 en 8 kunnen overlappen.** De scheiding is lus 2 versus lus 3, en die moet in deel 7
   expliciet operationeel gemaakt worden. Lukt dat niet, dan is het één deel.
3. **Deel 9 is nu het dichtst bevolkt.** Vier tradities plus de semantische grens in één deel is
   veel. Als het niet past: de semantische grens (Evans, ?p=441) is al eerder behandeld en kan tot
   één alinea terug; de escalatietrap is het nieuwe deel.
4. **Deel 7 leunt op één casus** voor intent alignment; zonder tweede bron alleen het begrip
   gebruiken.
5. **Deel 6 kan als pleidooi voor slordigheid gelezen worden.** De twee harde grenzen (veiligheid,
   correctheid) moeten vroeg in dat deel staan.
6. **Het geopolitieke uitstapje in deel 1 kan ontsporen.** Geen klaagzang over Brussel, geen
   post-hoc-redenering over continenten, en het gewapende-robot-voorbeeld blijft eruit.


## 10. Spanningen en open vragen

Deze horen expliciet op tafel voordat er een reeks op gebouwd wordt.

1. **De explicitering-paradox.** Als tacit kennis inherent tacit is, is "intentie expliciet maken"
   als reeksbelofte te sterk. Alternatieve framing: intentie *toetsbaar* maken, of de lus sluiten
   tussen bedoeling en waarneembaar resultaat. Dit raakt de titel van de hele reeks.
2. **Declaratief werkt alleen bij bekwaamheid.** Zowel mission command als Anthropic's unhobbling
   werken bij een uitvoerder met oordeelsvermogen. Bij een zwakke uitvoerder is imperatief
   aansturen niet ouderwets maar juist correct. De reeks moet dit als as behandelen, niet als
   ladder waar declaratief altijd beter is.
3. **Observatie als elicitatie is een privacyvraagstuk.** Ambient meelezen in teamkanalen is
   technisch elegant en organisatorisch beladen. Als dit in de reeks komt, hoort de tegenwerping
   erbij.
4. **Meetbaarheid van intentie is deels een categoriefout.** Je kunt outcomes meten. Of de
   *intentie* geraakt is, is een oordeel, en dat is precies waarom rubrics interessant zijn. Waard
   om uit te zoeken hoe ver je hiermee komt.
5. **Naamgeving gelijktrekken** tussen de twee sites (§7.3).
6. **Is SDD-tooling tijdelijk?** Thoughtworks suggereert zelf dat teams de noodzaak van SDD-tooling
   moeten herijken naarmate modellen sterker worden. Als dat klopt, is een deel van het huidige
   gereedschap een compensatie voor modelzwakte en geen blijvende praktijk. Dat is een scherpe maar
   riskante stelling; verdient eigen toetsing voordat hij de reeks in gaat.
7. **Datumkwestie Thoughtworks Radar.** De volume-nummering rond spec-driven development (vol. 33
   versus vol. 34) is tegenstrijdig op de blip-pagina's. Verifiëren vóór publicatie.
8. **Arbitrage tussen agents.** De leesronde van §8b heeft de theorie voor conflicterende
   *menselijke* intenties gedekt (van Lamsweerde, Boehm, Evans, RAPID). Wat er gebeurt bij
   onverenigbare intenties tussen geautomatiseerde partijen is daarmee niet beantwoord. Deel 6 van
   de anatomie-reeks raakte dit aan met conflictresolutie over de contextgrens. Speculatiever dan de
   rest; hooguit één alinea in deel 9.
9. **Twee bronnen nog niet gelezen:** het GenAI SECI-paper (arXiv 2603.21866) en het intent
   drift-paper (arXiv 2606.05076). Beide direct relevant; verdienen een leesronde voordat delen 4
   en 5 geschreven worden.

---

## 11. Bronnen

**Eigen materiaal**
- intentdriven.nl — Centrale Dogma (Problem Space, Mental Models, Solution Space, Implementation
  Space), Engineering Profielen, kenniselicitatie, gezamenlijk modelleren, Naur-aanhaling.
  Inhoud opgehaald uit `src/content.js`.
- augmentedorganisation.nl, zone Managementstijl — Intent-ecosysteem, 2×2-matrix, Strategische
  Orchestrator. Inhoud opgehaald uit `js/augmented.js`.
- [?p=384 — AI als Socratische Requirements Engineer](https://edwinvandillen.nl/?p=384) — Polanyi,
  Vibe-fase, wat wil je bouwen versus wat wil je bereiken.
- [?p=441 — Context Matters](https://edwinvandillen.nl/?p=441) — Farley, Evans, feature-denker
  versus context-denker.
- [?p=310 — Wat je al weet maar nog niet zegt](https://edwinvandillen.nl/?p=310) — Team van Vijf,
  drie niveaus van reflectie, tacit kennis.

**Extern, gelezen**
- Anthropic / Thariq Shihipar, "The new rules of context engineering for Claude 5 generation
  models", 24 juli 2026.
- van Lamsweerde, "Goal-Oriented Requirements Engineering: A Guided Tour", RE'01.
- HPE en Cisco over Intent-Based Networking (translation, activation, assurance, optimization).
- Snowden & Boone, "A Leader's Framework for Decision Making", HBR november 2007 — de vijf
  domeinen; Disorder als "state of not knowing what type of causality exists, in which state
  people will revert to their own comfort zone". https://hbr.org/2007/11/a-leaders-framework-for-decision-making
- [Cynefin Domains, cynefin.io](https://cynefin.io/wiki/Cynefin_Domains) — Clear (sinds 2015;
  eerder Obvious, Simple, Known), sense-categorise-respond versus probe-sense-respond, "cause and
  effect can only be deduced in retrospect".
- [Aporetic Turn, cynefin.io](https://cynefin.io/wiki/Aporetic_Turn) — splitsing van Disorder in
  *confused* (inauthentiek) en *aporetic* (authentiek, productief niet-weten).
- Kritiek op Sineks Golden Circle: [Praise & Criticism: The Golden Circle](https://blog.hptbydts.com/praise-criticism-the-golden-circle-sinek)
  en [The Lizard Brain Myth, Shortform](https://www.shortform.com/blog/lizard-brain-myth/) — de
  neuro-onderbouwing ("firmly grounded in the tenets of biology") houdt geen stand.
- Wikipedia "Mission-type tactics"; US Army over commander's intent; AUSA over de
  implementatieproblemen van mission command.
- Kritiekliteratuur op Nonaka's SECI (scispace, RealKM).
- Anthropic, "Introducing Claude Tag" en TechCrunch, 23 juni 2026.
- Böckeler, "Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl", 15 oktober 2025 —
  de driedeling spec-first / spec-anchored / spec-as-source.
- Thoughtworks Technology Radar, blips "Spec-driven development" en "OpenSpec".
- Zhang & Xia, "Structured-Prompt-Driven Development", 28 april 2026 — REASONS-raamwerk, het
  begrip *intent alignment*.
- Morris, "Humans and Agents in Software Engineering Loops", 4 maart 2026 — de mens bij de lus,
  het bottleneck-argument.
- Böckeler, "Harness Engineering, first thoughts", 17 februari 2026 — bron achter de
  guides/sensors-taxonomie uit deel 5 van de vorige reeks, nu met datum.

**Extern, gelezen (leesronde intentie-arbitrage, 2026-08-09)**
- van Lamsweerde, Darimont & Letier, "Managing Conflicts in Goal-Driven Requirements Engineering",
  IEEE TSE 1998 — het begrip *divergentie* als zwakkere vorm van conflict, en resolutie via
  hermodellering.
- Boehm & Ross, Theory W (1989) en Boehm et al., "Using the WinWin Spiral Model: A Case Study",
  IEEE Computer, juli 1998 — success-critical stakeholders, win conditions, issues, options,
  agreements; win-lose wordt lose-lose.
- Evans, Context Mapping — Partnership, Customer/Supplier, Conformist, Separate Ways,
  Anticorruption Layer als *governance* van relaties tussen bounded contexts.
- Bain RAPID en DACI — beslisrechten, met exact één beslisser en het onderscheid tussen input en
  besluit.

**Extern, gevonden maar nog niet gelezen**
- "Tacit Knowledge Management with Generative AI: Proposal of the GenAI SECI Model", arXiv 2603.21866.
- "Bridging High-Level Intent and Network Execution: Detecting Violations and Intent Drift",
  arXiv 2606.05076.
