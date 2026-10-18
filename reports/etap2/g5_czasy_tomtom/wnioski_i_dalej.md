# Walidacja R6 względem TomTom: wnioski, pułapki i plan dalszej pracy

Data: 2026-10-18. Podsumowanie całej sesji walidacji czasów (D22). Szczegóły i wszystkie liczby: [g5_czasy_tomtom.md](g5_czasy_tomtom.md). Commity: `0a51f0b`, `1cea901`, `b33609a` (+ ten dokument).

Stan: **walidujemy R6, model się nie zmienił.** Następny etap to ulepszanie modelu, a potem ponowna kalibracja i walidacja tym samym narzędziem.

## 1. Co zrobiliśmy

| krok | wynik |
|---|---|
| dokumentacja endpointów | TomTom Routing dla `departAt` w przyszłości zwraca **typowy profil dnia tygodnia i godziny** (wtorki 20.10 i 27.10 identyczne). Przeszłość jest przyjmowana. Flow Segment Data to stan z chwili zapytania |
| regulamin TomTom | pkt 11.4, 11.6.1 i 11.6.10 → **wariant A (D22)**: odpowiedzi tylko w pamięci, do repo same agregaty, bez porównania TomTom–HERE |
| próbka | 30 par z planów R6 (r 8, c 6, o 4, t 6, h 6), 10 korytarzy GPR, 25 segmentów. 1/3 każdej warstwy odłożona do walidacji (`split.csv`) |
| czasy modelu | sonda po trasie modelu z czasami linków z eventów 5 runów R6; zgodna z nogami agentów (mediana 1,000) |
| pobrania | 4 pełne przebiegi po 149 requestów + 149 nieudanych (401) + 18 testowych = 763. Wyniki identyczne we wszystkich przebiegach |
| literatura | TAG M3.1 (DfT 2026), FHWA Travel Model Validation Manual (2010), oba w `data/raw/g5/lit/` |

## 2. Wyniki

Mediana model / TomTom oraz błędy, dla zestawu analizy i zestawu walidacji (analiza | walidacja):

| co | iloraz | MAPE | RMSPE | %RMSE (FHWA) | trasy w kryterium TAG (> 85% wymagane) |
|---|---|---|---|---|---|
| czas swobodny trasy | 1,18 \| 1,08 | 20 \| 23% | 29 \| 42% | 18 \| 14% | 37 \| 54% |
| czas rano 07:30 | 1,06 \| 1,02 | 18 \| 13% | 26 \| 21% | 16 \| 11% | 48 \| 77% |
| czas w południe | 1,04 \| 1,00 | 17 \| 14% | 27 \| 21% | 16 \| 11% | 63 \| 62% |
| prędkość swobodna segmentu | 0,84 \| 0,87 | 21 \| 18% | 24 \| 19% | 22 \| 18% | – |

- **Prędkości swobodne sieci są o ok. 15% niższe niż u TomTom** na A1 (112 wobec 130 km/h), DK (72 wobec 87–89) i DW. To niemal dokładnie factor 0,8 z D13. Rozrzut segmentów: y = 0,97x + 17,3, R² 0,86.
- **Czasy w oknach zgadzają się w medianie (1,00–1,06),** bo dwa błędy się znoszą: wolniejsze prędkości swobodne w modelu i brak opóźnień na skrzyżowaniach. TomTom dolicza ok. 8% przez cały dzień, model 1–4%.
- **Kongestia szczytowa:** przyrost rano względem południa w modelu (+3 pp) nie jest mniejszy niż u TomTom (+1 pp). Brak śladu brakującej kongestii, więc **przepustowości nie ruszać**.
- **Rozrzut per trasa jest duży** (RMSPE 20–27%). Najgorsze są krótkie trasy w mieście (0,6–1,6) i Krośniewice (2,0). Najwyżej (model wolniejszy) leżą A1, przejazd Objazdowa → Sklęczkowska i DK92 zach. (1,1–1,25).
- **Ocena:** R6 jest **skalibrowany tylko w popycie** (natężenia GPR) i **niezwalidowany według TAG** (czasy: 48–77% tras w kryterium wobec 85%). Zastrzeżenia: TomTom to model dostawcy, nie pomiar; trasy 2–50 km zamiast zalecanych 3–15 km; n małe; FHWA odradza testy „zaliczony / niezaliczony”.

## 3. Co poprawić w modelu (kolejność proponowana, każda zmiana wymaga wpisu w `DECISIONS.md` i testu 2 iteracji)

1. **Prędkości jako „cruise speeds” zamiast limit × 0,8 (D13).**
   - TAG §5.2.3: prędkość przejazdowa w modelu to średnia prędkość między kolejkami na skrzyżowaniach, a nie prędkość swobodna ani limit.
   - Dziś factor 0,8 jest w praktyce zastępczym narzutem skrzyżowań. Dlatego zgadzają się czasy tras, ale nie prędkości odcinków.
   - Wybór: (a) factor osobno per klasa drogi i miasto/poza miastem, kalibrowany na zestawie analizy; albo (b) prędkości bliżej `freeFlowSpeed` plus jawne opóźnienia węzłów, razem z G1.
   - Wariant (b) jest poprawniejszy, ale większy. **Podnoszenie samego freespeed bez opóźnień węzłów skróci czasy tras poniżej TomTom** (szacunek 8–15%).
