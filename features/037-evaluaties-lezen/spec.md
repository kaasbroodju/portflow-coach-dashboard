# 037 – Evaluaties lezen in een zijpaneel

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-18

## Doel

Als **coach** of **gildemeester** wil ik op een evaluatie kunnen klikken en in een zijpaneel lezen wat de student in zijn zelfevaluatie schreef en wat de coach of beoordelaar erop antwoordde, op dezelfde manier als de feedbackvragen en reacties ([spec 035](../035-feedbackvragen/spec.md)). Zo hoef ik voor een coachgesprek niet naar Portflow.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Evaluatie, zelfevaluatie, beoordeling, evaluatieverzoek ([begrippen.md](../../docs/begrippen.md)); openstaande evaluatie `?` ([voortgangsregels.md](../../docs/voortgangsregels.md#openstaand))

## Functionele eisen

- [x] **F1 – Teksten bewaren bij Verversen.** De ophaalronde ([spec 005](../005-gegevens-ophalen/spec.md)) bewaart voortaan per feedback item ook de **tekst** (de toelichting van de student bij een zelfevaluatie, of de beoordeling door de coach of beoordelaar). Die tekst zit al in wat Verversen ophaalt; er komen geen extra verzoeken bij. *Dit wijzigt spec 005, F2, waarin toelichtingsteksten bewust niet werden bewaard (keuze van de gebruiker, 2026-11-18).*
- [x] **F2 – Zijpaneel per evaluatieverzoek.** Een klik op een evaluatie opent rechts een zijpaneel (hetzelfde paneel als bij de feedback) met het **hele evaluatieverzoek**: de titel en datum van indienen, en per vaardigheid in het verzoek (in de volgorde OC … RE) als gesprek:
  - de **zelfevaluatie** van de student (niveau dat hij zichzelf geeft, als dat er is, datum, tekst);
  - de **beoordeling(en)**: wie, rol (coach, gildemeester, overig), niveau, datum, tekst;
  - nog niet beoordeeld: "Nog niet beoordeeld."
  - *Acceptatie:* een klik op "OC 1" van een verzoek met OC en KO toont het verzoek met voor OC en KO de zelfevaluatie en de beoordeling.
- [x] **F3 – Waar je klikt.**
  - de **blokjes** in "Evaluaties per week" op de studentpagina ([spec 032](../032-studentpagina/spec.md));
  - de **cellen** (niveaulabels) in de tabellen op Overzicht, Evaluaties en de studentpagina; een cel met meer evaluaties (bijvoorbeeld `1/2`) toont alle verzoeken van die vaardigheid onder elkaar, het nieuwste bovenaan. De details bij hover blijven bestaan;
  - de **stippen** in "Bewijsstukken per vaardigheid" ([spec 034](../034-bewijsstukken-tijdlijn/spec.md)): het paneel toont alleen het **bewijsstuk** (naam, soort, vaardigheden, bij tekst de tekst zoals in [spec 036](../036-bewijsstuk-lezen/spec.md)) met de feedbackvragen en reacties erop; geen evaluaties. Bij een stip met meer bewijsstukken staan ze onder elkaar. *Gewijzigd 2026-11-18 op verzoek van de gebruiker: eerst stonden hier ook de evaluaties van de gekoppelde vaardigheden, dat was te veel informatie.*
- [x] **F4 – Veilig tonen.** Teksten worden getoond met alleen eenvoudige opmaak, zoals in [spec 036](../036-bewijsstuk-lezen/spec.md), F4.
- [x] **F5 – Namen verbergen.** Met Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)) aan geldt de vervanging ook in dit paneel.
- [x] **F6 – Zonder tekst.** Is een evaluatie opgehaald vóórdat de teksten bewaard werden, of heeft hij geen tekst, dan staat er "(geen tekst)"; na de volgende Verversen staan de teksten erbij.

### Buiten scope

- Zelf beoordelen of reageren (dat gebeurt in Portflow).
- Evaluaties in het paneel van een bewijsstuk.

## Schermen

Geen eigen ontwerp: het zijpaneel van [spec 035](../035-feedbackvragen/spec.md).

## Data

- **Bron:** de feedback items die Verversen al ophaalt (`GET /portfolios/{id}/goals/{id}/feedback-items`); de tekst staat in `evaluation.comment` (HTML), live nagekeken bij het bouwen (§4.5 van de API-documentatie).
- **Bewaard:** de tekst per feedback item, in de tabel `evaluations`.
- **Privacy:** teksten van studenten en docenten staan alleen in de lokale database; "Alles verwijderen" wist ze; reservekopieën volgen de bestaande regels.

## Technische eisen

- Eén template voor het gesprek per evaluatieverzoek, gebruikt door alle drie de ingangen van F3.
- Tests met een nep-Portflow.

## Open vragen

- [x] Waar klikken: blokjes, tabelcellen en de stippen van de bewijsstukken (F3).
- [x] Teksten: bewaren bij Verversen (F1).
- [x] Inhoud: het hele evaluatieverzoek (F2).
- [x] Een stip van een bewijsstuk: alleen het bewijsstuk met feedbackvragen en reacties (F3; eerst ook de evaluaties van zijn vaardigheden, op 2026-11-18 teruggedraaid).

## Logboek

- 2026-11-18 – spec aangemaakt op verzoek van de gebruiker; vragen beantwoord; status uitgewerkt
- 2026-11-18 – gebouwd. Tekst in `evaluations.text` (`portflow_fetch.parse_feedback_item`, migratie in `db._migrate`); gesprekken per verzoek in `dashboard/evaluation_panel.py`; één template-macro voor het gesprek (`_conversation.html`), gebruikt door `_evaluation_panel.html` (blokjes, cellen) en `_evidence_panel.html` (stippen). Het zijpaneel staat nu in `base.html`, zodat het ook op Overzicht en Evaluaties werkt. Bij de stip staan eerst alle bewijsstukken met hun feedback, daarna één keer de evaluaties van hun vaardigheden (geen herhaling bij meer bewijsstukken). Iemand die coach én gildemeester is, heet bij een productvaardigheid gildemeester en anders coach. Een evaluatie zonder verzoek (zoals in de demo) opent alleen. Getest in `tests/test_evaluation_panel.py` en met echte gegevens na Verversen
- 2026-11-18 – bekende beperking: Namen verbergen vervangt volledige namen; een voornaam in de tekst zelf (zoals "Hoi Joost" aan het begin van een tekst) blijft staan
- 2026-11-18 – F3 aangepast op verzoek van de gebruiker: een stip toont alleen het bewijsstuk met feedbackvragen en reacties, zonder evaluaties; gebouwd
