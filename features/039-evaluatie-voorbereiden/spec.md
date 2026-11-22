# 039 – Evaluatie voorbereiden

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-22

## Doel

Als **coach** of **gildemeester** wil ik vanuit "Te beoordelen" één evaluatieverzoek openen op een eigen pagina met alles wat ik nodig heb om het te beoordelen, zodat ik mijn beoordeling in Portflow goed voorbereid kan geven zonder zelf alles bij elkaar te zoeken.

Beoordelen zelf blijft in Portflow ([spec 030](../030-te-beoordelen/spec.md), buiten scope). Een AI-advies over het niveau is een aparte functie: [spec 040](../040-ai-advies-niveau/spec.md).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil in wat ze zien. Wie welke vaardigheid beoordeelt staat in [vaardigheden-openict.md](../../docs/vaardigheden-openict.md); de pagina laat dat per vaardigheid zien.

## Betrokken begrippen

- Evaluatieverzoek, zelfevaluatie, Te beoordelen: [begrippen.md](../../docs/begrippen.md)
- Vaardigheden OC … RE en hun niveaus: [vaardigheden-openict.md](../../docs/vaardigheden-openict.md), [vaardigheden-niveaus-LEF.md](../../docs/vaardigheden-niveaus-LEF.md)
- Weergave van niveaus en openstaand: [voortgangsregels.md](../../docs/voortgangsregels.md)
- Bewijsstukken en vermeldingen: [spec 034](../034-bewijsstukken-tijdlijn/spec.md), [spec 036](../036-bewijsstuk-lezen/spec.md), [spec 038](../038-bestanden-bekijken/spec.md)

## Functionele eisen

- [x] **F1 – Openen.** Een klik op een verzoek in **Te beoordelen** (pagina Evaluaties) of op een openstaande evaluatie op de **studentpagina** ([spec 032](../032-studentpagina/spec.md), F4; ook als die aan een andere beoordelaar is gericht) opent een nieuwe pagina voor dat verzoek. Kruimelpad "Evaluaties › <titel van het verzoek>". Bovenaan: de student (avatar en naam, link naar de studentpagina), de titel, de datum van indienen en de wachttijd.
  - *Acceptatie:* een klik op "OC & KO 1ste evaluatie" opent de pagina van dat verzoek met de naam van de student, de titel, de datum en "5 dagen".
- [x] **F2 – Stand van zaken.** De voortgangsregel van deze student: dezelfde niveaucellen als op **Overzicht**, in de compacte tabel van de studentpagina ([spec 032](../032-studentpagina/spec.md), F2). De kolommen van de gevraagde vaardigheden zijn gemarkeerd.
- [x] **F3 – Evaluaties per week.** De weekgrafiek met blokjes van deze student, zoals op de studentpagina ([spec 032](../032-studentpagina/spec.md), F3).
- [x] **F4 – Gevraagde vaardigheden.** Een overzicht van de vaardigheden in dit verzoek, in de volgorde OC … RE: code en naam, wie beoordeelt (coach of gildemeester), het huidige niveau en het niveau dat de student in zijn zelfevaluatie aangeeft.
- [x] **F5 – Zelfevaluatie.** De algemene toelichting van de student bij het verzoek (alleen bekend bij verzoeken aan de gebruiker; bij andere staat er "De toelichting is alleen zichtbaar voor de beoordelaar."), en per gevraagde vaardigheid de tekst van zijn zelfevaluatie, veilig getoond zoals in [spec 037](../037-evaluaties-lezen/spec.md).
- [x] **F6 – Vermeldingen zijn links.** Verwijst de student in zijn toelichting of zelfevaluatie naar een bewijsstuk (een vermelding "@naam"), dan is dat een link die het bewijsstuk in het zijpaneel opent, met de tekst of het bestand ([spec 036](../036-bewijsstuk-lezen/spec.md), [spec 038](../038-bestanden-bekijken/spec.md)) en de feedbackvragen erop.
  - *Acceptatie:* een zelfevaluatie met "@Onderzoek.docx" toont een link; een klik opent het zijpaneel met dat document als pdf.
