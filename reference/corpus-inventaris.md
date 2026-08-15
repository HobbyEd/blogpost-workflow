# Corpusinventaris — alles wat op edwinvandillen.nl staat

*Opgehaald op 2026-08-14 via de WordPress REST API, inclusief concepten: 61 posts,
waarvan 57 gepubliceerd en 4 concept.*

Dit bestand is het **vangnet onder de RAG-index**. De index (`scripts/rag_cli.py search`)
zoekt lexicaal: hij vindt "stroomopwaarts" wel, maar "de controle naar voren halen" niet.
Deze lijst vangt precies dat geval op. Loop hem door als je een onderwerp kiest of een
draft naast het archief legt, en zoek daarna gericht met `rag_cli.py` op de posts die
raakvlak lijken te hebben.

**Gebruik:**

1. `python3 scripts/rag_cli.py search "<onderwerp>" --top-k 12` — de treffers.
2. Deze lijst — de posts die de zoekopdracht mist omdat ze het idee anders benoemen.
3. `https://edwinvandillen.nl/?p=<id>` — de gepubliceerde tekst, leidend boven een
   lokale `draft.md`, want Edwin redigeert ook na publicatie.

**Over de kolommen.** `id`, `datum` en `titel` komen rechtstreeks uit de REST API.
`Kernbegrippen` is afgeleid: de onderscheidende termen per post, berekend als TF-IDF over
alle 61 posten en daarna opgeschoond. Het zijn dus de woorden die deze post van de rest
onderscheiden, niet per se de woorden die Edwin het belangrijkst vindt. `Raakt aan` is een
oordeel op basis van titel en termen, geen meting.

**Bijwerken.** Deze lijst veroudert bij elke nieuwe post. Werk hem bij zodra een post live
gaat, of haal hem opnieuw op met de REST API zoals beschreven in
`reference/externe-bronnen.md`.

---

## 1. Intentie-gedreven engineering (lopende reeks)

De reeks in uitvoering. Deel 1 staat live, deel 2 is concept, deel 3 is lokaal in
bewerking (`posts/intentie-3-waarom-intentie-zich-verstopt/`).

| id | datum | titel | kernbegrippen | raakt aan |
|---|---|---|---|---|
| 500 | 2026-08-11 | Intentie-gedreven engineering — deel 1: waarom intentie het enige is dat waarde draagt | meting, Ries, double-loop learning, assurance, bedoeling, uitvoerder, translation, Argyris | 243, 211, 251, 398 |
| 512 | 2026-08-12 *(concept)* | Intentie-gedreven engineering — deel 2: waarom 'begin bij het waarom' een stap overslaat | goal, Van Lamsweerde, intentie-laag, motief, Sinek, laagindeling, requirements | 500, 243, 384 |

## 2. Intentie, outcome en volwassenheid (het voorwerk van die reeks)

Dit cluster is het inhoudelijke fundament onder de intentie-reeks. Het valt structureel
buiten het venster van de twintig nieuwste posts, en werd daardoor eerder niet gevonden.

| id | datum | titel | kernbegrippen | raakt aan |
|---|---|---|---|---|
| 205 | 2026-01-11 | De Vier Dimensies van AI-Integratie in Software Engineering | vier dimensies, synthetische data, data engineering, privacy, exploratie, inconsistenties | 353, 211 |
| 211 | 2026-02-08 | De transitie naar de Strategische Orchestrator: Intentie-Ecosysteem Model | intentie-ecosysteem, outcome versus output, systeemdenken, lineair, workforce, verschuiving | 219, 251, 500 |
| 219 | 2026-02-16 | De synergie tussen intentie en volwassenheid: sturen op output versus outcome | Agile Fluency Model, zones, optimizing, strengthening, intentie-ecosysteem, team | 211, 224, 251 |
| 224 | 2026-02-22 | De Context-Match: waarom je teamfluency moet passen bij je probleemruimte | Cynefin, ongeordend, sense–respond, chaotic, focusing, strengthening, delivery | 219, 441 |
| 243 | 2026-03-08 | Intent-Driven Software Engineering: bouwen vanuit de bedoeling | kennis-elicitatie, articulatie, intentie, signalen, artefact, hypothese, cyclus | 500, 512, 384 |
| 251 | 2026-03-10 | Het vergroten van de outcome van Software Engineering | outcome, transformatie, Shapiro, organisatorisch, level, transitie, reis | 211, 219, 340 |

