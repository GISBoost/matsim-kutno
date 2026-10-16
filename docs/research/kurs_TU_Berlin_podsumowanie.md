# Kurs MATSim TU Berlin (Kai Nagel i zespół VSP) — podsumowanie i wnioski

Dokument podsumowuje 10 wykładów + 9 ćwiczeń (seminar) z kursu „Multi-Agent Transport Simulation" prowadzonego przez twórców MATSim (Prof. Kai Nagel, TU Berlin, VSP). Traktujemy ten kurs jako **ground truth** — w razie sprzeczności z innymi źródłami (blogi, stare tutoriale, dokumentacja społecznościowa) wygrywa treść stąd.

Źródła: transkrypcje w `course/lecture/transcripts/` i `course/seminar/transcripts/`, slajdy w `course/converted_md/`.

## O czym jest kurs (ogólnie)

Kurs prowadzi od zera do samodzielnego stawiania i modyfikowania scenariuszy MATSim: od pętli koewolucyjnej (mobsim → scoring → replanning), przez pliki wejściowe (network, plans, config), multimodalność (rower/pedelec jako tryb teleportowany vs. sieciowy), transport zbiorowy (GTFS → transit schedule), aż po kalibrację (ASC, kalibracja dochodowa) i emisje. Uczy też **warsztatu pracy**: Git/GitHub (fork → clone → branch → PR), Maven, IntelliJ, VIA i SimWrapper do wizualizacji.

Kurs jest prowadzony na **realnych, małych scenariuszach**, nie na Łodzi/Berlinie w pełnej skali — dokładnie w duchu Twojego podejścia „najpierw mała miejscowość".

## Najważniejsze spostrzeżenia (rzeczy, o których warto pamiętać)

### 1. Konkretne, gotowe małe scenariusze używane przez twórców MATSim jako materiał dydaktyczny

- **matsim-kelheim** (`github.com/matsim-scenarios/matsim-kelheim`) — realne miasteczko w Bawarii (~17 tys. mieszkańców + okolica), próbka 25%, skalibrowany względem liczników ruchu i modal split. To jest **dokładnie ten typ scenariusza**, o którym mówiliśmy: mała miejscowość, w pełni otwarta, prowadzona przez twórców MATSim. Dobry wzorzec struktury repo i pipeline'u (nie architektury Łodzi — to inne miasto, inny kraj — ale jako **wzorzec metodologiczny i strukturalny**).
- **Serengetipark Hodenhagen** — mały scenariusz „zabawkowy" (park rozrywki), używany do ćwiczeń z transportu zbiorowego (dodanie linii wahadłowej/shuttle) i kalibracji tras rowerowych. Pliki już masz w `course/Seminar Files-20260701/`.
- Oba potwierdzają: **zaczynanie od małego, kompletnego scenariusza, a nie fragmentu dużego miasta, to standardowa praktyka samych twórców MATSim**, nie tylko nasz pomysł.

### 2. Minimalne wymagania danych wejściowych — populacja może być bardzo prosta na start

Cytując wprost: żeby uruchomić MATSim, plik `plans` (populacja) potrzebuje **tylko**:
- sekwencji typów aktywności (np. dom→praca→dom),
- współrzędnych aktywności (nie trzeba nawet linków sieci — MATSim sam dowiąże),
- w miarę realistycznego czasu zakończenia aktywności (end time) lub czasu trwania (duration — **nie oba naraz**, to psuje logikę),
- trybu (`mode`) dla każdego legu — **bez trasy** (routing dorobi to samo).

To bardzo obniża próg wejścia dla MVP: prosty model „dom-praca-dom" z realistycznym rankiem dojazdowym już daje sensowne, porównywalne z danymi wyniki (potwierdzone wprost przez Kai Nagela).

### 3. Zasada próbkowania (sample size) — z ćwiczeń, konkretna reguła kciuka