- [x] **F7 – Tijdlijn bewijsstukken.** De tijdlijn met bewijsstukken per vaardigheid ([spec 034](../034-bewijsstukken-tijdlijn/spec.md)) over de **semesterperiode**, met alleen de rijen van de gevraagde vaardigheden. Daaronder de rijen **Feedbackvraag** en **Reactie** zoals op de studentpagina ([spec 035](../035-feedbackvragen/spec.md), F3), maar alleen voor de bewijsstukken van de gevraagde vaardigheden (toegevoegd 2026-11-23).
- [x] **F8 – Lijst bewijsstukken.** Per gevraagde vaardigheid een lijst van de bewijsstukken die de student er in zijn gedeelde collecties aan heeft gekoppeld: naam, soort, collectie, datum en het aantal feedbackvragen en reacties. Een klik opent het bewijsstuk in het zijpaneel. Over de semesterperiode; bewijsstukken die zijn toegevoegd of bijgewerkt **na de vorige beoordeling** van die vaardigheid, en bewijsstukken die de student in zijn zelfevaluatie noemt, zijn gemarkeerd.
- [x] **F14 – Verversen.** Klik je op deze pagina op **Verversen**, dan wordt deze student als eerste opgehaald ([spec 019](../019-eenvoudige-start/spec.md), F14). De pagina laadt zichzelf opnieuw zodra die student klaar is, en niet pas na de hele ronde. Dat gebeurt één keer per ronde. Hetzelfde geldt voor de studentpagina (toegevoegd 2026-11-22).
  - *Acceptatie:* bij 50 studenten toont de evaluatiepagina de bijgewerkte toelichting en zelfevaluatie al na de eerste paar studenten.
- [x] **F9 – Lege toestanden en fouten.** Zonder zelfevaluatietekst, bewijsstukken of verbinding met Portflow staat er per blok een korte melding; de rest van de pagina blijft zichtbaar. Een verzoek dat niet (meer) bestaat geeft een melding met een link naar Evaluaties.

- [x] **F10 – LEF-tekst.** Per gevraagde vaardigheid de LEF-tekst van het niveau dat de student aangeeft en van zijn huidige niveau, letterlijk uit [vaardigheden-niveaus-LEF.md](../../docs/vaardigheden-niveaus-LEF.md), in te klappen.
- [x] **F11 – Eerdere evaluaties.** Per gevraagde vaardigheid de eerdere beoordelingen: niveau, datum, beoordelaar en de tekst van de beoordeling.
- [x] **F12 – Feedbackvragen.** Per gevraagde vaardigheid de feedbackvragen en reacties op de bewijsstukken ([spec 035](../035-feedbackvragen/spec.md)), met het aantal; een klik opent het gesprek in het zijpaneel.
- [x] **F13 – Vorige / volgende.** Bij een verzoek uit Te beoordelen knoppen naar het vorige en volgende verzoek in die lijst (oudste eerst, zoals [spec 030](../030-te-beoordelen/spec.md), F2).

### Buiten scope

- Beoordelen in het dashboard; dat blijft in Portflow.
- AI-advies over het niveau: [spec 040](../040-ai-advies-niveau/spec.md).

## Schermen

Geen eigen ontwerp; in de stijl van de studentpagina ([spec 032](../032-studentpagina/spec.md)). Volgorde van boven naar beneden: kop met vorige/volgende (F1, F13) → stand van zaken (F2) → evaluaties per week (F3) → gevraagde vaardigheden (F4) → zelfevaluatie (F5, F6) → per gevraagde vaardigheid: LEF-tekst, eerdere evaluaties, bewijsstukken en feedbackvragen (F10, F11, F8, F12) → tijdlijn bewijsstukken (F7). De exacte indeling volgt bij het bouwen; bij een twijfel vraag ik het na.

## Data

