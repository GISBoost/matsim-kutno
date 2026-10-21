# D23 krok 4b (R7b) i krok 5 (walidacja TomTom): R7b vs R6

Data: 2026-10-21. Decyzja użytkownika: „robimy R7b, walidację po nim; wartościami f zajmiemy się później, przeanalizuj je po walidacji”. Poprzedni krok: [krok3_4_r7.md](krok3_4_r7.md). `f_g` bez zmian: A 0,95, B 1,00, C 0,60, D 0,70, E 0,85, F 0,55.

## 1. R7b: co zrobiono

| etap | wynik |
|---|---|
| model pracujących na sieci R7 (plany R1 `plans_g5r1k1_25pct`, bez tła i ciężkich, 3 seedy MATSim, 100 it.) | 7 478 nóg car na seedzie, 0 stuck (`r7b/check_r1_s*.json`) |
| estymacja O-D (`background_od.py 30 r7b_{lcv,heavy}_gpr … cls= drop=10045,91892,91119`, jak R6b; seedy planów p1, p2 jak w R6) | macierze `scenarios/kutno/demand/background_od_r7b[_p1\|_p2]_{lcv,heavy}_gpr.csv`; `od_warnings.py` bez flag we wszystkich 6 (`r7b/warn_r7b*.log`) |
| plany i pojazdy `plans_g5r7b[p1\|p2]_25pct` (`plans.py` z `background_od=`, `heavy_od=`, `seed=`) | 3 739 pracujących jak w R6; walidator ok, sha256 powtarzalny (`r7b/plans_r7b*/`); top-10 celów i domów to realne obiekty (`r7b/prerun_r7b.log`), max start 24 h + dojazd < endTime 48 h |
| runy 25% × 5, 100 it., ustawienia jak R6 (2 wątki, 3 GB) | `check_events.py --expect-car-legs`: 24 304 (×3), 24 252, 24 314, wszystkie ok, **0 stuck**, 0 przepełnionych linków (R6: 0) |

**Błąd znaleziony w trakcie i naprawiony.** `background_od.py`, `plans.py`, `border_zones.py`, `od_warnings.py` i `validate_plans.py` czytają na sztywno `scenarios/kutno/network.xml.gz`. Pierwsza estymacja szła więc po sieci R6 (macierz ciężkich wyszła identyczna jak R6b, co zdradziło błąd). W worktree `d23` podmieniłem `network.xml.gz` na sieć R7 (kopia R6: `network_r6.xml.gz`) i powtórzyłem estymację, plany i runy. W katalogu głównym `network.xml.gz` to nadal R6. **Przy scalaniu D23 do `main` ten plik trzeba podmienić świadomie.**

Macierze R7b względem R6b: lekkie 65 755 → 47 934 podróży/dobę (−27%; seedy planów −26 … −36%), ciężkie 22 972 → 19 368 (−16%). Udział km tła na drogach bez licznika spada (lekkie 33% → 11%). Estymator dopasowuje liczniki mniej ciasno niż w R6b (RMSE po linkach lekkie 38,6 wobec 3,7 poj./dobę), ale w runach liczniki mieszczą się w ±15% (niżej).

## 2. Krok 4b: natężenia R7b vs R6 vs GPR (mediana z 5 runów)

| | lekkie R6 | lekkie R7 (bez R7b) | **lekkie R7b** | ciężkie R6 | ciężkie R7 | **ciężkie R7b** |
|---|---|---|---|---|---|---|
| A1 (3 odc.) | 99% | 99% | **98%** | 101% | 98% | **101%** |
| DK w Kutnie (3) | 105% | 152% | **101%** | 68% | 109% | **83%** |
| DK pozostałe (9) | 82% | 147% | **90%** | 83% | 110% | **86%** |
| DW (5) | 60% | 90% | **77%** | 75% | 130% | **84%** |
| 15 odcinków w ±15% | 12/15 | 5/15 | **14/15** | 12/15 | 9/15 | **14/15** |
| mediana odchyłki (15) | 5,7% | 34,9% | **1,5%** | 2,6% | 8,1% | **3,0%** |