- **1%** wystarcza do analizy ruchu samochodowego/rowerowego/pieszego.
- **10%** to minimum przy transporcie zbiorowym opartym na rozkładzie (schedule-based PT) — inaczej pojazdy PT są nierealistycznie puste/pełne.
- **25%** potrzebne, gdy w grę wchodzi coś o małej pojemności na pojazd (taxi, DRT) — przy 1% jeden syntetyczny pasażer reprezentujący 100 osób realnych przeciąża abstrakcję (np. taksówka 4-osobowa „wozi" 100 ludzi).
- `flowCapacityFactor` i `storageCapacityFactor` w `qsim` trzeba zawsze skalować razem z próbką (np. 0.01 dla 1%).

To potwierdza i doprecyzowuje zapis już w `CLAUDE.md` — dodałem tę regułę tam.

### 4. Struktura config.xml i workflow pracy z kodem (potwierdzone wprost)

- Standardowy szkielet uruchomieniowy w Javie: `config → scenario → controller → controller.run()`.
- Pliki wejściowe **względne do lokalizacji config.xml** (albo URL) — nigdy ścieżki bezwzględne typu `/Users/ktoś/...` w commitowanym kodzie.
- `OverwriteFileSetting.deleteDirectoryIfExists` — standard w fazie iteracyjnego developmentu (nie `failIfDirectoryExists`, który jest domyślny).
- Duże pliki wejścia/wyjścia **nie trafiają do repo git** — trzymane osobno (u nich: `svn.vsp.tu-berlin.de/.../public-svn`, u nasododo ustalenia — potwierdza zapis już w `CLAUDE.md`).
- RAM: `-Xmx` ustawiane w VM options run configuration; scenariusz wielkości Kelheim (25% próbka małego regionu) potrzebował realnie ok. 10 GB.
- Workflow Git: fork → clone → branch → commit → push → Pull Request → merge → pull zmian z upstream. Uczony od pierwszych zajęć jako obowiązkowy nawyk.

### 5. Multimodalność — trzy sposoby symulowania trybu transportu

1. **Teleportowany** (najprostszy) — czas podróży liczony z `beelineDistanceFactor × dystans / prędkość`, bez realnej trasy. Dobre do szybkiego prototypu i trybów, których nie chcemy szczegółowo modelować (np. rower w mieście bez dobrej infrastruktury rowerowej).
2. **Trasowany po sieci (network mode)** — wymaga: dodania trybu do `qsim.mainModes`/`routing.networkModes`, oznaczenia linków dozwolonymi trybami (`allowedModes`), zdefiniowania typu pojazdu (`VehicleType`) z maksymalną prędkością, oraz **parametrów scoringu dla tego trybu** (inaczej MATSim rzuca błąd). Dopiero to daje realną wizualizację (agent faktycznie „jedzie" po sieci) i realną interakcję z zatorami.
3. **Pasażerski** (bus/tram/taxi) — agent wchodzi/wychodzi z pojazdu, trasa pojazdu jest niezależna od decyzji pasażera.
- Kluczowa uwaga: **rower jako network mode wymaga też `linkDynamics = PassingQ`**, inaczej wolniejsze rowery blokują szybsze samochody za sobą (kolejka FIFO).
- „Bicycle expressway" (droga rowerowa szybsza niż standard) — realizowane przez atrybut `bicycleInfrastructureSpeedFactor` na linku (bicycle contrib), nie przez zmianę prędkości maksymalnej pojazdu.

### 6. Transport zbiorowy (PT) — wprost potwierdza podejście z dokumentu badawczego

- Model wymaga: `transitSchedule.xml` (przystanki, linie, trasy, rozkłady) + `transitVehicles.xml` (typy i instancje pojazdów).
- **GTFS → MATSim**: konwerter `Gtfs2TransitSchedule` w `matsim-contribs`. Trzeba ręcznie: (a) rozszerzyć rozkład z GTFS (zwykle 0–24h) na pełną dobę symulacji (0–30h), kopiując pierwsze godziny; (b) zmapować trasy PT na sieć drogową — GTFS **nie zawiera** geometrii trasy, tylko przystanki, więc domyślnie MATSim rysuje linię prostą (beeline) między przystankami; jest eksperymentalny mapper (`PublicTransitMapper` z pt2matsim), ale wymaga ręcznej korekty.
- Częsty błąd: `awaitDeparture = false` zamiast `true` na przystankach — pojazd odjeżdża przed rozkładowym czasem, agenci „spóźniają się" mimo przybycia na czas. Zalecenie: zawsze `true`.
- Downscaling przy próbce: **liczba pasażerów spada, liczba kursów/pojazdów NIE** (inaczej PT kursowałby raz na godzinę i wyniki byłyby bez sensu).
- Brak danych o opóźnieniach w GTFS → symulacja zakłada PT zawsze punktualny (potwierdza ograniczenie, które i tak trzeba będzie zaadresować dla Łodzi).
- Taryfy PT: GTFS zwykle nie ma stref taryfowych w formacie maszynowym → MATSim domyślnie liczy tylko stały dzienny koszt PT, nie licznik zależny od odległości/strefy — istotne ograniczenie przy modelowaniu biletu strefowego ZDiT.

### 7. Scoring (funkcja użyteczności) — mechanika i domyślne wartości

- `betaPerforming` (nagroda za aktywność) domyślnie **6 utyli/h**; `betaTraveling` (kara za bycie w pojeździe) domyślnie **-6**, ale **rekomendacja: ustawić na 0 dla samochodu** i przenieść cały efekt do „opportunity cost of time" (czyli: siedzenie w aucie ≈ nicnierobienie, jazda kosztuje tylko przez to, że skraca czas na aktywności, nie przez dodatkową „niewygodę").
- Różnicowanie trybów: różnica między trybami (PT gorszy/lepszy niż samochód) wpisuje się jako **dodatkowy offset względem wartości bazowej auta**, nie jako niezależna liczba — inaczej łatwo o niespójność.
- **Kalibracja ASC** (alternative specific constant) metodą Flötteröda: iteracyjna korekta na podstawie różnicy między symulowanym a rzeczywistym udziałem modalnym (`asc_new = asc_old + ln(m_real) - ln(m_sim)` przybliżenie logitowe) — zaimplementowana w `matsim-python-tools` i szablonie `matsim-scenario-template/calibrate.py`. Konwerguje szybko (kilka iteracji MATSim), bo kierunek poprawki jest wyliczony analitycznie, nie zgadywany.
- **Utility of money zależny od dochodu** — od ok. 5 lat standard w produkcyjnych scenariuszach VSP: bogatsi mają wyższą gotowość zapłaty za oszczędność czasu. Wymaga przypisania dochodu (lub rozkładu Gini) do syntetycznej populacji — user guide/kod to wspiera.
- MATSim **nie jest** czystym modelem logitowym mimo pozorów — w praktyce (bo usuwa najgorszy plan i kopiuje najlepszy) zbiega do **maksymalizacji użyteczności** (best-reply), nie do rozkładu prawdopodobieństw. Efekt: przy dwóch podobnych opcjach model ma tendencję zbiegać do jednej, chyba że wprowadzi się heterogeniczność agentów (mikролokalizacja, dochód, gust) — to jest **wprost zbieżne z potrzebą realnej heterogeniczności populacji, którą i tak planujemy przez BREC+REGON**.

### 8. Podział pracy AI/programista wprost potwierdzony przez samych twórców

Nagel wielokrotnie podkreśla: błędy komunikatów są często mylące, trzeba szukać **pierwszego** błędu w logu, nie ostatniego; typowa pętla pracy to „zmień → uruchom zero iteracji → napraw błąd → powtórz"; zalecenie robienia commitów co godzinę/dzień, żeby móc się cofnąć. To potwierdza sens dzielenia pracy: iteracyjne poprawki i glue code — dobre zadanie dla AI; decyzje o tym, co „dobre"/"złe" w funkcji scoringu (normatywne) — świadomie zostawione osądowi człowieka nawet przez samych twórców MATSim.

## Rzeczy, które warto sprawdzić / uważać przy adaptacji do Łodzi

- **Emisje dla autobusów** — Kai Nagel przyznał wprost, że nie jest pewien, czy w scenariuszu Berlina emisje autobusów są w ogóle liczone (mało kto pyta, bo „autobus to zielony tryb"). Do zweryfikowania, jeśli emisje będą częścią analiz.
- **Cennik PT strefowy/dystansowy** — jawnie nierozwiązany problem nawet u twórców (49-euro-ticket w Niemczech zepsuł im dotychczasowe kalibracje dystansowe). Dla Łodzi: cennik ZDiT (strefy/bilety) będzie wymagał podobnego uproszczenia (constant dzienny vs. przybliżenie dystansowe) — decyzja do jawnego zapisania, nie do zgadywania.
- **Rower jako network mode** kosztuje dużo pracy (adnotacja linków, typ pojazdu, PassingQueue) — warto zacząć od trybu teleportowanego i przejść na sieciowy dopiero gdy będzie taka potrzeba (np. wizualizacja dla interesariuszy, o co Nagel też wprost prosi: „jeśli badasz rower, pokaż rowery w wizualizacji, inaczej ludzie ci nie uwierzą").
- **Model własności samochodu (car ownership)** — Nagel opisuje własne nieudane próby (student miał dobre połączenie PT, ale model odmawiał mu samochodu na inną, niepowiązaną aktywność) — **przestroga, żeby nie komplikować tego na starcie**, prostszy „coraz-to-jeden-parametr" jest bezpieczniejszy niż zewnętrzny model car-ownership bez dobrego strojenia.

## Co dalej

Materiał daje wystarczające pokrycie, żeby przejść do właściwych wytycznych budowy pierwszego demo (mała miejscowość) — łącznie z konkretną strukturą config/plans/network, konwencją nazewnictwa, oraz krokami pozyskania i przygotowania danych. To będzie osobny dokument.