## 3. De anatomie van agents (afgeronde reeks, 10 delen)

| id | datum | titel | kernbegrippen | raakt aan |
|---|---|---|---|---|
| 455 | 2026-07-14 | De anatomie van agents — deel 1: wat maakt een agent een agent | control loop, script versus model, zelfsturend, workflow, OpenAI | 459, 489 |
| 459 | 2026-07-15 | De anatomie van agents — deel 2: waaruit een agent bestaat | control loop, instructies, harness, geheugen, tools, Anthropic, onderdelen | 455, 473, 489 |
| 463 | 2026-07-17 | De anatomie van agents — deel 3: een agent in bestanden | repo, bestanden, tools, blogpost-schrijver, blogpost-deploy, Claude | 459, 488 |
| 469 | 2026-07-21 | De anatomie van agents — deel 4: samenwerkende agents en de plaats van controle | orkestrator, multi-agent, subagent, sensoren, gates, plaats van controle | 477, 489 |
| 473 | 2026-07-27 | De anatomie van agents — deel 5: het harnessen van agents | harness, sensor, feedforward, constraints, Böckeler, harness engineering | 398, 459 |
| 477 | 2026-07-29 | De anatomie van agents — deel 6: coördineren over de contextgrens | contextgrens, boekhoud-agent, calculatie-agent, autorisatie, runtime | 481, 485 |
| 481 | 2026-08-01 | De anatomie van agents — deel 7: autorisatie en auditing over de contextgrens | auditing, agent-trace, hooks, recht, budget, spoor, aanroep | 477, 485 |
| 485 | 2026-08-03 | De anatomie van agents — deel 8: MCP en A2A, de techniek van de koppeling | MCP, A2A, streamable HTTP, protocollen, state, revisie, foundation | 481, 488 |
| 488 | 2026-08-05 | De anatomie van agents — deel 9: frameworks voor agent-orchestration | LangGraph, AutoGen, CrewAI, Microsoft Agent Framework, categorie | 485, 318 |
| 489 | 2026-08-08 | De anatomie van agents — deel 10: terugblik op de reeks | control loop, harness, agency, grens, autorisatie, onderdelen | alle delen |

## 4. Grip op het IT-landschap (afgeronde reeks, 3 delen)

| id | datum | titel | kernbegrippen | raakt aan |
|---|---|---|---|---|
| 417 | 2026-06-22 | Grip op het IT-landschap — deel 1: het landschap in kaart brengen met bounded contexts | capability, bounded context, canvas, vermogens, van onderaf/bovenaf, overzicht | 180, 419 |
| 419 | 2026-06-22 | Grip op het IT-landschap — deel 2: het landschap classificeren naar waarde en sourcing | core, onderscheidend, mission critical, standaardpakket, lenzen, kopen | 417, 421 |
| 421 | 2026-06-22 | Grip op het IT-landschap — deel 3: het landschap levend houden en de brug naar de Context Space | pace-layered, Gartner, commodity, context mapping, classificatie | 441, 449 |

## 5. Context, kennis en domeinmodellen

De lange lijn van Domain-Driven Design naar de Context Space. Hier zit het materiaal
waar de intentie-reeks op terugvalt als het over kennis en bedoeling gaat.