Poza ±15%: lekkie DW 10043 (118%), ciężkie DK 91878 (78%). Odcinki kontrolne: Objazdowa 91124 lekkie 128 → 131%, ciężkie 35 → 77%; Bitwy 91866 lekkie 78 → 64%, ciężkie 55 → 54% (rozrzut seedów planów 16–39%; nie są niezależnym testem, I2). Liczniki lokalne 10045 / 91892 / 91119 (poza dopasowaniem), lekkie: 36 / 60 / 55% (R6: 17 / 24 / 22%). Opóźnienie dobowe (poj.-h próbki): R7b 212,7–223,6 (seedy MATSim), p1 246,9, p2 208,9; R6 238,7–242,7, p1 298,2, p2 248,4. Okno 6–9: udział czasu w opóźnieniu 4,0–5,3% (R6 3,4–4,3%). Tabela per odcinek: `r7b/c7b_r7b_vs_r6.csv`, skrypt `c7b_r7b_vs_r6.py`.

**Wniosek:** po R7b zgodność z GPR jest nie gorsza niż w R6 (14/15 wobec 12/15 w obu klasach), a ruch z dróg lokalnych przestał się przelewać na DK. Brak przepełnionych linków, opóźnienie mniejsze niż w R6. Ostrzeżenie: R7b dopasowuje popyt do tych samych liczników, więc zgodność z GPR na 15 odcinkach nie jest testem niezależnym.

## 3. Krok 5: walidacja TomTom (jednorazowa)

Tryb `traffic_providers.py run tomtom --validate` (nowy, D22 wariant A): jeden zestaw odpowiedzi w pamięci oceniony dwa razy, model R6 (`pairs.csv`, `model_times.csv`) i R7b. **Trasy modelu R7b z runów R7b** (`traffic_metrics.py model_r7b`, zmiana z `wnioski_i_dalej.md` §5 pkt 3a): 120 par, w tym 23 z `experienced_plans` s4711 (osoby r, c, o i kilka t/h o tych samych końcach) i 97 najszybszych po czasie swobodnym sieci R7 (D23, korytarze, reszta t/h, bo id agentów tła zależą od macierzy). 63 z 120 tras jest identycznych jak w R6. Kontrola sondy: czas sondy / czas nogi agenta w R7b, mediana 0,998 (p5 0,88, p95 1,10, n = 81). Prędkości segmentów z sieci R7.

| | |
|---|---|
| dane | TomTom Routing `historic` (typowy wtorek, okna 07:30 / 12:30 / 15:30) i Flow Segment, wysłane 2026-10-21 18:52–18:55 UTC |
| requesty | 5 (`--test`) + 385; HTTP 200 × 384, 400 × 1 (jeden segment, bez wpływu na trasy). Łącznie od początku **1 627** z 2 000 (dziś 630). Klucz tylko z `.env`, w logach `***`. |
| trasy | 120 par × 3 okna; po kontroli 50 m 345 obserwacji (15 wykluczonych); w metrykach 38 tras walidacji i 77 analizy |
| kontrole | niezależny skrypt `check_niezalezny.py` zgodny dla R6. **Dla R7b nie obowiązuje**: czyta pliki modelu R6 na sztywno, więc zgłasza „false” z konstrukcji. Ścieżka kodu R7b jest ta sama (`selftest` przechodzi), ale niezależnej kontroli R7b nie mam (odpowiedzi nie są zapisane, powtórka wymagałaby 385 requestów ponad budżet 2 000). |

### Czas trasy, model vs TomTom historic (3 okna łącznie, zestaw walidacji, 38 tras)

Zestaw walidacji nie służył do dopasowania `f_g`. Zastrzeżenie: `f` wybraliśmy po dopasowaniu na zestawie analizy, a R7b przeliczył popyt; jeśli zmienimy `f` na podstawie tej tabeli, walidacja przestaje być niezależna i trzeba to zapisać.

