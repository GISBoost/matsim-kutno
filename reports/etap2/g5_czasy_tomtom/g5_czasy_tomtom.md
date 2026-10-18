# G5: walidacja czasów przejazdu i prędkości R6 względem TomTom

Data: 2026-10-18 (niedziela). Zadanie: `prompt.md` w tym folderze, decyzja D22 (wariant A). **Walidacja, nie kalibracja.** Model nie został zmieniony.

## Na górze

| | |
|---|---|
| runy MATSim | R6, 5 runów 25% × 100 it.: `output/g5r6_25pct_s{4711,1,2}` (seedy MATSim), `output/g5r6p{1,2}_25pct_s4711` (seedy planów). Bez nowych runów |
| zapytany dzień i godziny | **wtorek 2026-10-20, 07:30 / 12:30 / 15:30 CEST** (`departAt` w przyszłości, czyli typowy profil historyczny dnia tygodnia i godziny). Model to uśredniony dzień roboczy, nie data |
| kiedy faktycznie wysłano | 2026-10-18 (niedziela wieczorem): 17:23–17:24, 17:59–18:00 i **18:02:51–18:03:51 UTC** (ostatni, w `przebieg_tomtom.json`) |
| zestaw tylko do walidacji | `split.csv`, zapisany przed policzeniem jakiegokolwiek błędu: 1/3 każdej warstwy, czyli 13 z 40 par i korytarzy oraz 8 z 25 segmentów. Nieużyty do propozycji |
| requesty | **TomTom: 614** (budżet podniesiony z 400 do 650 na prośbę użytkownika o MAE, wykresy i mapę). 149 nieudanych w przebiegu 1 (401, klucz w cudzysłowie w `.env`, `ERRORS.md`), 18 testowych (`--test`), 3 × 149 właściwych (każdy: 148 × 200, 1 × 400 dla segmentu). Ostatni przebieg: 2026-10-18 18:02:51–18:03:51 UTC. Liczba w przebiegu = dry-run (149). **HERE: 0** (brak klucza) |
| czego endpointy nie umieją | TomTom Routing dla przyszłej daty zwraca typowy profil, a nie predykcję konkretnego dnia. Flow Segment Data to stan z chwili zapytania, więc w niedzielę nie mierzy szczytu dnia roboczego (porównujemy tylko `freeFlowSpeed`). Szczegóły w §1 |
| czego nie ma w repo | odpowiedzi TomTom (tylko w pamięci procesu), czasy i prędkości TomTom per para/segment, porównanie TomTom–HERE (regulamin, niżej) |

