# Backlog blogpost-onderwerpen

Onderwerpen en intenties voor blogposts op edwinvandillen.nl. Vul dit aan zodra we
onderweg nieuwe ideeën opdoen. Per onderwerp: de **intentie** (wat we ermee willen
bereiken), niet de uitwerking. De workflow-intake (fase 0) raadpleegt dit bestand.

---

## Reeks: De anatomie van agents

De reeks neemt de lezer **vanaf nul** mee: van "wat is een agent" naar "hoe bouw en
combineer je er een". Rode draad: agency is een instelbare knop; determinisme/autonomie
is een ontwerpkeuze per context (haakt aan bij de deterministisch-as- en Harnessing-lijn).
Opbouw: *definitie → onderdelen → één concrete agent → samenwerkende agents (binnen
één runtime) → harness verdiept (één agent) → gedistribueerde orchestration: concept →
autorisatie → techniek (A2A/MCP) → frameworks → recap.*

**Let op — herstructurering van het staartstuk (2026-07-29).** Het oorspronkelijke deel
6 ("de harness voorbij één agent") was te veel in één post gepropt. Het is opgesplitst in
vijf delen (6 t/m 10) zodat elk onderwerp lucht krijgt; dit wordt bewust een langere,
uitgebreidere staart en **deel 10 is de reeksafsluiter**. Daarna start een nieuwe reeks
(rondom intentie, zie onderaan dit bestand).

### Deel 1 — Wat maakt een agent een agent (gepubliceerd, ?p=455)
De definitie: een agent is een systeem waarin het model zelf de control-loop vasthoudt
(vs. een tool/workflow die de controle teruggeeft). Plus: agency als knop, orchestrator/
subagent als perspectief, en hoe Anthropic/OpenAI/Google/xAI het framen.

### Deel 2 — Waaruit een agent bestaat (gepubliceerd, ?p=459)
Overzicht van de zes onderdelen in twee lagen: model + tools + geheugen (het basisbouwblok,
de augmented LLM) en instructies + control-loop + harness (wat het tot agent maakt). Op
overzichtsniveau; eerlijk over waar bronnen anders indelen.

### Deel 3 — De anatomie in bestanden: hoe een agent er concreet uitziet (gepubliceerd, ?p=463)
*Uitgevoerd met twee subagents (schrijver + dunne deploy) i.p.v. één, om het determinisme-
aspect concreet te maken.*
**Intentie:** de abstracte zes onderdelen uit deel 2 tastbaar maken door één echte agent
als bestanden te tonen. De lezer heeft na twee delen abstractie recht op een "zo ziet het
er echt uit"-deel, en kan het daarna zelf nabouwen.
- **Voorbeeld:** Edwins eigen blogpost-workflow, ingeperkt tot **één subagent** (bv. de
  schrijver). Het geheel (meerdere agents) bewaren we voor deel 4.
- **Kern om te laten zien:** waar elk onderdeel woont — instructies = system prompt/config,
  tools = de tool-declaraties, geheugen = context-/geheugenbestanden, model = één regel in
  de config, harness = de omringende structuur (referentiedocs, scripts, gates).
- **Het inzicht:** de **control-loop zit niet in een bestand** maar in de runtime. Dat
  maakt zichtbaar wat je zelf ontwerpt en wat het framework levert.
- **Toon:** concreet en nabouwbaar; één framework als voorbeeld kiezen, benoemen dat het
  patroon generaliseert.

### Deel 4 — Samenwerkende agents: orkestratie en multi-agent (gepubliceerd, ?p=469)
**Intentie:** van één concrete agent naar meerdere die samenwerken. Bouwt voort op het
spectrum uit deel 1 (orchestrator/subagent als perspectief) en de concrete agent uit deel 3.
- **Voorbeeld:** de blogpost-workflow als geheel — orchestrator (hoofdthread) + subagents +
  het deterministische deploy-script.
- **Kern om te behandelen:** wanneer meerdere agents wél/niet lonen; orkestratie en handoffs;
  de generator-verifier-scheiding (loop engineering, Karpathy); gates en mens-in-de-lus.