| grupa | n tras | mediana R6 → R7b | MAPE R6 → R7b | RMSPE R6 → R7b | MAE [s] R6 → R7b | RMSE [s] R6 → R7b | w TAG R6 → R7b |
|---|---|---|---|---|---|---|---|
| A autostrada | 1 | 1,11 → 0,98 | 11,4 → 4,3% | 11,6 → 4,7% | 73 → 28 | 74 → 30 | 100 → 100% |
| B DK/DW poza | 4 | 1,21 → 1,07 | 23,9 → 21,9% | 29,6 → 26,6% | 148 → 125 | 174 → 145 | 33 → 50% |
| C lokalne poza | 7 | 0,82 → 0,99 | 17,9 → 7,3% | 19,1 → 10,9% | 125 → 62 | 153 → 103 | 38 → 76% |
| D osiedlowe poza | 4 | 1,11 → 1,21 | 37,8 → 47,0% | 44,0 → 53,8% | 111 → 125 | 146 → 142 | 50 → 25% |
| E główne w mieście | 4 | 0,79 → 0,82 | 21,2 → 22,2% | 22,0 → 22,9% | 81 → 82 | 86 → 86 | 42 → 17% |
| F lokalne w mieście | 5 | 0,75 → 0,84 | 25,2 → 25,4% | 28,8 → 28,3% | 129 → 106 | 152 → 116 | 20 → 27% |
| **wszystkie (z korytarzami i trasami agentów)** | 38 | 0,96 → 0,98 | **20,5 → 18,2%** | 26,2 → 25,7% | 110 → 90 | 135 → 116 | **48 → 58%** |

Dla „wszystkie” %RMSE (RMSE / średnia TomTom): 18,6 → 15,9%.

Zestaw analizy (77 tras, na nim dopasowano `f_g`): MAPE 18,3 → **14,7%**, RMSPE 24,7 → 21,5%, %RMSE 20,9 → 16,1%, MAE 114 → 85 s, RMSE 153 → 118 s, kryterium TAG 52 → **64%**, mediana 0,95 → 0,99. Przewidywanie z kroku 2 (f wg reguły, kongestia R6 stała): MAPE 14,3%, TAG 71%. R7b z naszymi `f` daje 14,7% i 64%, czyli kongestia R7b nie zepsuła założenia stałej Δ (różnica wynika z innych `f`).

**Łączenie okien:** MAPE, MAE, RMSE, RMSPE i TAG są ważone liczbą obserwacji (dokładnie), mediana ilorazu to średnia median okien (przybliżenie). Dokładne tabele per okno i podgrupa: `r7b/walidacja_r{6,7b}_tomtom.csv`; grupy: `r7b/walidacja_r6_vs_r7b_grupy.csv`; wykres: `r7b/walidacja_r6_vs_r7b.png`; błędy: `r7b/walidacja_r{6,7b}_tomtom_bledy.png`. Rozrzut czasów i mapa (wartości TomTom per obiekt) są w `output/g5_czasy_tomtom/`, poza repo (D22).

### Prędkość swobodna segmentów (Flow Segment; 16 segmentów w metrykach)

| | model / TomTom R6 | R7b | MAPE R6 → R7b |
|---|---|---|---|
| A1 (3) | 0,86–0,87 | 1,02–1,03 | 13,5 → 2,7% |
| DK poza miastem (5) | 0,81–0,82 | 1,01–1,03 | 18,3 → 3,4% |
| DW poza miastem (4) | 0,69–0,84 | 0,86–1,05 | 28 → 15% |
| miasto (3) | 0,72–0,91 | **0,62–0,65** | 19 → 36% |
| wszystkie (16) | 0,84–0,86 | 0,99–1,01 | 20,0 → 12,9% |

Miasto pogorszyło się (n = 3: model ok. 35% wolniejszy niż TomTom na segmentach primary/secondary/tertiary w mieście, czyli w grupie E).

## 4. Analiza współczynników f po walidacji (nic nie zmieniłem)