- **Bron:** wat "Verversen" al bewaart: `received_requests`, `evaluations` (met de tekst van de zelfevaluatie, spec 037), `evidence_items` en `evidence_comments` (spec 034, 035). Bewijsstukken worden bij het openen op de achtergrond bijgewerkt, zoals op de studentpagina (spec 034, F1).
- **Nieuw:** de algemene toelichting (`review_request_note`) van het verzoek wordt bij Verversen bewaard in `received_requests` (gekozen 2026-11-22; [spec 030](../030-te-beoordelen/spec.md) is aangepast). Die staat alleen in verzoeken **aan de gebruiker**.
- **Vermeldingen:** `data-id` en `data-portfolio-id` van een vermelding verwijzen naar het bewijsstuk (API §6); een bewijsstuk dat niet in `evidence_items` staat, wordt live opgehaald.
- **Privacy:** alleen lokaal, zoals de rest; "Alles verwijderen" wist ook de toelichting.

## Technische eisen

- De zelfevaluatie en toelichting worden veilig getoond (`evidence.safe_html`), met vermeldingen als links in plaats van "[naam]".
- Hergebruik de bestaande onderdelen (voortgangsregel, weekgrafiek, bewijsstukkentijdlijn, zijpaneel); geen tweede implementatie van de voortgangsregels.
- Tests met verzonnen namen.

## Open vragen

- [x] 1. Toelichting: bewaren bij Verversen (spec 030 aangepast).
- [x] 2. Klikbaar: Te beoordelen én de openstaande evaluaties op de studentpagina (F1).
- [x] 3. Periode: de semesterperiode, met wat na de vorige beoordeling kwam gemarkeerd (F7, F8).
- [x] 4. Aanvullingen: LEF-tekst, eerdere evaluaties, feedbackvragen, vorige/volgende (F10–F13).

## Logboek

- 2026-11-22 – spec aangemaakt op verzoek van de gebruiker, met een voorstel en open vragen
- 2026-11-22 – vragen beantwoord door de gebruiker; F10–F13 toegevoegd; status uitgewerkt
- 2026-11-22 – gebouwd: `evaluation_page.py` (verzoek, vaardigheden, zelfevaluatie, LEF, eerdere evaluaties, bewijsstukken en feedbackvragen per vaardigheid, vorige/volgende), `lef.py` (leest de LEF-teksten uit `docs/vaardigheden-niveaus-LEF.md`, de enige bron), route `/evaluaties/<id>` met `evaluation_page.html`; de weekgrafiek staat nu in `_student_weeks.html` (gedeeld met de studentpagina). De toelichting wordt bij Verversen bewaard (`received_requests.note`, met migratie); tot de eerste Verversen staat er "Klik op Verversen". Vermeldingen worden links via `evidence.safe_html(…, mention)`; een genoemd bewijsstuk dat niet bewaard is, haalt het zijpaneel live op. De tijdlijn toont alleen de gevraagde vaardigheden, zonder de feedbackrijen (die staan per vaardigheid). Zijn de bewijsstukken nog niet opgehaald, dan laadt de pagina zich na het ophalen één keer opnieuw. F2 gebruikt de compacte tabel van de studentpagina (dezelfde cellen als Overzicht). Tests in `tests/test_evaluation_page.py`; met echte gegevens nagekeken (o.a. 10 klikbare vermeldingen, bewijsstukken en feedbackvragen per vaardigheid, vorige/volgende). Status klaar
- 2026-11-22 – gemeld door de gebruiker: na Verversen kwam de toelichting niet als eerste. Oorzaak 1: de student werd wel als eerste opgehaald, maar de pagina laadde zich pas na de hele ronde opnieuw (alleen Overzicht deed dat). Nu laadt de evaluatiepagina en ook de studentpagina zichzelf één keer opnieuw zodra die student klaar is (`Fetcher.fetched` en `round` in de status, `data-reload-when-fetched` in `app.js`); F14 toegevoegd. Oorzaak 2: bij een verzoek zonder toelichting geeft Portflow `null`; dat werd als "nog niet opgehaald" bewaard, waardoor "Klik op Verversen" bleef staan. Nu wordt het een lege toelichting. Met echte gegevens nagekeken: de pagina laadde zich na 4 van de 50 studenten opnieuw
- 2026-11-23 – op verzoek van de gebruiker: op de evaluatiepagina staan in de bewijsstukkentijdlijn nu ook de rijen Feedbackvraag en Reactie, zoals op de studentpagina, beperkt tot de gevraagde vaardigheden (`feedback.rows(..., skills)`). Test in `tests/test_evaluation_page.py`