| id | datum | titel | kernbegrippen | raakt aan |
|---|---|---|---|---|
| 441 | 2026-06-29 | Context Matters: denken in contexten, niet in features | Context Space, Naur, Farley, theorie, kennis, schatkamer, feature | 421, 449, 224 |
| 449 | 2026-07-07 *(concept)* | De Context Space vastleggen: van SpecFlow-specificaties naar het Open Knowledge Format | Open Knowledge Format, SpecFlow, vier kennistypen, scenario, strategic knowledge | 441, 421 |
| 180 | 2021-05-22 | Bounded context: grote invloed op organisatiestructuur | bounded contexts, team-aligned, organisatiestructuur, orderverwerking, verantwoordelijkheden | 417, 67 |
| 67 | 2015-06-07 | EventStorming: zeker geen hype! | EventStorming, businessdomein, gebeurtenissen, modelleren, gezamenlijk, essentie | 180, 13 |
| 13 | 2007-07-06 | Ontmoeting Eric Evans | domeinmodel, ubiquitous language, ontwerpregels, verantwoordelijkheden, Evans | 67, 12 |
| 12 | 2007-06-20 | Waar ligt de essentie van jouw software? | essentie, businesslogica, businessprocessen, database, schermen | 13, 441 |

## 6. AI in de praktijk: harnessing, prompting, lokaal draaien

| id | datum | titel | kernbegrippen | raakt aan |
|---|---|---|---|---|
| 398 | 2026-05-24 | Harnessing: de ingenieursdiscipline die AI-engineering betrouwbaar maakt | harnessing, vibing, specing, stroomopwaarts, Böckeler, Pocock, Bender, process-contexten | 473, 500, 384 |
| 402 | 2026-05-31 | Liever moe dan lui: AI als je collega | Scherder, brein, engagement, overgave, syntax, worstelen, collega | 310, 258 |
| 384 | 2026-05-14 | AI als Socratische Requirements Engineer – tacit knowledge expliciet maken in de Vibe-fase | domeinexpert, socratisch, spec-fase, requirements engineer, prototype, interview | 243, 512, 398 |
| 370 | 2026-05-03 | Waarom lokaal AI draaien serieus wordt | Open WebUI, vLLM, LiteLLM, mcpo, Gemma, tool calling, Spark, stack | 318 |
| 366 | 2026-04-26 | L4 keynote — de slides zijn het bijproduct | slides, speaker notes, spec, narratief, dialoog, publiek, zaal | 274 |
| 353 | 2026-04-16 | AI-systemen worden deterministischer — en de grootste winst zit niet waar je denkt | determinisme, variabiliteit, verifieerbaarheid, requirements-fase, vier dimensies | 205, 384 |
| 340 | 2026-04-11 | AI adoptie is mensenwerk. De Augmented Organisation als navigatiekaart | Augmented Organisation, maturity scan, governance, adoptie, Promptington, augmenteren | 277, 251 |
| 318 | 2026-04-03 | Krijgen we een agentic agents besturings-systeem? | agentic, tool registry, sandboxing, identity, NemoClaw, acties | 455, 488, 370 |
| 310 | 2026-03-30 | Wat je al weet maar nog niet zegt — reflectie met AI in het Team van Vijf | Team van Vijf, reflectie, coachingrol, oefenruimte, niveaus van reflectie, drempel | 402, 277 |
| 277 | 2026-03-29 | Promptington — hoe je een organisatie prompt-bewust maakt, één stap per keer | Promptington, meta-prompting, temperatuur, bekwaamheid, ladder, twee teams | 340, 274 |
| 274 | 2026-03-26 | Prompt chaining — de brug naar agentic werken | prompt chaining, keten, tokenverbruik, complexe taak, stap, transcript, vaardigheid | 277, 455 |
| 258 | 2026-03-21 | Multimodaal leren — cognitive load is een vast volume en de vorm is aan jou | cognitive load, multimodaal leren, Barbapapa, breedte versus diepte, profiel, volume | 402, 310 |

## 7. Vroeger archief (2007–2022)

Korte posts uit de DDD-, architectuur- en DevOps-periode. Zelden direct bruikbaar als
bron, wel als bewijs dat een lijn er al langer ligt. Let op: de meeste zijn kort
(50–500 woorden) en vaak niet meer dan een aankondiging van een sessie of artikel.

