# D23: współczynnik prędkości per grupa dróg (miasto / poza miastem), kalibracja na zestawie analizy: plan

Data: 2026-10-18. Decyzja użytkownika: wariant (a) z `reports/etap2/g5_czasy_tomtom/wnioski_i_dalej.md` §3.1. Ten dokument to plan, nic jeszcze nie jest wdrożone.

## 1. Co zmieniamy

Dziś (D13): `freespeed = limit × 0,8` dla każdego linku. Limit pochodzi z tagu `maxspeed` albo z limitu ustawowego wg typu drogi i położenia.

Po D23: **`freespeed = limit × f_g`**, gdzie `f_g` to współczynnik grupy dróg `g`. Limit liczony jak w D13. Współczynniki dobieramy na zestawie analizy (TomTom), a sprawdzamy raz na zestawie walidacji.

Grupy (typ OSM bez `_link`; miasto = `towns.wkt`, czyli miasta z BREC razem z Kutnem, jak w D13):

| grupa | definicja | km w sieci | km w trasach: analiza / walidacja | tras z ≥ 1 km: analiza / walidacja |
|---|---|---|---|---|
| A autostrada | motorway | 95 | 193 / 125 | 8 / 6 |
| B DK/DW poza miastem | trunk, primary, secondary poza miastem | 288 | 137 / 66 | 18 / 8 |
| C lokalne poza miastem | tertiary, unclassified poza miastem | **2 858** | 77 / 40 | 9 / 5 |
| D osiedlowe poza miastem | residential, living_street poza miastem (wsie) | 820 | **1 / 2** | **0 / 1** |
| E główne w mieście | trunk, primary, secondary, tertiary w mieście | 123 | 76 / 26 | 21 / 9 |
| F lokalne w mieście | residential, unclassified, living_street w mieście | 313 | **24 / 10** | **10 / 3** |

Zawrotki graniczne (`boundary_turnaround`) zostają bez zmian (30 km/h, D13/F2).

**Wniosek z tabeli:** obecna próbka (40 tras) identyfikuje tylko A, B i E. Grupy C i F są słabo pokryte, a D nie ma wcale. Grupa C to 65% sieci i grupa wskazana w audycie, więc **bez rozszerzenia próbki kalibracja nie ma sensu**.

## 2. Kroki

### Krok 1. Rozszerzenie próbki (przed jakimkolwiek dopasowaniem)
- Nowe trasy losowane z seeda (`config/kutno.toml`), tak żeby każda grupa A–F miała **≥ 12 tras w analizie i ≥ 6 w walidacji**, w których ta grupa stanowi ≥ 50% długości.
- Długość tras 3–15 km (TAG M3.1 §4.3.3). Wyjątek: grupy D i F, gdzie trasy z przewagą tych ulic są krótsze, minimum 2 km.
- Losowanie z par link → link na sieci R6. Trasa modelu = najszybsza po czasie swobodnym, jak przy korytarzach.
- Szacunek: ok. 60 nowych tras.
- Stare 40 tras zostaje z dotychczasowym przydziałem do zestawów. Nowe dostają przydział 2/3 do analizy i 1/3 do walidacji, warstwowo po grupie. **Zapis `split.csv` przed pierwszym requestem.**
- Kontrole jak w D22: punkty < 50 m od linku, osie, jednostki.

### Krok 2. Dopasowanie współczynników (w pamięci, wariant A z D22)
- Model czasu trasy w oknie `w` (bez nowych runów MATSim):

  `T_r,w(f) = Σ_g Σ_{l∈r,g} [ L_l / (limit_l · f_g) + 1 s ] + Δ_r,w`

  - pierwsza część: czas przejazdu linków grupy przy prędkości `limit × f_g` (+1 s za każdy link, reguła QSim z I1);
  - `Δ_r,w`: opóźnienie z kongestii z R6 (mediana 5 runów; dziś 1–4% czasu tras). ZAŁOŻENIE: zmiana prędkości nie zmienia kongestii; sprawdzone w kroku 3.
- Cel: TomTom `historicTrafficTravelTimeInSeconds` dla wtorku 07:30, 12:30 i 15:30 (typowy profil).
- Kryterium: minimum `Σ_r,w (ln T_r,w(f) − ln T_TomTom_r,w)²`, czyli błąd względny, zgodnie z preferencją raportowania w % (MAPE, RMSPE).
- Ograniczenia: `f_g ∈ [0,5; 1,1]`.
- Niepewność: bootstrap po trasach (1 000 losowań). Do raportu idą `f_g`, przedział 90% i liczba tras na grupę.
- Grupa z < 12 trasami w analizie albo z przedziałem szerszym niż ±0,1 dostaje **0,8 (jak dziś) z adnotacją „nieidentyfikowalne”**, a nie wartość z dopasowania.
- Narzędzie: `pipeline/traffic_providers.py run tomtom --fit` (nowy tryb). Pobranie, dopasowanie i bootstrap w jednym procesie. Na dysk tylko `f_g`, przedziały, n i metryki dopasowania. Wcześniej `selftest`: syntetyczny dostawca ze znanymi `f_g` musi je odtworzyć (też z szumem).

