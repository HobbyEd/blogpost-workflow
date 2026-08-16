# Grok-review op het reeksontwerp "Intentie-gedreven engineering"

Datum: 2026-08-08. Ruwe kritiek van Grok via de MCP-server, plus mijn weging eronder.
Ingezonden: §1 (waarom) en §9 (de twaalf delen) uit `onderzoek-intentie-gedreven-engineering.md`.

---

## Ruwe kritiek (onbewerkt)

**1. Drie-lussenmodel als ruggengraat.** Het model is grotendeels een herverpakking: lus 1 is
standaard verificatie, lus 2 combineert Argyris' single-loop met IBN-assurance, lus 3 is letterlijk
Argyris' double-loop. De nieuwe waarde zit alleen in de expliciete stapeling en de volgorde-eis. Dat
mechanisme is niet aangetoond; het ontwerp laat onbesproken hoe een organisatie lus 2 en 3
operationeel scheidt zonder dat ze samenvallen of dat lus 3 terugvalt op subjectieve interpretatie.
Daardoor blijft het model descriptief in plaats van voorspellend.

**2. Convergentie van de vier tradities.** De vier voorbeelden delen alleen de oppervlakkige
formulering "zeg wat, niet hoe". Auftragstaktik is een commandostructuur met hiërarchie en sancties;
Goal-Oriented RE een formeel modelleersysteem met traceerbaarheid; Intent-Based Networking een
closed-loop controlesysteem met meetbare toestanden; AI-context engineering een prompting-strategie
zonder formele garantie. De mechanismen (verantwoordelijkheid, formalisering, observeerbaarheid,
inferentie) verschillen fundamenteel. De claim dat ze "hetzelfde punt" bereiken is pattern-matching
zonder gemeenschappelijk onderliggend mechanisme.

**3. Het "waarom nu"-argument via concurrentie.** Een drogreden van het type post hoc. Het
veronderstelt dat China en de VS sneller innoveren omdát ze intentie-gedreven werken, zonder te
laten zien dat dit de causale factor is in plaats van kapitaal, schaal, regulering of demografie. De
sterkste tegenwerping: Europa kent al decennia intentie-gedreven kaders (Europese normalisatie,
ISO 15288) maar vertaalt die niet naar lokale besluitvorming; het probleem zit in de vertaallaag,
niet in het ontbreken van het idee. Het ontwerp erkent dit zelf in de AI Omnibus-paragraaf, maar
gebruikt het niet om het concurrentie-argument te nuanceren.

**4. Interne spanning declaratief versus assurance.** De reeks bepleit "minder voorschrijven" maar
tegelijk "zwaardere toetsing" en "tests als uitvoerbare intentie". De voorgestelde oplossing
(imperatief deel eruit, declaratief deel erin) lost dit niet op: een test of rubric is per definitie
een specificatie van gewenst gedrag. Zolang lus 2 en 3 expliciete criteria eisen om te kunnen
sluiten, blijft de aanpak prescriptief op het niveau van de verificatie.

**5. Ontbrekende schakel.** De reeks mist een deel over conflicterende of onverenigbare intenties
tussen actoren (stakeholders, teams, systemen). Zonder mechanisme voor intentie-arbitrage of
prioritering blijft lus 3 theoretisch. Dit is de eerste tegenwerping die een criticus zal maken
zodra het model op organisatieniveau wordt toegepast.

**6. Overbodige of zwakke delen.** Deel 12 (recap) voegt niets toe. Deel 5 (AI als observator) is de
zwakste schakel: het introduceert een surveillance-kanttekening die nergens wordt uitgewerkt en die
het betoog over kenniselicitering onderbreekt zonder nieuwe argumenten.

**7. Volgorde.** Deel 11 (wie ermee kan werken) is te laat geplaatst. Het kwadrantenmodel en de
Cynefin-verwijzing zijn nodig om de haalbaarheid van lus 3 te beoordelen, maar komen pas na de
operationele lussen.

**Drie wijzigingen die de reeks het meest versterken:** maak expliciet welk nieuw mechanisme de drie
lussen toevoegen ten opzichte van Argyris plus IBN, of laat het model vallen als integratiekader;
vervang of nuanceer het concurrentie-argument door een kosten- en vertaallaag-argument dat
consistent is met de AI Omnibus-observatie; schrap deel 5 of integreer de surveillance-kritiek in
deel 3.

---

## Weging

### Punt 3 — snijdt hout, en dit is de belangrijkste correctie