| id | datum | titel | kernbegrippen |
|---|---|---|---|
| 195 | 2022-05-14 | Boekenplank, lente 2022 | Data Mesh, David Farley, Vaughn Vernon, process orchestrator, high performing teams |
| 189 | 2021-05-23 *(concept, 24 woorden)* | The machine that makes the machine | machine |
| 77 | 2020-01-04 | The Unicorn Project: must read… | Unicorn Project, Phoenix Project, code deployment, performance, lessen |
| 62 | 2013-06-12 | DevOps: hype of toch meer… | DevOps, productie, deployen, operations, continuous |
| 55 | 2009-08-06 | Paneldiscussie Model Driven Development | model-driven development, Devnology, platform, paneldiscussie |
| 51 | 2009-07-29 | Data Vault | Data Vault, hubs, attributen, modelleerstijl, objectmodel |
| 47 | 2008-11-03 | Computable Expert Panel | expert panel, Computable, discussie, softwareontwikkeling |
| 41 | 2008-09-01 | Smalltalk bijeenkomst | Smalltalk, ESUG, events pushen, framework, presentaties |
| 39 | 2008-08-13 | Mooie code! | mooie code, eindresultaat, schrijven |
| 35 | 2008-02-27 | Specificeren versus verifiëren | specificatietalen, test-driven development, contracten, Ruby |
| 27 | 2008-05-16 | SDN Architectuur track | software-architectuur, track, bijeenkomsten |
| 26 | 2008-01-25 | Enterprise architect en applicatie-architect: hoe kunnen ze elkaar begrijpen? | enterprise architect, applicatie-architect, architectuur, discussie |
| 25 | 2007-11-08 | DDD en DSL: een mooie combinatie! | domeingedreven, DSL |
| 23 | 2007-09-23 | SDC presentatie | NHibernate, sessie |
| 11 | 2007-06-17 | DDD in de praktijk | DDD |
| 10 | 2007-06-16 | Domain Driven Design: achtergronden en ervaringen uit de praktijk | domain-driven design, achtergronden, ervaringen |
| 9 | 2007-06-15 | Domain Driven Design and Lego Mindstorms NXT | Lego Mindstorms, Bluetooth, implementatie, domain-driven design |
| 8 | 2007-06-14 | Spreken op SDC, onderwerp: DDD en DSL: een mooie combinatie! | DDD, DSL, domein, sessie |
| 7 | 2007-06-13 | Agenda tot 13 juni 2007 | workshop, CIBIT, driven programming, studenten |
| 6 | 2007-06-06 | Text mining for portals: giving words a meaning | text mining, CIBIT, portals |
| 5 | 2007-06-05 | XML en UDDI: het ontdekken van diensten op het web | UDDI, XML, diensten ontdekken |
| 4 | *(concept, geen datum)* | Domain Driven Design en Lego Mindstorms | Lego Mindstorms, robot, inschrijvingen, sessie |

---

## Terugkerende begrippen en waar ze vandaan komen

De eigen terminologie, met de post die hem introduceert of het scherpst uitwerkt. Zoek
hierop als je wilt weten of een begrip al bezet is.

| begrip | eerste/scherpste vindplaats |
|---|---|
| Augmented Organisation | 340 |
| Promptington | 277 |
| harnessing / vibing / specing | 398 |
| stroomopwaarts | 398 (de eigen positionering tegenover Böckeler; komt verder nergens voor) |
| Context Space | 441, vastgelegd in 449 |
| Open Knowledge Format | 449 |
| bounded context | 180, toegepast in 417 |
| intentie-ecosysteem | 211 |
| Agile Fluency-zones (focusing, delivering, optimizing, strengthening) | 219, toegepast in 224 |
| Cynefin / probleemruimte | 224 |
| control loop | 455, uitgewerkt in 459 |
| harness | 459, uitgewerkt in 473 |
| plaats van controle | 469 (bewust Nederlands, niet "locus of control") |
| contextgrens | 477 |
| Team van Vijf | 310 |
| cognitive load als vast volume | 258 |
| double-loop learning (Argyris) | 500 |
| intentie-laag versus motief (Van Lamsweerde) | 512 |