„Wskazane” = f × (mediana model / TomTom, walidacja), przy założeniu, że czas jazdy ∝ 1/f (bez +1 s na link i kongestii). **Przy n = 1–7 tras na grupę i przedziałach dopasowania ±0,07–0,17 to kierunki, nie liczby.**

| grupa | f teraz | dopasowanie z kroku 2 (90%) | wskazane przez walidację (n tras) | ocena |
|---|---|---|---|---|
| A | 0,95 | 0,92 (0,83–1,00) | ok. 0,93 (1) | zgodne; segmenty A1 1,02. Zostaje. |
| B | 1,00 | 1,02 (0,93–1,10) | ok. 1,07 (4) | model nieco wolny (mediana 1,07); segmenty DK idealne (1,01–1,03), DW za wolne. 1,00–1,05 mieści się w niepewności. |
| C | 0,60 | 0,60 (0,53–0,68) | ok. 0,59 (7) | **zgodne** (MAPE 17,9 → 7,3%, TAG 38 → 76%). Najmocniejszy wynik D23. |
| D | 0,70 | 0,75 (0,61–0,94) | ok. 0,85 (4) | model za wolny (mediana 1,21), MAPE 38 → 47%. 0,70 jest poniżej dopasowania i wskazania walidacji. Kandydat do podniesienia do 0,75–0,85. Mało tras. |
| E | 0,85 | 0,88 (0,73–1,05) | ok. 0,70 (4) | **sprzeczne**: dopasowanie mówi 0,88, walidacja tras i segmenty (model za wolny) wskazują 0,65–0,70. Trasy w mieście zawierają opóźnienia skrzyżowań, segmenty nie. Rozstrzygnie G1. |
| F | 0,55 | 0,50 (0,50–0,55, granica) | ok. 0,46 (5) | wskazanie na dole zakresu, MAPE bez zmian (25%). Współczynnik pochłania opóźnienia węzłów, schodzenie poniżej 0,5 nie ma sensu. Zostaje do G1. |

Wnioski:
1. **A i C pewne**, B w granicach niepewności (1,00–1,05). „Na dziś” są dobre.
2. **D** to jedyna grupa, gdzie R7b wyraźnie się pogorszył i dwa sygnały (dopasowanie, walidacja) wskazują wyższe `f`. Grupa ma 820 km sieci (1 617 linków), więc zmiana wpływa na wybór tras przez wsie.
3. **E i F (miasto)**: `f` miesza prędkość i opóźnienia węzłów, więc zgodność tras i segmentów jest sprzeczna. Rozstrzygnie G1.
4. **Kryterium TAG (> 85% tras w 15% lub 1 min) nie jest spełnione**: 58% (walidacja), 64% (analiza); R6 miał 48% i 52%. Poprawa jest realna, ale pozostały błąd to w dużej części skrzyżowania i wybór trasy, nie prędkość swobodna.

## 5. Ograniczenia i ZAŁOŻENIA

- Małe n w grupach walidacji (1–7 tras); mediana łączona z okien przybliżeniem.
- TomTom `historic` to model dostawcy, nie pomiar (D22/D23).
- Nowa estymacja O-D i `f` zmieniły się razem w R7b; wpływ O-D na czasy trasy idzie tylko przez kongestię (1–5% czasu trasy).
- Brak niezależnej kontroli metryk R7b (wyżej).
- Sieć R7 jest z tego samego OSM co R6, różni się tylko `freespeed` (`check_network_r7.py`).

## 6. Do decyzji

1. Czy **R7b zostaje nową bazą** (sieć R7, `f` z tabeli, macierze `r7b`, plany `plans_g5r7b*`) w configach (`config_*pct.xml`, `kutno.toml`) i `DECISIONS.md` (D23 przejmuje D13)?
2. Zmiana `f_D` (0,70 → 0,75–0,85) i ewentualnie `f_B` (1,00 → 1,02)? Każda zmiana wymaga R7c (estymacja + runy), a walidacja przestaje być niezależna.
3. Czy po D23 zamykamy G5 (etap 2 zamykają D23 + G3 + potwierdzenie G5, ROADMAP)?
