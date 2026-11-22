# 040 – AI-advies bij een evaluatie

**Status:** uitgewerkt <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-22

## Doel

Als **coach** of **gildemeester** wil ik een evaluatieverzoek aan een AI kunnen voorleggen en per gevraagde vaardigheid een advies over het niveau krijgen. Dan heb ik een tweede blik als ik mijn eigen beoordeling maak. Het advies is hulp en geen oordeel: de beoordeling blijft van de coach of gildemeester, en die geeft hem in Portflow.

De AI draait **lokaal op de laptop** (Ollama). Er gaan dus geen studentgegevens van de laptop af.

Bouwt voort op de evaluatiepagina van [spec 039](../039-evaluatie-voorbereiden/spec.md); het advies staat onderaan die pagina.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil. Het advies gaat over **alle** gevraagde vaardigheden, en bij elke staat wie hem beoordeelt ([vaardigheden-openict.md](../../docs/vaardigheden-openict.md)).

## Betrokken begrippen

- Vaardigheden en niveaus: [vaardigheden-niveaus-LEF.md](../../docs/vaardigheden-niveaus-LEF.md). De LEF-teksten zijn de maatstaf voor het advies.
- Evaluatieverzoek, zelfevaluatie, bewijsstuk: [begrippen.md](../../docs/begrippen.md)
- Namen verbergen: [spec 033](../033-namen-verbergen/spec.md)

## Functionele eisen

- [ ] **F1 – Advies vragen.** Onderaan de evaluatiepagina ([spec 039](../039-evaluatie-voorbereiden/spec.md)) staat een blok **"Advies (AI)"** met de knop **"AI-advies vragen"**. Pas na die klik gaat er iets naar het model.
- [ ] **F2 – Wat er meegaat.** Boven de knop staat wat er naar het model gaat. Een klik toont het overzicht met aantallen ("zelfevaluatie, 2 vaardigheden, 6 bewijsstukken waarvan 3 bestanden, 4 eerdere beoordelingen, 9 feedbackberichten"). Er gaat mee:
  - de toelichting en de zelfevaluatie per gevraagde vaardigheid, met het niveau dat de student aangeeft;
  - de LEF-teksten van alle niveaus van de gevraagde vaardigheden;
  - per gevraagde vaardigheid de bewijsstukken in de semesterperiode: de tekst van tekst-bewijsstukken en de inhoud van bestanden (zie F7);
  - eerdere beoordelingen van die vaardigheden: niveau, datum en tekst;
  - de feedbackvragen en reacties op die bewijsstukken.
- [ ] **F3 – Namen vervangen.** Vóór het versturen worden de naam van de student en andere bekende namen vervangen, zoals bij Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)): "Student", "Coach", "Medestudent 1" enzovoort. Namen in afbeeldingen kunnen niet worden vervangen, en in tekst uit bestanden alleen als ze precies zo geschreven zijn.
- [ ] **F4 – Bezig.** Een lokaal model kan er een paar minuten over doen. Tijdens het maken staat er "Advies wordt gemaakt…", met wat er klaar is ("bestanden lezen 3 van 5", "advies schrijven") en een knop **"Stoppen"**. De rest van de pagina blijft bruikbaar. Verlaat je de pagina, dan gaat het maken door; kom je terug, dan zie je de voortgang of het resultaat.
- [ ] **F5 – Advies per vaardigheid.** Per gevraagde vaardigheid, in de volgorde OC … RE:
  - wie hem beoordeelt (coach of gildemeester);
  - een **voorgesteld niveau** (`0` … `4`, zoals in de interface) naast het niveau dat de student zelf aangeeft;
  - een korte **onderbouwing**, met verwijzing naar de LEF-tekst van dat niveau en naar de bewijsstukken bij naam;
  - wat er nog **ontbreekt** of wat de student kan doen om verder te komen.

  Het advies is in het Nederlands en ontwikkelingsgericht geformuleerd, niet beoordelend ([design-system.md](../../docs/design-system.md)).
  - *Acceptatie:* bij een verzoek voor OC en KO staan twee adviezen, elk met een niveau, een onderbouwing die minstens één bewijsstuk noemt, en een ontwikkelpunt.
- [ ] **F6 – Duidelijk een advies.** Het blok zegt dat het advies door een AI-model is gemaakt, kan kloppen of niet kloppen, en dat de coach of gildemeester beslist. Daarbij staan het model en de datum. Het voorgestelde niveau valt minder op dan het echte niveau, dus het lijkt niet op een beoordeling.
- [ ] **F7 – Inhoud van bestanden.**
  - Word, PowerPoint en Excel: de tekst uit het origineel, zonder extra pakket (zip met XML, zoals de Excel-import van [spec 013](../013-excel-importeren/spec.md)).
  - Pdf: de tekst met het pakket `pypdf`.
  - Afbeeldingen: als afbeelding naar het model, als dat model afbeeldingen kan lezen. Kan het dat niet, dan gaat alleen de naam mee.
  - Video en andere soorten: alleen de naam.
  - Een bestand dat niet te lezen is, gaat mee met de naam en de opmerking "inhoud niet gelezen".
  - Het overzicht van F2 noemt welke bestanden alleen met hun naam meegaan.