### Krok 3. Sieć i runy
- `CreateKutnoNetwork.setSpeed` czyta `factor.<grupa>` z `config/network.properties`, z fallbackiem na `factor`. Link dostaje atrybut `speed_group`. Grupy liczone w Javie tą samą geometrią miast co D13.
- Kontrola sieci:
  - te same id linków i węzłów co w R6 (plany przypinają aktywności do linków);
  - różnica tylko w `freespeed`;
  - `validate_network.py`.
- Test regresyjny smoke (`check_events.py --expect-car-legs 20`). **Test 2 iteracji na MATSim 2026** (CLAUDE.md pkt 9).
- Runy 25% × 5: 3 seedy MATSim i 2 seedy planów, jak R6. **Te same plany i macierze co R6.** Szacunek: ok. 25 min równolegle (R6: 23 min). Nazwa: R7.

### Krok 4. Sprawdzenie, czy nie zepsuliśmy natężeń (GPR)
- Zmiana prędkości zmienia wybór tras, więc zmienia natężenia, do których kalibrowany był popyt (D19–D21).
- Porównanie R7 z R6 na 15 odcinkach GPR: mediana z 5 runów, z rozrzutem seedów planów.
- Jeśli któraś klasa (A1, DK w Kutnie, DK pozostałe, DW) zmieni się bardziej niż rozrzut seedów planów (9–12% na odcinek, ok. 20 pp dla miasta i DW), robimy nową estymację O-D (R7b). Estymacja korzysta z czasów sieci. To osobna decyzja.

### Krok 5. Walidacja (jeden raz)
- `traffic_metrics.py model` na runach R7, potem `run tomtom` na wszystkich trasach.
- Trasy modelu liczone z runów R7 (zmiana z `wnioski_i_dalej.md` §5 pkt 3a), nie z `pairs.csv` R6.
- Raport R7 vs R6, osobno dla analizy i walidacji, per grupa: iloraz, MAPE, RMSPE, %RMSE, MAE i RMSE, kryterium TAG. Do tego wykres rozrzutu, mapa (w `output/`) i porównanie z GPR.
- **Zestaw walidacji ocenia wynik i niczego nie zmienia.** Jeśli wynik jest zły, wracamy do kroku 2 tylko z nową decyzją, a walidacja traci niezależność. Trzeba to zapisać w raporcie.

## 3. Budżet i czas

| krok | requesty TomTom | czas |
|---|---|---|
| 1 (test + pobranie kontrolne nowych tras) | ok. 200 | 5 min |
| 2 (dopasowanie: trasy analizy × 3 okna, tylko Routing) | ok. 200 | 5 min + bootstrap |
| 5 (walidacja: wszystkie trasy × 3 okna + segmenty) | ok. 330 | 5 min |
| **razem** | **ok. 750** (dotąd 763, nowy `BUDGET` ok. 1 600) | |

Darmowy próg TomTom: 20 tys. miesięcznie na API (cennik z 2026-10-18). Runy MATSim: smoke, 2 iteracje, 5 × 25% (ok. 25 min), ewentualnie R7b.

## 4. Ryzyka i ZAŁOŻENIA

1. **TomTom `historic` jako cel kalibracji** (typowy profil dostawcy, nie pomiar). Model nauczy się prędkości TomToma, a nie rzeczywistych. ZAŁOŻENIE świadome, bo innego źródła czasów nie mamy.
2. **`Δ` z R6 stałe w kroku 2.** Przy kongestii 1–4% błąd jest mały. Sprawdzamy go w kroku 5: R7 vs przewidywanie z kroku 2.
3. **Wspólny `f_g` dla tagowanych i nietagowanych linków grupy.** Tag 50 km/h w wiosce na DK i limit 90 poza nią dostają ten sam współczynnik. Wariant do rozważenia po kroku 2: osobny `f` dla `speed_source = default_*` w grupie C.
4. **Proste linki (2 punkty):** zgodność tras nadal niewiarygodna. Kontrola zastępcza: stosunek długości tras (dziś 1,00).
5. **Dopasowanie pochłania błędy niezwiązane z prędkością** (skrzyżowania, wybór trasy). `f` w mieście będzie niższe, bo zawiera opóźnienia węzłów. Zgodne z TAG §5.2.3 (cruise speeds), ale do G1 trzeba to rozdzielić.
6. **Grupa D bez danych:** jeśli krok 1 nie znajdzie 12 tras z przewagą ulic osiedlowych na wsiach, zostaje 0,8.

## 5. Do decyzji przed startem

1. Podział na 6 grup (A–F) i progi identyfikowalności (≥ 12 tras, przedział ±0,1).
2. Cel: TomTom `historic` 3 okna, kryterium logarytmiczne (błąd względny).
3. Budżet requestów ok. 1 600 łącznie (`BUDGET`).
4. Czy przy zmianie GPR większej niż rozrzut (krok 4) robimy R7b od razu, czy wracamy do decyzji.