- **Vooronderzoek:** de brede verkenning en de gebronde frameworkvergelijking
  (typologie-vraag, dun↔dik orkestrator-spectrum, de plaats van controle als as, landschap
  incl. LangGraph/CrewAI/OpenAI Agents SDK/Google ADK/Temporal) zijn in de post verwerkt.
  Het losse brainstormbestand is opgeruimd; de inhoud staat in de gepubliceerde post en in
  de git-historie.

### Deel 5 — Het harnessen van agents (gepubliceerd, ?p=473)
**Intentie:** in detail laten zien waaruit een harness bestaat. Directe verdieping op de
eerdere Harnessing-post (edwinvandillen.nl/?p=398, harness als ingenieursdiscipline) en op
deel 2, waar de harness bewust alleen is aangestipt.
- **Taxonomie als ruggengraat:** intent (kern-doel), constraints (regels/grenzen), sensors
  (input/waarneming van de huidige toestand), state management (historie en evolutie van
  context), instruction set (protocollen/werkwijzen).
- **Aanvullende lagen:** feedback-mechanismen (meten/evalueren van agent-prestatie),
  guardrails (veiligheidsgrenzen voor onvoorziene situaties), integraties (tools, data,
  API's — raakvlak met MCP).
- **Hier ook onderbrengen:** guides vs sensors en computationele vs inferentiële controls
  (Böckeler) — de kiem die eerder los in deze lijst stond.
- **Afbakening t.o.v. deel 2 (cruciaal):** zelfde ingrediënten, andere laag. Deel 2
  beschreef de onderdelen van de *agent*; dit deel beschrijft de *controlelaag* die de
  loop begrenst, observeert en bijstuurt. Zonder die positionering leest het als herhaling.

### Deel 6 — Coördineren over de contextgrens (gepubliceerd, ?p=477)
**Intentie:** de conceptuele omslag van deel 4 (orchestratie *binnen* één runtime) naar
orchestratie over agents die **gedistribueerd** zijn — in een andere runtime, een ander
team of een andere bounded context. Dit deel legt het *concept* uit; de techniek volgt in
7 t/m 9. Kernvraag: wat verandert er zodra het gedeelde substraat (runtime, geheugen,
system prompt) wegvalt?
- **Rode draad (uit redeneersessie 2026-07-29):** neem de vijf-plus-drie-taxonomie uit
  deel 5 en loop hem over de contextgrens. Alles wat binnen één runtime impliciet in code
  zat, wordt over de grens een expliciete vraag:
  - **intent → roldefinities** — een gedeeld doel zonder gedeelde bestuurder.
  - **instruction set → communicatieprotocol** — geen gedeelde system prompt meer; je moet
    een berichtformaat afspreken (preview A2A, uitgewerkt in deel 8).
  - **constraints/guardrails → autorisatie** — preview; uitgewerkt in deel 7.
  - **integraties → MCP (agent↔tool) vs A2A (agent↔agent)** — preview; uitgewerkt in deel 8.
  - **state management → federatie van bounded contexts** i.p.v. een globale store. Hier de
    Context Space-link (**verwijs naar [augmentedengineering.nl](https://augmentedengineering.nl)**,
    niet naar het nog niet-live concept-artikel). Cognitions "houd writes single-threaded"
    (deel 4) is over een grens niet meer in code afdwingbaar.
  - **sensors/feedback → conflictresolutie** — tegenstrijdige uitkomsten uit verschillende
    contexten: wie beslist?
- **Afbakening t.o.v. deel 4 (cruciaal):** deel 4 = *binnen* één runtime (orchestrator,
  subagents, handoffs, gates); dit deel = *over* contextgrenzen. Dit deel is concept/
  overzicht; 7 t/m 9 vullen de techniek in.
- **Te verifiëren bij onderzoek (niet aannemen):** RDMA als transport voor shared memory
  tussen agents — infrastructuurtechniek (HPC), waarschijnlijk schrappen tenzij een bron
  het in agent-context als gevestigde praktijk plaatst.

### Deel 7 — Agents, autorisatie én auditing (gepubliceerd, ?p=481)
**Intentie:** vóór de techniek eerst het uitstapje naar autorisatie. Nu regelen we
mens-in-de-lus met **harde gates**; dat is workflow-sturing, geen autorisatie. Zodra agents
over contextgrenzen resources van elkaar aanroepen, wordt echte autorisatie een productie-
eis. (Gepromoveerd uit "losse ideeën".)

**Uitgebreid (2026-07-29, BESLIST):** deel 7 behandelt niet alleen autorisatie maar
evenveel gewicht op **auditing**: niet alleen vooraf weten of een agent iets mag, ook
achteraf kunnen vaststellen wat een agent daadwerkelijk deed. Autorisatie is preventief,
auditing is detectief; over een contextgrens zijn beide nodig. De losse kiem
"Agents en traceability" (zie onder "losse ideeën") is
hierin opgenomen en uit de losse lijst gehaald; het is dezelfde vraag vanuit een andere
hoek.
- **Kernonderscheid:** workflow-gate (volgorde/akkoord) versus autorisatie (recht + budget
  + audit).
- **Eigen voorbeeld:** de **Grok-MCP-server** (waar kosten aan verbonden zijn) — wie/wat mag
  hem aanroepen, onder welke limieten, met welke verantwoording? Doorgetrokken naar audit:
  wat wil je achteraf kunnen aantonen (welke aanroep, door welk deel van de workflow, met
  welke kosten, geautoriseerd door wie)?
- **Tweede anker:** `posts/<slug>/state.json` (de eigen orkestrator-log) als illustratief
  "audit trail in het klein" — met de beperkingen (geen identiteit, geen
  integriteitsgarantie, geen tool-calls/kosten) als brug naar wat er over de grens bij moet.
- **Waarom vóór deel 8:** autorisatie is de constraint/guardrail-laag die je moet begrijpen
  voordat je agent↔agent- (A2A) en agent↔tool-koppelingen (MCP) veilig opzet.
- **Cursor-onderzoek (uitgevoerd 2026-07-29):** Cursor heeft met **Agent Trace v0.1.0**
  (RFC, agent-trace.dev, CC BY 4.0) een reëel, geverifieerd standaardiseringsvoorstel
  neergezet — maar dat gaat over **code-attributie** (welk model schreef deze regels),
  niet over agent-*handelingen* (welke aanroep, met welk recht, welk resultaat). Precies dit
  is het punt voor de post: standaardisering aan de detectieve kant is begonnen bij het
  makkelijkste stuk (herkomst van code); herkomst van handelingen ligt nog grotendeels
  open. Niet breder aannemen dan dit; zie het brainstormdocument §5 voor de volledige
  bronvermelding en de aanpalende initiatieven (OpenTelemetry GenAI-conventies,
  MCP-autorisatiespec, EU AI Act art. 12).
- **AI Act kort meenemen (BESLIST):** twee à drie zinnen over art. 12 (record-keeping voor
  hoog-risicosystemen), met reikwijdte-afbakening — geen dragend argument, wel de externe
  reden dat de detectieve helft niet optioneel is.
- **Te verifiëren bij onderzoek (niet aannemen):** bestaande standaarden/patronen voor
  agent-autorisatie (OAuth-achtige scoped tokens, MCP-authorisatie); de OpenTelemetry
  GenAI-conventies; de exacte AI Act-tekst — niet aannemen, uit primaire bronnen halen (zie
  brainstormdocument §8 voor wat al bevestigd is vs. nog open staat).

### Deel 8 — De techniek: MCP en A2A (concept in WordPress, post 485)
**Intentie:** de techniek onder gedistribueerde orchestration invullen. De twee integratie-
vragen die in deel 6 op conceptniveau werden aangestipt, hier concreet en scherp uit elkaar:
**agent↔tool = MCP, agent↔agent = A2A.**
- **Afbakening t.o.v. deel 6:** deel 6 introduceerde protocol/integratie op conceptniveau;
  hier de concrete werking — berichtformaten, transport, wanneer je wat kiest.

**Uitkomst van het onderzoek (2026-08-01/02, alle bronnen primair geverifieerd):**
- **De stateless MCP-update is gevonden, en het vermoeden klopte maar half.** Streamable
  HTTP dateert van revisie `2025-03-26` en is niet de stateless-stap. De eigenlijke stap is
  revisie **`2026-07-28`**: "Make MCP stateless: remove the `initialize`/
  `notifications/initialized` handshake" (SEP-2575), plus verwijdering van protocol-sessies
  en `Mcp-Session-Id` (SEP-2567), van resumability en van `ping`/`logging/setLevel`/
  `notifications/roots/list_changed`. **Kern:** het *protocol* wordt stateless, de
  functionaliteit niet — state verhuist naar de applicatielaag via expliciete,
  server-uitgegeven handles als gewone tool-argumenten.
- **A2A-governance geverifieerd:** door Google gedoneerd aan de **Linux Foundation** op
  23 juni 2025 (founding members AWS, Cisco, Microsoft, Salesforce, SAP, ServiceNow);
  v1.0.0 op 12 maart 2026, v1.0.1 op 28 mei 2026. IBM's ACP is erin opgegaan (datum staat
  niet op de ACP-site).
- **Dragende stelling (bewust als duiding geformuleerd, niet als protocolfeit):** de twee
  protocollen bewegen tegengesteld op state, te herleiden tot de eigendomsvraag over de
  loop. Let op voor hergebruik: bij A2A is dat verband gedocumenteerd (opaque execution,
  "without needing access to each other's internal state"), bij MCP níét — SEP-2567
  motiveert de stateless-stap vanuit clientcomplexiteit en veilige list-caching.

### Deel 9 (kandidaat) — Frameworks voor agent-orchestration
**Intentie:** de framework-vraag die in deel 4 bewust op landschapsniveau bleef
(LangGraph/CrewAI/OpenAI Agents SDK/Google ADK/Temporal e.a.) hier concreet maken: niet "welk framework is het beste" maar "welk type systeem bouw
je, en welk framework past daarbij". Aanleiding: IBM Technology, *"Agentic AI
Frameworks Explained"* (YouTube, https://youtu.be/ZVPlLaehjLk) — deelt frameworks in
naar vijf categorieën op architectuur/doel:
1. **Linear Workflows** (sequentiële pipelines, voorspelbaar/gecontroleerd) —
   LangChain, LlamaIndex, LangGraph.
2. **Autonomous Multi-Agent Systems** (doelgerichte autonomie, open-ended) —
   AutoGen, BabyAGI (experimenteel), CrewAI.
3. **Role-Based AI Systems** (rolgebaseerde samenwerking binnen strikte grenzen) —
   CrewAI, AutoGen (met structuur), ChatDev (niche, softwareontwikkeling).
4. **Production Orchestration Systems** (enterprise, diepe integraties, monitoring) —
   Microsoft Agent Framework (Semantic Kernel + AutoGen), LangGraph.
5. **Rapid Prototyping** (visuele no-code/low-code canvas) — LangFlow, Flowise.

Kernboodschap uit de video: niet het "beste" framework kiezen, maar de vraag stellen
welk type systeem je bouwt (vaste pipeline, autonoom team, productie-orchestratie of
prototype-canvas) en het framework daarbij zoeken.
- **Raakvlak met de reeks:** sluit aan op deel 6 (concept van gedistribueerde
  orchestration) en deel 8 (de techniek); welk framework past bij welk type gedistribueerd
  systeem. Haakt ook aan de plaats van controle / het orkestrator-spectrum uit deel 4.
- **Kritisch haakje (bewaren, dit maakt het meer dan een video-samenvatting):** de vijf
  categorieën zijn **niet orthogonaal**. Ze mengen doel-gedreven indeling (productie versus
  prototyping) met architectuur-gedreven indeling (lineair versus autonoom versus
  rolgebaseerd), en frameworks komen in meerdere categorieën terug (CrewAI, LangGraph).
  Dat zelf benoemen is waarschijnlijk het scherpste punt van de post.
- **Ook toetsen:** verhoudt Anthropics workflow-versus-agent-as (*Building Effective
  Agents*, al gebruikt in deel 4) zich tot IBM's "Linear Workflows" versus de rest als
  dezelfde as, of is het een andere indeling?
- **Te verifiëren bij onderzoek (niet aannemen):** de indeling/voorbeelden komen uit
  één bronvideo — bij uitwerking onderbouwen met primaire bronnen (framework-docs) en
  toetsen of de vijf categorieën ook elders zo worden gehanteerd of dat dit een
  IBM-specifieke indeling is. Verder: actuele status van BabyAGI (in de video zelf
  "experimenteel" genoemd) en naam/scope van het Microsoft Agent Framework (samenvoeging
  van Semantic Kernel en AutoGen); en of er naast de video een transcript of blogpost is.

### Deel 10 (kandidaat) — Recap: de reeksafsluiter
**Intentie:** de reeks afsluiten met een compacte recap. Van "wat is een agent" (deel 1) tot
gedistribueerde orchestration (deel 6-9), met de rode draad expliciet: agency als instelbare
knop, determinisme/autonomie als ontwerpkeuze per context, de harness als controlelaag.
- **Vorm:** kort en terugblikkend; één alinea of regel per deel, geen heruitleg.
- **Bruggen:** naar de bredere lijn Augmented Software Engineering
  ([augmentedengineering.nl](https://augmentedengineering.nl)) en een vooruitwijzing naar de
  **volgende reeks (rondom intentie, zie onderaan)**.
- **Dit is de laatste in deze reeks.** Daarna start de intentie-reeks.

---

## Reeks: Intentie-gedreven engineering (volgende reeks, twaalf delen)

**Status:** opzet gereed en herzien na Grok-review (2026-08-09). Volledige onderbouwing in
`onderzoek-intentie-gedreven-engineering.md`; de weging van de kritiek in
`grok-review-intentie-ontwerp.md`. Bij intake beide gebruiken, niet alleen deze samenvatting.

**Start pas nadat de anatomie-reeks is afgerond met deel 10 (concept 489).**

### De twee dragende keuzes

**Vertrekpunt is de waardevraag, niet de AI-ontwikkeling.** Begin je bij AI, dan is de reeks over
drie modelreleases verouderd. Openingsstelling: *AI heeft intentie niet belangrijk gemaakt. Het heeft
de laatste smoes weggenomen om er niet mee te beginnen.*

**Het argument voor "waarom nu" is de vertaallaag, niet concurrentie.** Niet "China en de VS
innoveren sneller dus intentie-gedreven werken loont" (dat is post hoc en niet te onderbouwen), maar:
Europa heeft de intentie op papier en de meetlat niet. Wat veranderd is sinds Ries en Argyris is dat
declareren, uitvoeren en toetsen van intentie voor het eerst grotendeels geautomatiseerd kan worden.

### De intentie van de reeks zelf (vastgelegd 2026-08-09, verbreed na de tweede Grok-review)

> De lezer stopt met AI als de reden te zien en herkent zijn eigen manier van sturen als het
> knelpunt; kan vaststellen waar hij staat; en weet welke eerstvolgende stap bij die positie hoort.

Drie bewegingen: **herkaderen** (delen 1 t/m 3), **diagnosticeren** (de lussen en de kwadranten) en
**handelen** (technieken, tests, werkwijze).

**Waarom verbreed.** De eerste formulering stopte bij diagnosticeren. Bij de tweede Grok-review
bleek dat inconsistent met wat de opzet al deed: deel 4 (elicitatietechnieken), deel 6 (tests als
uitvoerbare intentie) en deel 10 (de C-laag eindigt in een werkwijze) zijn alle drie praktisch. De
intentie liep dus achter op het ontwerp. Gekozen richting: de praktische streng blijft en wordt
volwaardig, in plaats van deel 4 te schrappen om tonale consistentie te kopen.

**Gevolg voor de opzet:** de praktische streng moet zichtbaar zijn als streng, niet als uitschieter.
Deel 11 sluit daarom af met de **eerstvolgende stap per kwadrant**; dat lost meteen het bezwaar op
dat de diagnose in zelfkennis blijft steken.

**De vijf observaties die moeten blijven hangen** (herzien: de oude nummers 2 en 5 waren
onderbouwingen, geen conclusies):

1. Dit is geen AI-verhaal. Vier vakgebieden losten hetzelfde delegatieprobleem op met vier
   middelen; agents zijn de nieuwste partij die de drempel passeert, niet de aanleiding.
2. Organisaties hebben één lus en denken dat ze er drie hebben. Output-sturing blijft bestaan omdat
   het de enige lus is die sluit.
3. **Je kunt agents niet volwassener aansturen dan je mensen.** Als er één zin blijft hangen, deze.
4. AI landt vrijwel overal op de A-laag (sneller bouwen), terwijl de hefboom op C zit (beter worden
   in het achterhalen van wat er moet gebeuren).
5. Leg het *wat* vast en laat het *hoe* vrij, ook in je tests. Dat is de praktische regel die de
   hele reeks samenvat.

**Drie punten om op te letten bij het schrijven:**

- **Deel 1 kan omslaan in een pleidooi**, want het is het enige deel met een overtuigingsdoel. Twee
  onafhankelijke reviews signaleerden dit. Discipline: elke alinea eindigt in een feit, niet in een
  oproep.
- **Deel 3 moet diagnostisch eindigen**, met de vraag hoe de lezer vaststelt waar zijn *eigen* grens
  ligt, in plaats van met de constatering dat er een grens is.
- **Deel 11 doet twee bewegingen** (kwadranten uitleggen, Cynefin als verklaring) en krijgt er nu een
  derde bij (stap per kwadrant). Vraagt strakke opbouw; splitsen als het niet past.

**Hoe we zouden merken dat de reeks zijn intentie haalt:** niet aan bereik (dat is precies de vanity
metric die deel 1 afwijst), maar aan lezers die zich in een kwadrant plaatsen en daarop reageren, of
die melden dat ze hun eerste uitkomstlus hebben gesloten. Klein en anekdotisch, maar het meet de
bedoeling in plaats van de verspreiding.

### De ruggengraat: drie lussen

Expliciet een **integratiekader**, geen nieuw model (lus 1 is verificatie, lus 3 is Argyris'
double-loop). De waarde zit in de stapeling, de volgorde-eis en de diagnose per kwadrant.

1. **Bouwlus** — hebben we het goed gebouwd? (iedereen) — Engelbart: A
2. **Uitkomstlus** — heeft het opgeleverd wat we bedoelden? (weinigen) — B
3. **Intentielus** — was dat wel de juiste bedoeling? (zeldzaam) — B/C
4. **Methodelus** — worden we beter in het vinden van intentie? (vrijwel niemand) — C

De eerste drie gaan over dít project, de vierde over de methode. Die vierde lus (deel 10) maakt de
grens uit deel 3 productief in plaats van beperkend, en lost daarmee de spanning op die bij het
toetsen van de reeksintentie naar voren kwam.

Feature Factory heeft alleen lus 1; Korte-termijn Optimizer 1 en 2 maar lokaal; Over-Engineered
Architect een verbeelde lus 3 zonder toetsing; Strategische Orchestrator alle drie, met lus 3 gevoed
door lus 2.

### De twaalf delen

1. **Waarom intentie het enige is dat waarde draagt.** Ries, Argyris, Double Diamond. De vier
   tradities (Auftragstaktik, GORE, IBN, context engineering) als **vier oplossingen voor één
   delegatieprobleem**, niet als convergentie. Het vertaallaag-argument. Eindigt in de drie lussen
   plus een korte introductie van de kwadranten.
2. **Wat intentie is, en waarom "begin bij het waarom" onvolledig is.** GORE-definitie, laagindeling,
   commander's intent. Naast Sinek in plaats van erachter.
3. **Waarom intentie zich verstopt, en waarom die grens beweegt.** Polanyi;
   expliciet/impliciet/tacit; SECI-kritiek. Niet als muur maar met Toyota Kata's **threshold of
   knowledge**: de grens ligt niet vast, het werk bestaat eruit hem te verleggen. Juist omdat
   explicitering onvolledig blijft is de lus de enige correctie die je hebt. **Eindigt
   diagnostisch:** hoe stel je vast waar jouw eigen grens ligt?
4. **Elicitatie: de techniek kiezen bij de kennissoort.** Per kennissoort meteen de bijbehorende
   AI-rol (interviewer, spiegel, observator met Claude Tag). Surveillance-afweging staat bij de
   techniek die hem oproept.
5. **Van intentie naar vorm: declaratief vastleggen zonder dicht te timmeren.** Anthropic's
   unhobbling; Böckelers spec-first / spec-anchored / spec-as-source.
6. **De rol van de engineer: van hoe naar of.** Dragend principe: leg het *wat* vast en laat het
   *hoe* vrij, ook in je tests. Hier wordt de schijnbare tegenspraak van de reeks opgelost (minder
   voorschrijven én zwaarder toetsen).
7. **Lus 2: heb je bereikt wat je bedoelde?** IBN-assurance, intent drift, rubrics, Cynefin-begrenzing.
   Plus expliciet: hoe houd je lus 2 en 3 gescheiden (wat staat ter discussie, welk ritme, wie draait
   hem).
8. **Lus 3: was het de juiste bedoeling?** Argyris, build-measure-learn, Naur.
9. **Wiens intentie, en waar houdt hij op.** Semantische grens (bounded context, Evans/Farley) plus
   de politieke grens als **escalatietrap**: (1) divergentie herkennen en wegontwerpen
   (van Lamsweerde 1998), (2) onderhandelen naar win-win (Boehm Theory W), (3) de structurele
   verhouding kiezen (Evans' Context Mapping: Partnership, Customer/Supplier, Conformist, Separate
   Ways) — dat is een architectuurbeslissing, geen bestuurlijke, (4) beslisrechten (RAPID/DACI).
   Stelling: wie bij stap 4 begint, heeft er drie overgeslagen.
10. **De machine die de machine bouwt: beter worden in expliciteren.** Engelbarts A/B/C-model en
    zijn claim dat een doorlopende C-activiteit de grootste hefboom is. Musk als herkenbare maar
    onvolledige illustratie: hij had een intentie (software-defined car, massa én kwaliteit), geen
    specificatie; de doorbraak kwam door kwaliteitsbevindingen terug te leggen in de *productie*.
    Voert de vierde lus in, met de frequentie erbij: **de methodelus voedt zich op lus 2, niet op
    lus 3.** Elke uitkomstmeting laat zien of de bedoeling gehaald is én waar het
    expliciteringsapparaat tekortschoot; dat tweede is per release waarneembaar, terwijl lus 3
    zeldzaam blijft. Consequentie: AI wordt vrijwel overal op de A-laag ingezet.
    *Doseren:* de auto-industrie is één alinea-illustratie over cyclustijd (48-54 maanden Duits
    versus 24-30 Chinees, BYD tot 18), zonder marktaandeelclaims — die bewegen te snel.
11. **Wie hiermee kan werken, en waarom dat geen karakterkwestie is.** Kwadranten als "welke lussen
    heeft dit kwadrant"; Cynefin-Disorder als verklaring. **Sluit af met de eerstvolgende stap per
    kwadrant**, zodat de reeks in een handeling eindigt en niet in zelfkennis.
12. **Recap.**

### Vaste afspraken

- **Compressie naar negen** als delen dun uitvallen: voeg 2 en 3 samen, en 5 en 6. Dragend zijn 1, 7,
  8, 9 en 10.
- **Geen tooling-vergelijking**, **geen promptadvies**, **geen volledige DDD- of Lean-introductie**.
- **Het geopolitieke uitstapje in deel 1** blijft een uitstapje, met drie verboden: geen klaagzang
  over Brussel, geen post-hoc-redenering over continenten, en geen gewapende-robot-voorbeeld (dat
  dient een andere intentie en ondergraaft het punt).

### Openstaand vóór intake

- **Arbitrage tussen agents.** De leesronde van 9 augustus dekte conflicterende *menselijke*
  intenties (§8b in het onderzoeksdocument). Wat er gebeurt tussen geautomatiseerde partijen is
  niet beantwoord; hooguit één alinea in deel 9, geen belofte.
- **Naamgeving gelijktrekken** tussen intentdriven.nl en augmentedorganisation.nl: dezelfde matrix,
  andere namen (Strategische Meedenker versus Strategische Orchestrator, Over-engineer versus
  Over-Engineered Architect, Short-term versus Korte-termijn Optimizer).
- **Drie bronnen nog niet gelezen:** GenAI SECI (arXiv 2603.21866), intent drift (arXiv 2606.05076),
  Böckeler "Context Engineering for Coding Agents".
- **Datumkwestie Thoughtworks Radar** rond de volumenummering van spec-driven development.


## Openstaande onderhoudsacties (reeks-breed)

- **Bronvermelding standaardiseren over delen 1-5 heen.** Gevonden door de
  reeks-consistentie-check op deel 5 (2026-07-24), niet-blokerend maar wel
  storend voor naslag:
  - **Anthropic-bron — BESLIST 2026-07-29:** reeks-standaard wordt **"Building effective
    agents"** (zonder "AI"), de zichtbare H1 op de pagina. Delen 1, 2 en 5 (al live) citeren
    nu nog *"Building Effective AI Agents"* en moeten naar deze vorm; delen 3 en 4 citeren al
    "Building Effective Agents" (hoofdletters gelijktrekken naar "Building effective agents").
    Deel 6 gebruikt de standaard meteen.
  - **Böckeler-bron:** delen 2 en 3 citeren *"Agent = Model + Harness"* als
    artikeltitel; dat is een kernzin úít het artikel, niet de titel. De echte titel
    is *"Harness engineering for coding agent users"* (martinfowler.com, 2 april
    2026) — deel 5 citeert dit al correct. Delen 2 en 3 hebben hier een
    bronvermeldingsfout die gecorrigeerd moet worden.
  - **Aanpak bij oppakken:** vastleggen welke citeervorm de standaard wordt in
    `reference/huisstijl.md`, dan delen 1 t/m 4 in één pas bijwerken en (waar al
    live) opnieuw deployen als concept-update.

---

## Losse ideeën / kandidaten voor latere delen

Verzamelplek; nog niet ingepland, nog geen volgorde.
- **Loop engineering als eigen deel** — Karpathy's autoresearch, de gen-verify-loop, de
  aparte verifier. In deel 2 kort genoemd in de control-loop-sectie.
- **Geheugen/context-engineering verdiept** — context window als begrensde hulpbron,
  kort/lang geheugen, context editing; haakt aan bij Context Matters / Context Space.
- **Evaluatie van agents** — hoe meet je of een agent goed werkt (buiten de reeks-scope van
  deel 1–2 gehouden).
- ~~Agents en traceability~~ — **opgenomen in deel 7** (2026-07-29): dit was dezelfde vraag
  (herleidbaarheid van agent-handelingen) vanuit een andere hoek als de auditing-uitbreiding
  van deel 7. Zie daar, inclusief het uitgevoerde Cursor-onderzoek.
- ~~**Agents en autorisatie**~~ — **gepromoveerd tot deel 7 van de reeks** (2026-07-29),
  zie hierboven. Niet langer een losse kiem.