2. **Drogi tertiary/unclassified poza miastami (72 km/h bez tagu).**
   - Audyt, walidacja GUS i ORS wskazują zawyżenie. TomTom tego nie rozstrzygnął: 6 z 7 segmentów odpadło w kontroli 50 m, n = 1.
   - Potrzebny osobny pomiar: trasy wybrane tak, żeby ≥ 70% długości leżało na tych klasach.
3. **Geometria linków z OSM.** Każdy link to dziś prosta z 2 punktów (A1 do 6,7 km). Bez kształtu nie działa zgodność tras (bufor 25 m), a kontrola segmentów odrzuca kręte drogi. Kształt przyda się też w Blenderze (G6).
4. **Skrzyżowania (G1).** Krótkie trasy w mieście mają największy rozrzut; brak opóźnień węzłów to najbardziej prawdopodobna przyczyna (interpretacja, nie pomiar).
5. **Korytarz Krośniewice (iloraz 2,0)** sprawdzić osobno (trasa modelu, zawrotki, przypięcie linków), razem ze znaną wadą liczników lokalnych.
6. **Otwarte z popytu** (`reports/etap2/audyt_g5/poprawki/podsumowanie.md`): bilans stref DK91/DK92 wsch., liczniki lokalne, podział Objazdowa/Bitwy, losowość estymacji (K = 20 punktów), brak niezależnych pomiarów w mieście.

## 4. Na co uważać (pułapki z tej sesji)

| pułapka | jak unikać |
|---|---|
| **Regulamin TomTom** (11.4, 11.6.1, 11.6.10) | odpowiedzi tylko w pamięci (`traffic_providers.py run`), do repo agregaty. Mapy i rozrzuty per obiekt tylko w `output/` (poza gitem). **Nie zestawiać TomTom z HERE** |
| klucz w `.env` w cudzysłowie dał 149 × 401 | naprawione (`api_key` zdejmuje cudzysłowy, przerwanie przy 401/403). **Zawsze najpierw `run tomtom --test` (9 requestów)** |
| dane znikają po przebiegu | każda nowa metryka lub wykres wymaga ponownego przebiegu (149 requestów). **Zanim pobierzesz, dopisz wszystkie metryki i sprawdź je w `selftest`** |
| TomTom `historic` to profil, nie pomiar | nie nazywać go „obserwacją”. `currentSpeed` ma sens tylko dla zapytania wysłanego w oknie dnia roboczego |
| proste linki MATSim | metryki geometryczne (bufor, odległość punktu) zawodzą na łukach. Selftest nie może dziedziczyć tej samej geometrii (`ERRORS.md` 23) |
| `bash -c "python -c '…'"` z backtickami | powłoka wykonuje `` `…` `` jako polecenie i ścieżki znikają z tekstu (dwa razy w tej sesji). Treść z backtickami zapisuj narzędziem Write/Edit |
| małe n i dwa zestawy | różnice model–TomTom poniżej ok. 5% nie są wynikiem. Analiza i walidacja różnią się o 4–10 pp |
| zestaw walidacji | **nie używać do wyboru korekty.** Korekty tylko z analizy, a walidacja ocenia je raz, na końcu |
| budżet requestów | wewnętrzny limit to 800 (zużyte 763). Darmowy próg TomTom to 20 tys. miesięcznie na API. Podniesienie limitu: decyzja użytkownika i zmiana `BUDGET` |

## 5. Jak powtórzyć walidację po zmianach modelu

1. Nowe runy (25%, 3 seedy MATSim + 2 seedy planów, jak R6).
2. **Zmienić w kodzie wskazanie na nowe runy:** `RUNS` i `META` w `pipeline/traffic_metrics.py`, `RUN` i `META` w `pipeline/traffic_providers.py`. Dziś wskazują na R6.
3. **Trasy modelu w `pairs.csv` pochodzą z R6.** Po zmianie prędkości trasy mogą się zmienić. Dwie opcje:
   - (a) te same pary i korytarze (porównywalność z R6), ale trasy z nowego runu; wymaga małej zmiany: kolumna `route` liczona w `cmd_model`, nie w `sample`;
   - (b) nowa próbka (`sample`) z nowym seedem.

   Rekomendacja: (a), żeby porównać R6 i nowy model na tych samych trasach.
4. `uv run python pipeline/traffic_metrics.py model`, potem `selftest`, potem `uv run python pipeline/traffic_providers.py run tomtom --test`, a na końcu `run tomtom`.
5. Raport: te same tabele (iloraz, MAPE, RMSPE, %RMSE, kryterium TAG), osobno dla analizy i walidacji, plus porównanie z R6.

## 6. Co robić dalej (propozycja kolejności)

1. Decyzja o wariancie prędkości (§3.1: a albo b) i wpis w `DECISIONS.md`.
2. Geometria linków z OSM (§3.3), bo bez niej nie ocenimy zgodności tras ani klasy tertiary/unclassified.
3. Implementacja wariantu prędkości, test 2 iteracji, runy 25% × 5.
4. Ponowna walidacja TomTom według §5, z próbką rozszerzoną o:
   - trasy 3–15 km (TAG §4.3.3);
   - trasy z przewagą tertiary/unclassified;
   - więcej tras miejskich (n ≥ 30 na zestaw).
5. Prędkość bieżąca w szczycie: zapytania Flow wysłane w dzień roboczy 7:00–8:00 i 15:00–16:00 (sesja musi trwać w tym oknie).
6. HERE: klucz i sprawdzenie warunków (AUP pkt 4). Tylko jako osobne źródło, bez zestawiania z TomTom.