**Regulamin TomTom i wariant A (D22).** Regulamin TomTom (Terms and conditions, https://docs.tomtom.com/legal/terms-and-conditions, odczyt 2026-10-18) koliduje z pierwotnym projektem zadania:

| punkt | treść (skrót) | koliduje z | rozwiązanie (wariant A) |
|---|---|---|---|
| 11.4 | przechowywanie i cache wyników zabronione, z wyjątkiem cache w kliencie zgodnie z nagłówkami cache-control i nie dłużej niż ich max-age. Flow Segment Data ma `Cache-Control: public, max-age=0` | surowe JSONL w `data/raw/g5/tomtom/` i cache wznawiania (prompt §6) | odpowiedzi tylko w pamięci procesu; brak plików i wpisów w manifeście; wznowienie = ponowne requesty w budżecie |
| 11.6.1 | zakaz tworzenia „secondary or derived database” z treści TomTom, także łączonej z własnymi danymi | tabela czasów TomTom per para w repo | do repo trafiają tylko agregaty (n, mediana, MAPE, RMSE per zestaw, rodzaj i klasa drogi) |
| 11.6.10 | zakaz „check, compare or benchmark” z podobnymi produktami konkurentów TomTom bez pisemnej zgody | porównanie TomTom–HERE (prompt §7.4) | §7.4 wypada. Porównujemy TomTom z modelem MATSim, który nie jest produktem konkurencji |

HERE: Acceptable Use Policy (https://www.here.com/en-gb/terms/acceptable-use-policy-january-2022, odczyt 2026-10-18), pkt 4, ogranicza „benchmarking”, „copying, storing” i „creating derivative works”, chyba że prawo albo umowa pozwala. Przed użyciem HERE trzeba to sprawdzić z aktualnymi warunkami. Klucza HERE nie ma.

Przebieg (`uv run python pipeline/traffic_providers.py run tomtom`) w jednym procesie:
1. wysyła partie probe, main i flow;
2. liczy metryki (`traffic_metrics.compare`) i kontrole §8;
3. uruchamia niezależną kontrolę `check_niezalezny.py` jako osobny proces z danymi przez stdin;
4. zapisuje `metrics_tomtom.csv`, `przebieg_tomtom.json` i wykres agregatów.

Odpowiedzi znikają z końcem procesu.

## 1. Dokumentacja endpointów (odczyt 2026-10-18)

### TomTom Routing API `calculateRoute`
Źródło: https://docs.tomtom.com/routing-api/documentation/tomtom-maps/calculate-route

- `departAt`: domyślnie `now`, inaczej `dateTime`; bez offsetu przyjmowana jest strefa punktu startu. **Dokumentacja nie mówi, czy przeszłość jest dozwolona** ani od kiedy ruch bieżący przestaje się liczyć. SDK JS (https://docs.tomtom.com/maps-sdk-js/api-reference/types/services.DepartArriveParams.html) podaje, że przy dacie z przeszłości system wraca do wartości domyślnej. Partia `probe` sprawdziła to empirycznie (korytarz K_dk92z_in, 4 requesty, wynik w `przebieg_tomtom.json`):
  - **przeszłość (wt. 13.10 07:30) jest przyjmowana** (HTTP 200, `departureTime` = podana chwila), a `travelTime` = `historic`;
  - przyszłość (wt. 20.10 i 27.10, 07:30): `travelTime` = `historic` = `liveTrafficIncidents`. Ruch bieżący nie wchodzi, **`historic` i `noTraffic` są identyczne dla obu wtorków** (iloraz 1,0000), czyli to typowy profil, a nie predykcja dnia;
  - `now` (niedziela 19:23 CEST): `travelTime` / `historic` = 1,027, czyli tylko tu wchodzi ruch bieżący.
- Cel endpointu: trasa uwzględnia ruch bieżący i „typical road speeds on the requested day of the week and time of day”.
- `computeTravelTimeFor=all`: `noTrafficTravelTimeInSeconds` = czas „as if there are no delays … due to traffic conditions”; `historicTrafficTravelTimeInSeconds` = z „time-dependent historic traffic data”; `liveTrafficIncidentsTravelTimeInSeconds` = z „real-time speed data”; `travelTimeInSeconds` zawiera opóźnienie z ruchu także przy `traffic=false` (historyczny wpływ na prędkości zostaje).
- Wniosek dla projektu: dla przyszłego wtorku miarą „czasu w oknie” jest `historicTrafficTravelTimeInSeconds` (typowy profil dnia tygodnia i godziny). Kolejne wtorki dają ten sam profil, więc **podział przestrzenny** (2/3 analiza, 1/3 walidacja), a nie dniowy. Potwierdzone partią `probe`, więc zestaw dniowy jest zbędny.
- `travelMode=truck`: `vehicleMaxSpeed` (0 = dobrane automatycznie), wymiary i masa (0 = ograniczenie nieuwzględniane), `vehicleCommercial`.
- Geometria: `routes[].legs[].points` (lat, lon), `coordinatePrecision=full` = 7 miejsc.

### TomTom Traffic Flow Segment Data
Źródło: https://docs.tomtom.com/traffic-api/documentation/tomtom-maps/traffic-flow/flow-segment-data

- `point=lat,lon` (WGS84, najpierw szerokość), `unit=kmph` (małe litery, wielkość liter ma znaczenie), `zoom` 0–22 wpływa na widoczne drogi i współrzędne.
- `currentSpeed` / `currentTravelTime`: „fused real-time measurements”, czyli **stan z chwili zapytania**. `freeFlowSpeed`: prędkość „under ideal conditions”. Dodatkowo `confidence` 0–1, `frc` FRC0–6, `coordinates`, `roadClosure`.
- 18.10 to niedziela, więc w tej sesji `currentSpeed` w szczycie dnia roboczego jest niemierzalny. Porównujemy tylko `freeFlowSpeed`. `currentSpeed` z niedzieli nie jest profilem „wtorek 8:00”.

### HERE Routing API v8 i Traffic API v7
Źródła: https://docs.here.com/routing/docs/routing-v8-duration, https://docs.here.com/routing/docs/routing-v8-time-dependent-routing, https://docs.here.com/routing/docs/routing-intro

- `duration` = „all available data sources” (ruch bieżący, wzorce historyczne, prędkości swobodne); `typicalDuration` = „typical for the time of day” (historyczne + swobodne, na żądanie w `return=summary,typicalDuration`); `baseDuration` = „without time-awareness” (tylko swobodne). `baseDuration` może być większe od `duration`.
- `departureTime`: domyślnie czas zapytania; `any` = tryb planowania bez ruchu. O przeszłości i horyzoncie ruchu bieżącego dokumentacja milczy.
- Flow v7: `in=circle:lat,lon;r=…`, `locationReferencing=shape`; `currentFlow.freeFlow`, `speed`, `jamFactor` (0–10), prędkości w **m/s** (HERE SDK: free flow speed „in meters per second”). Stan bieżący.

### Limity i licencja
- TomTom, cennik (https://docs.tomtom.com/pricing, 2026-10-18): Routing API i Traffic Flow Segment Data po „20K monthly” za darmo. Starsze źródła podają 2 500 non-tile dziennie. FAQ: limit QPS 5–50 zależnie od API, bez tabeli. Skrypt: 5 QPS, backoff przy 429, budżet 400.
- HERE: cennik bez aktualnych liczb dla Routing v8 / Traffic v7 (źródła trzecie: ok. 30 tys. transakcji miesięcznie, niepotwierdzone).
- Licencja TomTom: tabela wyżej. Do gita trafiłyby tylko agregaty (wariant A).

## 2. Próbka i zestawy

`pipeline/traffic_providers.py sample` (seed 4711 z `config/kutno.toml`, sha256 powtarzalny w dwóch uruchomieniach):

- **30 par** z planów R6 (run `g5r6_25pct_s4711`, nogi car ≥ 1 km, podróż 1): mieszkańcy `r` 8, przyjeżdżający z linku wjazdu `c` 6, wyjeżdżający do linku wyjazdu `o` 4, tło lekkie `t` 6, ciężkie `h` 6 (truck: 80 km/h, 15 × 2,5 m, komercyjny; ZAŁOŻENIE, masa/wysokość 0). Początek i koniec = koniec linku startowego i docelowego; trasa modelu = linki z `output_experienced_plans`.
- **10 korytarzy** między linkami liczników GPR (`gpr_linki.csv`) i centrum (ZAŁOŻENIE: centroid gminy Kutno, najbliższy link primary/secondary/tertiary): wloty DK92 zach. (91123), DK92 wsch. (91869), DK60 płn. (91878), DK60 płd. (91115), wylot DK92 zach., przejazd 91869 ↔ 91124 w obie strony, A1 71410 ↔ 91821 w obie strony, Krośniewice 91892 → 91119 (kontrola znanej wady). Trasa modelu = najszybsza po czasie swobodnym.
- **25 segmentów** (środek linku, linki ≥ 300 m, jeden na drogę OSM): miasto 6, DK poza miastami 5 (≈ primary, ZAŁOŻENIE), DW poza 4 (≈ secondary), A1 3, tertiary/unclassified poza miastami 7.
- Współrzędne: EPSG:2180 → WGS84 raz, `always_xy` (x = E ≈ 525 000, y = N ≈ 485 000); przykład: link `13478409070011f` (524 608, 484 358) → 52,2247 N, 19,3604 E.

## 3. Przewidywanie (zapisane przed pobraniem, §8)

Freespeed segmentów w próbce (D13: 0,8 × limit PoRD albo tag `maxspeed`): A1 112 km/h (3/3 z tagu 140), DK poza miastami 72 (limit 90), DW poza 40–72 (mediana 56), miasto 40 (5 z 6; jeden residential z tagiem 90 → 72), tertiary/unclassified poza miastami 72 (6 z 7 bez tagu, `default_rural`).

| klasa | przewidywanie dla model / dostawca (`freeFlowSpeed`, `noTraffic`) | uzasadnienie |
|---|---|---|
| tertiary/unclassified poza miastami | **> 1, wyraźnie** (model szybszy, rzędu 1,2–1,8) | 72 km/h bez tagu; ORS dla unclassified 30, tertiary 50 km/h; walidacja GUS i audyt wskazały zawyżenie |
| A1 | **< 1** (model wolniejszy, ok. 0,85–0,95) | 112 km/h = 0,8 × 140; swobodna prędkość na autostradzie zwykle bliżej limitu (do sprawdzenia, nie liczba ze źródła) |
| DK poza miastami | ≈ 1 (0,9–1,1) | 72 km/h przy limicie 90 |
| miasto | ≈ 1 albo lekko > 1 | 40 km/h przy limicie 50; skrzyżowań i sygnalizacji w modelu nie ma (G1 odłożone) |
| trasy dojazdów w oknie | model krótszy od `historic` | brak skrzyżowań, kongestia w R6 mała (3,7% czasu w opóźnieniu w oknie 6–9) |

## 4. Czasy modelu (bez dostawcy)

`pipeline/traffic_metrics.py model` → `model_times.csv` (para × okno: mediana, min i maks. z 5 runów, czas swobodny w sieci, czas ORS na trasie modelu), `model_legs_check.csv`, log `model.log`. Model to uśredniony dzień roboczy, nie data. Czasów nie skalowano przez próbkę.

**Metoda.** Czas modelu w oknie liczy sonda jadąca po trasie modelu, z czasem przejazdu linku równym średniej z eventów pojazdów lekkich, które wjechały na link w danej godzinie (bez przejazdów: floor(L/v) + 1 s, I1). Ciężkie: max(czas lekkich, czas swobodny przy 80 km/h). Dzięki temu ta sama para ma czas w każdym z 5 runów, także w runach z innym seedem planów, gdzie są inne osoby.

**Kontrola sondy:** dla 30 osób z próbki w 3 seedach MATSim porównałem czas sondy przy faktycznym wyjeździe z `trav_time` nogi agenta. Wynik: mediana 1,000, p5–p95 0,90–1,04, n = 90. Najgorsze 0,81 to wyjazd 07:59, tuż przed zmianą godziny przedziału.

| okno (środek) | kongestia: mediana czasu w oknie / czas swobodny | maks. | rozrzut 5 runów (maks. − min.) / mediana: mediana | maks. |
|---|---|---|---|---|
| rano 07:30 | 1,035 | 1,32 (`r6511128_10`, 3 km w mieście) | 1,5% | 14% |
| południe 12:30 | 1,007 | 1,05 | 0,6% | 2,4% |
| popołudnie 15:30 | 1,032 | 1,11 | 1,2% | 17% |

Po rodzaju, rano: mieszkańcy 1,14, wyjeżdżający 1,06, przyjeżdżający 1,05, tło 1,04, korytarze 1,03, ciężkie 1,01. **Czas w oknie różni się od czasu swobodnego o 0–14% (mediany)**. Porównanie „czas w oknie” z TomTom mierzy więc głównie prędkości swobodne sieci (D13), a kongestię w niewielkim stopniu. Różnica model–dostawca w szczycie, której nie ma przy czasie swobodnym, wskazywałaby na brak kongestii albo skrzyżowań (G1) w modelu.

**ORS jako trzecie źródło** (prędkości jak w `g5_gus_czasy.py` wariant `ors`, na trasie modelu; ciężkie ograniczone do 80 km/h): model / ORS mediana 1,12. Mieszkańcy 1,16 (1,10–1,22), korytarze 1,15 (0,91–1,41), wyjeżdżający 1,05, tło 1,02, ciężkie 1,00, przyjeżdżający 0,93 (0,66–1,13). W mieście model jest wolniejszy od ORS (40 km/h z D13 wobec 45 km/h, czyli 0,9 × 50). Na długich trasach zamiejskich z unclassified/tertiary bez tagu jest szybszy (72 wobec 30–50 km/h). Obie wartości ORS to reguły routera, a nie pomiary, więc tylko porządkują przewidywanie.

## 5. Wyniki TomTom (agregaty, `metrics_tomtom.csv`, wykres `g5_czasy_tomtom.png`)

Wszystkie ilorazy to **mediana model / TomTom**. Wartość > 1 oznacza, że model jest wolniejszy (dłuższy czas). Czas modelu w oknie to mediana z 5 runów, w nawiasie zakres dla wariantów min. i maks. z 5 runów. Model to uśredniony dzień roboczy, a TomTom typowy profil wtorku. Obie strony są więc „typowe”, żadna nie jest datą.

### 5.1 Czas swobodny tras (model: sieć D13 na trasie modelu; TomTom `noTrafficTravelTime`)

| zestaw | n | model / TomTom | MAPE | RMSE | ORS / TomTom | długość model / TomTom |
|---|---|---|---|---|---|---|
| analiza | 27 | **1,18** | 20% | 177 s | 1,03 (MAPE 14%) | 1,00 |
| walidacja | 13 | **1,08** | 23% | 141 s | 1,00 (MAPE 26%) | 1,00 |

Po rodzaju (analiza; n małe, grupy rozbite przez wadliwy wskaźnik bufora, §6): przyjeżdżający 1,18 (n 3), korytarze 1,24 (3) i 1,23 (4), tło lekkie 1,20 (1) i 1,18 (3), mieszkańcy 1,05 (2) i 0,91 (3), wyjeżdżający 1,02 (3), **ciężkie 1,00 (4; walidacja 0,97, n 2)**. Ciężkie zgadzają się, bo po obu stronach jest limit 80 km/h (D20 i `vehicleMaxSpeed=80`).

### 5.2 Czas w oknie (model: mediana 5 runów; TomTom `historicTrafficTravelTime` dla `departAt` w tym oknie)

| zestaw | okno | n | model / TomTom (min.–maks. 5 runów) | MAPE | RMSE |
|---|---|---|---|---|---|
| analiza | rano 07:30 | 27 | **1,057** (1,053–1,077) | 17,6% | 164 s |
| analiza | południe 12:30 | 27 | 1,043 (1,039–1,053) | 17,0% | 170 s |
| analiza | popołudnie 15:30 | 27 | 1,059 (1,038–1,108) | 17,3% | 169 s |
| walidacja | rano 07:30 | 13 | **1,023** (1,010–1,041) | 13,3% | 117 s |
| walidacja | południe 12:30 | 13 | 1,003 (0,994–1,004) | 14,4% | 118 s |
| walidacja | popołudnie 15:30 | 13 | 1,006 (0,995–1,009) | 14,7% | 113 s |

„Kongestia” po obu stronach (czas w oknie / czas swobodny, mediana; analiza i walidacja zgodne co do 0,01):

| | południe | rano | popołudnie |
|---|---|---|---|
| model | 1,007 | 1,036 | 1,032 |
| TomTom `historic` / `noTraffic` | 1,077 | 1,088 (walidacja 1,077) | 1,080 (1,086) |

TomTom ma opóźnienie ok. 8% względem `noTraffic` **przez cały dzień**, a w szczycie tylko ok. 1 pp więcej niż w południe. Model ma ok. 1% w południe i 3–4% w szczytach. Przyrost szczytowy jest więc w modelu nawet większy niż u TomTom. Brak kongestii szczytowej w modelu nie wynika z danych. Stałe 8% u TomTom to raczej skrzyżowania, sygnalizacja i manewry, których model nie ma (G1). To interpretacja, nie pomiar.

### 5.3 Prędkość swobodna segmentów (freespeed linku vs `freeFlowSpeed`)

Do metryk weszło 16 z 25 segmentów: punkt odpowiedzi musi leżeć < 50 m od środka linku (§6).

| zestaw | klasa | n | freespeed / TomTom | model [km/h] | TomTom [km/h] (mediana) | MAPE |
|---|---|---|---|---|---|---|
| analiza | wszystkie | 11 | **0,84** | 72 | 86 | 21% |
| analiza | A1 | 2 | 0,86 | 112 | 130 | 14% |
| analiza | DK poza miastami | 3 | 0,81 | 72 | 89 | 19% |
| analiza | DW poza miastami | 3 | 0,84 | 72 | 83 | 26% |
| analiza | miasto | 2 | 0,72 | 40 | 57,5 | 28% |
| analiza | tertiary/unclassified poza | **1** | 1,13 | 72 | 64 | 13% |
| walidacja | wszystkie | 5 | **0,87** | 72 | 83 | 17% |
| walidacja | A1 / DK / DW / miasto | 1 / 2 / 1 / 1 | 0,87 / 0,83 / 0,69 / 0,91 | 112 / 72 / 40 / 40 | 129 / 87 / 58 / 44 | |
| walidacja | tertiary/unclassified poza | 0 | (oba punkty > 50 m albo HTTP 400) | | | |

Analiza i walidacja zgadzają się kierunkiem i rzędem wielkości. **Freespeed modelu jest o 13–19% niższy od `freeFlowSpeed` TomTom na A1, DK i DW**, czyli dokładnie o współczynnik 0,8 z D13: TomTom podaje prędkość swobodną bliską limitowi (A1 129–130 przy 140, DK 87–89 przy 90).

### 5.4 Błędy bezwzględne: MAE i RMSE, kryterium TAG (przebiegi 2 i 3)

Wykres: `g5_czasy_tomtom_bledy.png` (agregaty). Przebiegi 2 i 3 (prośba użytkownika o MAE, wykresy i mapę) dały **identyczne mediany, MAPE i RMSE co przebieg 1**. Profil TomTom jest powtarzalny między zapytaniami.

| zestaw | porównanie | n | RMSE [s] | MAE [s] | w 15% lub 1 min (TAG tab. 3) | w 15% i 1 min (TAG C.3.10) |
|---|---|---|---|---|---|---|
| analiza | czas swobodny | 27 | 177 | 140 | 37% | 22% |
| analiza | rano 07:30 | 27 | 164 | 128 | 48% | 22% |
| analiza | południe 12:30 | 27 | 170 | 129 | 63% | 33% |
| analiza | popołudnie 15:30 | 27 | 169 | 131 | 63% | 30% |
| walidacja | czas swobodny | 13 | 141 | 112 | 54% | 31% |
| walidacja | rano 07:30 | 13 | 117 | 93 | 77% | 38% |
| walidacja | południe 12:30 | 13 | 118 | 94 | 62% | 31% |
| walidacja | popołudnie 15:30 | 13 | 113 | 92 | 62% | 31% |

Średnia długość tras to ok. 20 min, więc MAE 1,5–2,3 min to ok. 13–18% (zgodnie z MAPE).

| zestaw | klasa (n) | MAE [km/h] | RMSE [km/h] |
|---|---|---|---|
| analiza | wszystkie (11) | 17,5 | 19,3 |
| analiza | A1 (2) / DK (3) / DW (3) / miasto (2) / tert-uncl (1) | 18 / 17 / 21 / 18 / 8 | 18 / 17 / 24 / 20 / 8 |
| walidacja | wszystkie (5) | 13,8 | 14,9 |
| walidacja | A1 (1) / DK (2) / DW (1) / miasto (1) | 17 / 15 / 18 / 4 | 17 / 16 / 18 / 4 |

### 5.5 Rozrzut prędkości (symulowana vs TomTom, prosta MNK)

Wykres per obiekt jest w `output/g5_czasy_tomtom/rozrzut_predkosci_tomtom.png`, poza repo (wartości TomTom per obiekt, D22). Do raportu trafiają tylko parametry prostej (wszystkie punkty w metrykach, analiza + walidacja):

| panel | n | prosta (y = TomTom, x = model) | R² |
|---|---|---|---|
| segmenty: freespeed vs `freeFlowSpeed` | 16 | y = 0,972x + 17,26 | 0,863 |
| trasy: prędkość swobodna (długość / czas) | 40 | y = 1,125x − 1,32 | 0,755 |
| trasy: prędkość rano 07:30 vs `historic` | 40 | y = 1,235x − 9,46 | 0,834 |

Segmenty: nachylenie bliskie 1 z przesunięciem +17 km/h, czyli TomTom jest stale szybszy o kilkanaście km/h niezależnie od klasy drogi. To zgodne z factorem 0,8. Na trasach rano punkty leżą blisko y = x do ok. 80 km/h. Nachylenie 1,24 ciągną A1 (TomTom ok. 130, model ok. 107) i kilka tras mieszkańców w mieście.

**Mapa próbki z odczytami** (`output/g5_czasy_tomtom/mapa_tomtom.png`, poza repo): trasy pokolorowane ilorazem czasu rano, segmenty z etykietą „model / TomTom km/h”, segmenty wyłączone (> 50 m) jako x. Wnioski z mapy:
- najwyżej (model wolniejszy) leżą korytarze A1 (1,21–1,24), przejazd Objazdowa → Sklęczkowska (1,24) i DK92 zach. (1,12–1,16): to drogi, na których freespeed jest najdalej od `freeFlowSpeed`;
- trasy mieszkańców w mieście mają największy rozrzut, od 0,62 do 1,63 (krótkie trasy 3–15 min, więc 1–3 min różnicy daje duży iloraz);
- ciężkie i wyjeżdżający są blisko 1 (0,78–1,15);
- Krośniewice (nr 40): 3,0 wobec 1,5 min, czyli 2,0. To korytarz kontrolny znanej wady; przyczyny na tej trasie nie sprawdzałem.

### 5.6 Literatura: jakie wartości są akceptowalne

- **TAG Unit M3.1 Highway Assignment Modelling** (DfT, maj 2026, `data/raw/g5/lit/tag_m3_1_highway_assignment_modelling.pdf`, manifest):
  - **tab. 3 (§3.3.15)**: czas modelu w trasie w 15% czasu pomierzonego (albo 1 min, jeśli to więcej) dla > 85% tras. Mierzy się procent różnicy z limitem bezwzględnym, a nie RMSE ani MAE;
  - **aneks C.3.10** (mikrosymulacja): 15% **i** 60 s jednocześnie;
  - **tab. 2**: GEH < 5 dla > 85% natężeń. To miara natężeń, dla czasów nie ma zastosowania.
- **Progów RMSE ani MAE dla czasów przejazdu nie znalazłem w źródle pierwotnym.** Wytyczne (TAG, FHWA Travel Model Validation Manual 2010) używają RMSE głównie dla natężeń (%RMSE po klasach natężenia). Liczb dla FHWA nie podaję, bo nie zweryfikowałem tekstu.
- **Ocena R6 według TAG tab. 3:** rano 48% (analiza) i 77% (walidacja) tras w kryterium, w ruchu swobodnym 37% / 54%. **Wytyczna > 85% nie jest spełniona.** Zastrzeżenia:
  - TAG porównuje z czasem **pomierzonym** (badania przejazdów), a TomTom `historic` to model dostawcy;
  - TAG dotyczy modeli strategicznych z kalibracją prędkości i przepustowości, a R6 tych nie kalibrował;
  - n jest małe (27 / 13).

## 6. Kontrole (§8)

| kontrola | wynik |
|---|---|
| liczba requestów = dry-run | 149 = 149 w każdym z 3 przebiegów ✔ (plus 149 nieudanych 401 i 18 testowych, łącznie 614 ≤ 650) |
| klucz | brak w logu i plikach (asercja w kodzie; `fetch_tomtom.log` ma `key=%2A%2A%2A` (*** zakodowane w URL) we wszystkich 316 liniach; sprawdzone skryptem, że klucz nie występuje w żadnym pliku raportu ani kodu) ✔ |
| początek i koniec trasy TomTom vs punkt zapytania | maks. 5,9 m / 3,4 m, 0 tras > 50 m ✔ |
| kolejność osi | ✔ (jak wyżej; po zamianie osi odległości byłyby rzędu setek km) |
| jednostki | `freeFlowSpeed` 44–130 km/h (`unit=kmph`), czasy w s; czas TomTom / model 0,42–1,51 ✔ |
| id agentów i nóg z planami R6 | wszystkie osoby z par są w `plans_g5r6_25pct_{meta,tlo,ciezkie}.csv` ✔; sonda vs noga agenta: mediana 1,000 (§4) ✔ |
| **segment < 50 m od środka linku** | **8 z 24 segmentów > 50 m (maks. 1 254 m), 1 × HTTP 400.** 5 z 7 to tertiary/unclassified poza miastami, 3 to miasto. Wyłączone z metryk |
| **zgodność tras (bufor 25 m)** | **wskaźnik niewiarygodny.** Mediana 0,56, 26 z 40 tras < 70%, w tym A1 (K_a1_ns, K_a1_sn). Przyczyna: geometria linku w sieci MATSim to prosta między węzłami (wszystkie 10 383 linki mają 2 punkty, linki A1 mają do 6,7 km, unclassified mediana 565 m), więc trasa TomTom po rzeczywistej drodze wychodzi poza 25 m na łukach. Zastępczo: **długość trasy model / TomTom = 1,00** (analiza i walidacja), czyli trasy są tej samej długości |
| niezależna kontrola mediany i MAPE (`check_niezalezny.py`: osobny proces, nie importuje `pipeline/`, czyta pliki modelu sam, wartości TomTom przez stdin) | zgodna co do 1e-9 dla wszystkich grup „wszystkie” (swobodny, 3 okna, segmenty, oba zestawy) ✔ |
| selftest metryk na syntetycznym dostawcy | ok (`traffic_metrics.py selftest`) ✔. Nie wykrył problemu bufora, bo syntetyczna trasa miała tę samą prostą geometrię (`ERRORS.md`) |

## 7. Przewidywanie vs wynik

| klasa | przewidywanie (§3) | wynik | ocena |
|---|---|---|---|
| tertiary/unclassified poza miastami | model szybszy (1,2–1,8) | 1,13, ale **n = 1** (6 z 7 segmentów odpadło w kontroli 50 m) | kierunek zgodny, **brak podstaw do liczby**. Flow TomTom nie jest dobrym pomiarem tej klasy przy prostych linkach |
| A1 | model wolniejszy (0,85–0,95) | 0,86–0,87 | zgodne |
| DK poza miastami | ≈ 1 | 0,81–0,83 | **niezgodne.** Zakładałem, że prędkość swobodna DK jest niższa od limitu; TomTom daje 87–89 km/h przy limicie 90 |
| miasto | ≈ 1 lub > 1 | 0,72 / 0,91 (n 2 / 1) | niezgodne kierunkiem, ale n bardzo małe |
| trasy w oknie | model krótszy od `historic` | model dłuższy o 2–6% | **niezgodne.** Wolniejszy freespeed (0,8 × limit) z nawiązką rekompensuje brak opóźnień na skrzyżowaniach |

Rozbieżności mają jedno źródło. Współczynnik 0,8 z D13 obniża prędkość swobodną poniżej `freeFlowSpeed` TomTom o ok. 15%. Jednocześnie TomTom w „typowym” czasie dolicza ok. 8% opóźnień, których model nie ma. Efekty znoszą się na poziomie tras: w oknach model / TomTom wynosi 1,00–1,06.

## 8. Ograniczenia

- **TomTom `historic` to model dostawcy** (typowy profil), a nie pomiar konkretnego dnia. Wtorek 20.10 i 27.10 dały identyczne czasy.
- `currentSpeed` w szczycie dnia roboczego nie został zmierzony (zapytania w niedzielę). Model i TomTom są porównane tylko jako „typowe”.
- Próbka mała: 27 + 13 par i korytarzy, 11 + 5 segmentów. Klasa tertiary/unclassified poza miastami, wskazana w audycie, jest praktycznie niezmierzona przez Flow (n = 1). Na trasach jest wymieszana z innymi klasami.
- Podział na grupy po rodzaju w `metrics_tomtom.csv` przechodzi przez wadliwy próg bufora 70% (np. `c` i `c_trasa<70%`). Mediany per rodzaj bez tego podziału nie da się już policzyć, bo odpowiedzi nie były przechowywane (wariant A). Każdy ponowny przebieg kosztuje 149 requestów.
- **Różnica analiza vs walidacja** (swobodny 1,18 vs 1,08, okno rano 1,06 vs 1,02) jest tego samego rzędu co odchylenia czasów w oknie od 1. Różnice model–TomTom w oknach poniżej ok. 5% **nie są wynikiem**. Rozrzut 5 runów to 1–7 pp, a rozrzut seedów planów dla natężeń 9–12% na odcinek (`g5_r6_ref.md`).
- TomTom vs HERE (§7.4) nie zostało zrobione (regulamin TomTom 11.6.10, D22). Niepewności samego „pomiaru” nie znamy.

## 9. Propozycja do decyzji (bez zmian plików)

1. **Freespeed (D13) nie zmieniać na podstawie samego `freeFlowSpeed`.** Na A1, DK i DW model jest o 13–19% wolniejszy od prędkości swobodnej TomTom (zgodnie w analizie i walidacji), czyli dokładnie o factor 0,8. Ale podniesienie freespeed do poziomu TomTom bez dodania opóźnień na skrzyżowaniach skróciłoby czasy w oknach o ok. 8–15% poniżej `historic`. Dziś czasy w oknach zgadzają się na 0–6%. Factor 0,8 działa więc jak zastępczy narzut skrzyżowań. Opcja do rozważenia razem z G1 (skrzyżowania): freespeed bliżej `freeFlowSpeed` + jawne opóźnienia węzłów zamiast 0,8.
2. **Tertiary/unclassified poza miastami (72 km/h):** TomTom tego nie rozstrzyga (n = 1, kierunek zgodny z GUS i ORS). Do sprawdzenia innym pomiarem, np. Routing TomTom na krótkich trasach wybranych tak, żeby ≥ 70% długości leżało na tych klasach. Wymagałoby to nowej próbki i decyzji.
3. **Capacity: nie ruszać.** Warunek z promptu nie jest spełniony. Czas w szczycie zgadza się tak samo jak w południe, a przyrost szczytowy w modelu (+3 pp) nie jest mniejszy niż u TomTom (+1 pp). Nie ma śladu brakującej kongestii, który dałoby się oddzielić od znanych wad popytu (§1 promptu).
4. Jeśli walidacja ma być powtarzana: **geometria linków z OSM** (shape w sieci albo map-matching do `origid`), bo bez niej wskaźnik zgodności tras i kontrola segmentów są słabe. Do tego decyzja, czy regulamin pozwala na ponowne zapytania (wariant A: tylko agregaty).
5. Każde wdrożenie wymaga wpisu w `DECISIONS.md` i testu 2 iteracji na MATSim 2026 (CLAUDE.md, pkt 9).

## 10. Odtworzenie i HERE

- `uv run python pipeline/traffic_providers.py sample` (deterministyczne, sha256 powtarzalny), `uv run python pipeline/traffic_metrics.py model`, `uv run python pipeline/traffic_metrics.py selftest`, `uv run python pipeline/traffic_providers.py run tomtom [--dry-run|--test]`. `run` liczy wszystko w jednym procesie i zapisuje tylko agregaty. Przerywa przy pierwszym 401/403. Log: `fetch_tomtom.log` (bez klucza i treści), `przebieg_tomtom.log`.
- **HERE: przygotowane, niepobrane.** Brak `HERE_API_KEY`. `run here --dry-run` = 149 requestów (Routing v8 `return=summary,polyline,typicalDuration`, truck `vehicle[speedCap]`; Flow v7 `circle` r = 30 m, prędkości m/s → km/h). Przed użyciem trzeba sprawdzić aktualne warunki HERE: AUP pkt 4 ogranicza „benchmarking” i „storing”. Bez zestawiania z TomTom (D22).