- [ ] **F8 – Te veel.** Past niet alles in wat het model aankan, dan gaat de inhoud van bewijsstukken mee tot de grens: per vaardigheid evenveel, de nieuwste eerst. De rest gaat mee met alleen de naam, en het blok zegt dat.
- [ ] **F9 – Bewaren.** Het laatste advies per verzoek blijft lokaal bewaard, met het model en de datum. Als je de pagina opnieuw opent, staat het er meteen. **"Opnieuw vragen"** maakt een nieuw advies en vervangt het oude. **Alles verwijderen** ([spec 014](../014-alles-verwijderen/spec.md)) wist de adviezen.
- [ ] **F10 – Ollama niet klaar.** Draait Ollama niet, of is het gekozen model niet geïnstalleerd, dan staat er in plaats van de knop een korte uitleg:
  - waar je Ollama downloadt;
  - hoe je het model installeert, met de opdracht om te kopiëren (bijvoorbeeld `ollama pull gemma3:12b`);
  - een knop **"Opnieuw controleren"**.
- [ ] **F11 – Instellingen.** In Instellingen staat een sectie **"AI-advies"** met:
  - de status ("Ollama draait, model gemma3:12b geïnstalleerd");
  - een keuzelijst met de geïnstalleerde modellen, met als voorstel een model dat Nederlands kan en afbeeldingen leest (Gemma 3 12B, ongeveer 8 GB, voor laptops met 16 GB geheugen; een kleiner model voor minder geheugen);
  - het adres van Ollama, standaard `http://127.0.0.1:11434` en alleen een adres op de laptop zelf.

### Buiten scope

- AI-diensten buiten de laptop, zoals de Claude-API (niet gekozen, 2026-11-22).
- Beoordelen of het advies in Portflow zetten.
- Advies zonder evaluatieverzoek, bijvoorbeeld voor een hele student.
- Oudere adviezen bewaren: alleen het laatste blijft.
- De student informeren. Dat is de afweging van de coach of gildemeester; het dashboard toont er niets over (gekozen 2026-11-22).

## Schermen

Geen eigen ontwerp: een kaart onderaan de evaluatiepagina, in de stijl van het dashboard. Volgorde: kop "Advies (AI)" met model en datum → wat er meegaat (F2) → knop of voortgang → per vaardigheid het advies (F5).

## Data

- **Bron:** wat de evaluatiepagina al toont ([spec 039](../039-evaluatie-voorbereiden/spec.md)), plus de inhoud van bestanden. Voorbeelden haalt het dashboard uit de cache van [spec 038](../038-bestanden-bekijken/spec.md); Office-originalen haalt het live op en bewaart het niet.
- **Bewaard:** het laatste advies per verzoek in een nieuwe tabel: `review_request_id`, model, datum, per vaardigheid het voorgestelde niveau en de teksten, en de aantallen van F2.
- **Privacy:** alles blijft op de laptop. Ollama draait lokaal en het dashboard praat alleen met een adres op de laptop zelf. Namen worden toch vervangen (F3). [architectuur.md](../../docs/architectuur.md#privacy) wordt bijgewerkt.

## Technische eisen

- Ollama aanroepen met `urllib` (`POST /api/chat`, en `GET /api/tags` voor de modellen). Een JSON-schema in `format` geeft een vast antwoord per vaardigheid; het dashboard controleert dat antwoord voordat het iets toont.
- Alleen `127.0.0.1`, `localhost` of `[::1]` als adres van Ollama. Geen token en geen Portflow-gegevens naar andere adressen.
- **Nieuwe dependency `pypdf`** (zuiver Python), alleen voor tekst uit pdf's. De reden komt in de tabel in [architectuur.md](../../docs/architectuur.md): de standaardbibliotheek kan geen pdf lezen. Werkt de app ook zonder `pypdf`, dan gaat bij een pdf alleen de naam mee.
- De opdracht aan het model (rol, LEF als maatstaf, ontwikkelingsgericht, niet verzinnen, bewijsstukken bij naam noemen, Nederlands) staat op één plek in de code en is te testen.
- Het maken gebeurt in een achtergrondtaak, zoals Verversen, met voortgang en stoppen. Er loopt per verzoek één tegelijk.
- Tests met een nep-Ollama en verzonnen namen: wat er meegaat, het vervangen van namen, de grens (F8), een ongeldig antwoord van het model, en Ollama niet bereikbaar.

## Open vragen

- [x] AI-dienst: lokaal, met Ollama.
- [x] Model: een vast voorstel (Gemma 3 12B), te wijzigen in Instellingen.
- [x] Meesturen: zelfevaluatie, LEF-teksten, teksten van bewijsstukken, bestanden, eerdere beoordelingen, feedbackvragen en reacties.
- [x] Bestanden: tekst eruit halen; Office zonder pakket, pdf met `pypdf`, afbeeldingen als afbeelding.
- [x] Namen vervangen: ja.
- [x] Bewaren: het laatste advies per verzoek, lokaal.
- [x] Welke vaardigheden: alle gevraagde.
- [x] Student informeren: de afweging van de gebruiker; niets in het dashboard.

## Logboek

- 2026-11-22 – spec aangemaakt op verzoek van de gebruiker, als eerste schets naast spec 039
- 2026-11-22 – vragen beantwoord door de gebruiker: lokaal model met Ollama, Gemma 3 12B als voorstel, alles meesturen met tekst uit bestanden (`pypdf` voor pdf), namen vervangen, advies lokaal bewaren, alle gevraagde vaardigheden, niets over het informeren van de student; status uitgewerkt