Grok legt een interne inconsistentie bloot die ik zelf heb geïntroduceerd. Het ontwerp constateert
bij de AI Omnibus dat Europa's probleem de ontbrekende **vertaallaag** is, en gebruikt vervolgens
twee alinea's later een **concurrentie**-argument dat een andere oorzaak veronderstelt. Die twee
verhouden zich niet tot elkaar.

Zijn tegenwerping is bovendien sterk: Europa kent intentie-gedreven kaders al decennia. Het idee
ontbreekt niet, de vertaling ontbreekt. En de causale claim (China en de VS innoveren sneller *omdat*
ze intentie-gedreven zijn) is niet te onderbouwen tegenover kapitaal, schaal en demografie.

**Advies: het concurrentie-argument vervangen door het vertaallaag-argument.** Dat is consistent,
beter onderbouwd, en het maakt hetzelfde punt scherper: het verschil zit niet in wie het idee heeft,
maar in wie de lus sluit. De demografische cijfers en de robotica-voorbeelden blijven bruikbaar, maar
als illustratie van *een gesloten intentielus* (intentie → beleid → uitvoering → meting), niet als
bewijs van continentale superioriteit.

### Punt 5 — snijdt hout, en dit is de beste toevoeging

"Wiens intentie?" ontbreekt volledig. Het hele ontwerp behandelt intentie als iets van één partij,
terwijl elk echt project meerdere stakeholders met onverenigbare bedoelingen kent. Zonder arbitrage
is lus 3 inderdaad theoretisch: bij wie leg je de vraag "was dit de juiste bedoeling" neer?

**Advies: opnemen.** Samenvoegen met het bounded-context-deel tot één deel over de grenzen van een
intentie: hij is begrensd in *betekenis* (bounded context, semantisch) en in *eigenaarschap*
(conflict en arbitrage, politiek). Dat is coherent en het lost meteen het lengteprobleem op.

### Punt 2 — snijdt hout, maar de conclusie moet anders zijn dan Grok voorstelt

Hij heeft gelijk dat de vier tradities verschillende mechanismen hebben, en dat ik convergentie
claimde zonder een gedeeld mechanisme aan te wijzen. "Genoeg oordeelsvermogen bij de uitvoerder" is
een randvoorwaarde, geen mechanisme.

Maar zijn conclusie (pattern-matching, dus waardeloos) gaat te ver. Wat de vier delen is niet één
mechanisme maar **hetzelfde structurele probleem met vier verschillende oplossingen**: hoe delegeer
je werk aan een uitvoerder die het "hoe" zelf invult, zonder de grip op het resultaat te verliezen.
Auftragstaktik lost dat op met vertrouwen en training, GORE met formalisering, IBN met continue
meting, AI-context engineering met modeloordeel plus verificatie.

**Advies: de claim verzwakken en daarmee interessanter maken.** Niet "vier tradities zeggen
hetzelfde" maar "vier tradities lossen hetzelfde delegatieprobleem op, elk met een ander middel, en
software-engineering kan van alle vier iets lenen". Dat is toetsbaar, het geeft deel 1 een echte
analyse in plaats van een opsomming, en het levert meteen de vraag op welk middel bij agents past.

### Punt 1 — gedeeltelijk

Grok heeft gelijk dat lus 1 en 3 bestaande begrippen zijn en dat het model descriptief is. Maar een
integratiekader hoeft niet voorspellend te zijn om nut te hebben; het nut zit in de diagnose per
kwadrant en in de volgorde-eis.

**Advies: het model presenteren als wat het is, een integratiekader, en niet als nieuw model.** Dat
is eerlijker en het ontneemt de criticus zijn punt. Wel zijn tweede observatie overnemen: het
ontwerp moet zeggen hoe je lus 2 en 3 in de praktijk gescheiden houdt, anders vallen ze samen. Dat
is een concrete lacune in deel 8 en 9.

### Punt 4 — gedeeltelijk, en het antwoord staat er al maar te zwak

Grok stelt dat een test per definitie een specificatie van gewenst gedrag is, dus prescriptief. Dat
klopt, maar het is geen tegenspraak: het onderscheid is *wat* voorschrijven versus *hoe*
voorschrijven. Een test die zegt "gegeven X moet het resultaat Y zijn" laat de implementatie vrij.

Het ontwerp heeft dit antwoord al, maar als kanttekening aan het eind van deel 7 ("een test die de
implementatie vastpint is imperatief vermomd als verificatie").

**Advies: die kanttekening promoveren tot het dragende principe van deel 7,** in plaats van hem
achteraan te zetten. Dan is de spanning expliciet opgelost in plaats van weggemoffeld.

### Punt 6 — deels afwijzen

De recap schrappen is huisstijl-onkundig: de anatomie-reeks sluit ook met een recap, en die werkte.
Het is conventie, geen vulling.

Deel 5 schrappen gaat te ver, want de observator-rol is inhoudelijk het nieuwste van de hele reeks.
Maar Grok heeft gelijk dat het als los AI-tooling-deel de lijn onderbreekt.

**Advies: samenvoegen met deel 4 (elicitatie),** zodat AI-rollen verschijnen als antwoorden op de
kennissoorten uit dat deel in plaats van als eigen aflevering. De surveillance-kanttekening wordt dan
onderdeel van de afweging per techniek, waar hij thuishoort.

### Punt 7 — overnemen in afgezwakte vorm

Grok wil deel 11 naar voren. Het bezwaar daartegen blijft dat de kwadranten in de nieuwe opzet
gelezen worden als "welke lussen heeft dit kwadrant", en dat vereist de lussen.

**Advies: de kwadranten kort introduceren in deel 1** (ze staan al in de drie-lussen-diagnose), zodat
de lezer zich vroeg kan plaatsen, en de volledige behandeling achteraan houden.

---

## Voorgestelde herziene reeks: elf delen

> **Achterhaald op 2026-08-09.** Dit was de stand direct na deze review. De reeks telt inmiddels
> twaalf delen: er is een deel bijgekomen over de C-laag (Engelbart, Toyota Kata, "de machine die
> de machine bouwt") en deel 3 is herkaderd van muur naar bewegende grens. Zie
> `onderzoek-intentie-gedreven-engineering.md` §8c en §9 voor de actuele opzet. Hieronder blijft
> staan wat er toen is voorgesteld, als vastlegging van de weging.

1. Waarom intentie waarde draagt — met het **vertaallaag-argument** in plaats van het
   concurrentie-argument, en de vier tradities als **vier oplossingen voor één delegatieprobleem**.
   Introduceert de drie lussen als integratiekader en de kwadranten kort.
2. Wat intentie is, en waarom "begin bij het waarom" onvolledig is.
3. Waarom intentie zich verstopt, en waar de grens ligt.
4. Elicitatie naar kennissoort, en AI in drie rollen (samengevoegd, inclusief surveillance-afweging).
5. Van intentie naar vorm: declaratief vastleggen zonder dicht te timmeren.
6. De rol van de engineer: van hoe naar of — met "wat vastleggen, hoe vrijlaten" als dragend
   principe in plaats van als kanttekening.
7. Lus 2: heb je bereikt wat je bedoelde? Met expliciet: hoe houd je lus 2 en 3 gescheiden.
8. Lus 3: was het de juiste bedoeling?
9. **Wiens intentie, en waar houdt hij op** — nieuw. Conflicterende intenties en arbitrage
   (politiek), samengevoegd met de bounded context als betekenisgrens (semantisch).
10. Wie hiermee kan werken, en waarom dat geen karakterkwestie is.
11. Recap.

---

# Tweede Grok-review — 2026-08-09 (twaalf delen, na de herzieningen)

Ingezonden: de reeksintentie, het deel 1-materiaal, de C-laag en de twaalf delen. Deze keer
gevraagd om een tweezijdig oordeel: eerst wat sterk is, dan de verbeterpunten.

## Wat Grok sterk noemt

- **De herpositionering van AI als laatste partij** die een bestaand delegatieprobleem passeert in
  plaats van als oorzaak. "Dat maakt de reeks meteen anders dan de gebruikelijke *AI verandert
  alles*-verhalen."
- **De delegatietabel plus de expliciete afwijzing van een gedeeld mechanisme** dragen het meeste
  gewicht, omdat ze "een concrete vraag opleveren in plaats van een vage convergentieclaim".
- **Observaties 1, 3 en 4 zijn het sterkst verankerd**; ze volgen direct uit de tabel, de
  lus-scheiding en de kwadranten. **Observatie 2 en 5 zijn zwakker** als zelfstandige observatie,
  want ze zijn afgeleid van respectievelijk deel 3 en de delen 6-7.
- **Deel 9 en deel 10 zijn de twee functioneelste uitbreidingen**; ze dichten echte gaten.

Bruikbare bevestiging: de dragende elementen zijn ook voor een buitenstaander zichtbaar als dragend.
Met één correctie op de eigen lijst: observatie 2 en 5 horen niet in het rijtje "moet blijven
hangen"; het zijn onderbouwingen, geen conclusies.

## De verbeterpunten, gewogen

### De interne spanning die hij vindt — snijdt hout, en dit is de beste vondst

*"Lus 3 wordt in deel 7-8 gedefinieerd als zeldzaam en mensenwerk, terwijl deel 10 suggereert dat
je er systematisch beter in kunt worden. Die tegenstelling is nog niet opgelost."*

Dit raakt het mechanisme en niet de presentatie. Strikt genomen is systematisch beter worden in iets
zeldzaams niet tegenstrijdig (deliberate practice werkt zo), maar er zit een echt frequentieprobleem
onder: **een C-laag heeft feedback nodig, en lus 3 levert per ontwerp weinig gebeurtenissen.**

**De oplossing die het model strakker maakt:** de C-laag voedt zich niet op lus 3 maar op **lus 2**.
Elke uitkomstmeting levert twee dingen op: of de bedoeling gehaald is, en waar het
expliciteringsapparaat tekortschoot. Dat tweede is waarneembaar op lus 2-frequentie, dus per
release, en niet op lus 3-frequentie. Lus 3 blijft zeldzaam en mensenwerk; de methodelus draait mee
met de uitkomstlus. Dat hoort expliciet in deel 10.

### Deel 3 blijft verklarend terwijl de ambitie diagnostisch is — gedeeltelijk

Zijn stelling dat de threshold-of-knowledge-herkadering het probleem verplaatst in plaats van
oplost, gaat te ver: een reeks mag exposeren. Maar de kern is terecht: **deel 3 eindigt in een
inzicht en niet in een diagnose.** Concrete verbetering: laat deel 3 sluiten met de vraag hoe de
lezer vaststelt waar zijn *eigen* grens ligt, in plaats van met de constatering dat er een grens is.

### Twaalf delen te lang — deels afwijzen, deels een echte keuze

**De recap schrappen: afwijzen.** Dat zei hij bij de eerste review ook. De anatomie-reeks sloot
ermee en dat werkte; het is huisstijlconventie.

**Deel 4 als tweede kandidaat: dit verdient een besluit van Edwin.** Zijn argument is consistent:
techniekkeuze per kennissoort is *hoe doe je het*, terwijl de reeks zich beperkt tot herkaderen en
diagnosticeren. Daarmee legt hij een vork bloot die samenvalt met Edwins eigen zwakke punt 2
("diagnose loopt uit op zelfkennis, niet op een handeling"):

> **Is dit een puur diagnostische reeks, of een diagnostische reeks met een praktische streng?**

- *Puur diagnostisch:* deel 4 vervalt, de AI-rollen verhuizen naar één alinea in deel 3, de reeks
  gaat naar tien delen en wordt tonaal consistent. Prijs: het nieuwste materiaal (de observator,
  Claude Tag) verdwijnt grotendeels.
- *Diagnostisch plus praktisch:* deel 4 blijft en krijgt gezelschap van een praktische afsluiting
  per kwadrant. Dan is de reeksintentie te eng geformuleerd en moet "weet wat zijn eerstvolgende
  stap is" een volwaardige belofte worden in plaats van een bijzin.

Beide zijn verdedigbaar. Niet houdbaar is de huidige tussenstand: één praktisch deel in een verder
diagnostische reeks.

### Deel 11 doet twee dingen tegelijk — als vormrisico noteren

Kwadranten uitleggen én Cynefin-Disorder als verklaring inzetten. Zijn conclusie dat de reeks daar
"al klaar mee had moeten zijn" wijs ik af, want de kwadranten zijn de ontknoping. De vormobservatie
is wel bruikbaar: twee bewegingen in één deel vraagt strakke opbouw. Schrijfrisico, geen
herstructurering.

### Deel 1 als pleidooi — bevestigd

Tweede onafhankelijke waarneming van een punt dat al als zwakte stond genoteerd. Dat verhoogt het
gewicht.

## Netto acties

1. **Deel 10:** vastleggen dat de methodelus zich voedt op lus 2-frequentie, niet op lus 3.
2. **Deel 3:** laten eindigen in een diagnostische vraag in plaats van een inzicht.
3. **Observaties 2 en 5** uit de "moet blijven hangen"-lijst halen; het zijn onderbouwingen.
4. **Besluit voor Edwin:** puur diagnostisch (tien delen) of diagnostisch plus praktisch (twaalf,
   met verbrede intentie).
