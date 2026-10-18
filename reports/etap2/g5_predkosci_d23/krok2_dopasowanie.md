# D23 krok 2: dopasowanie współczynników prędkości f_g (zestaw analizy, TomTom)

Data: 2026-10-18. Plan: [plan.md](plan.md) §2. Próbka: [krok1_probka.md](krok1_probka.md). Model R6 nie był zmieniany.

## Na górze

| | |
|---|---|
| dane | TomTom Routing `historicTrafficTravelTimeInSeconds`, wtorek 2026-10-20, 07:30 / 12:30 / 15:30 (typowy profil); **tylko zestaw analizy** (76 tras × 3 okna) |
| wysłane | 2026-10-18 (niedziela wieczorem), `fit_tomtom.json` |
| requesty | 3 (`--test`) + 228 = 231. Łącznie od początku 994 (limit 1 400, dziś poniżej 2 000 na dobę) |
| obserwacje w dopasowaniu | 222 (74 trasy). 2 trasy wyłączone: start TomTom > 50 m od punktu zapytania (D23C_13: 307 m, D23D_12) |
| model | czas swobodny trasy = Σ L / min(limit × f_g, cap) + 0,5 s na link + kongestia R6 (mediana 5 runów, stała). Ciężkie cap 80 km/h |
| kryterium | min Σ (ln model − ln TomTom)², f_g ∈ [0,5; 1,1], bootstrap 1 000 po trasach |
| narzędzia | `traffic_metrics.py selftest_fit` (syntetyczne f_g odtworzone, błąd maks. 0,015); `traffic_providers.py run tomtom --fit` (dane tylko w pamięci, D22) |
| wyniki | `fit_f_g_tomtom.csv`, `fit_tomtom.json`, `metrics_r6_analiza_tomtom.csv`, wykres `fit_f_g_tomtom.png` |

## Wynik

| grupa | f dopasowane | przedział 90% | trasy z przewagą | km w trasach | reguła z planu | f_final wg reguły |
|---|---|---|---|---|---|---|
| A autostrada | **0,92** | 0,82–1,01 | 12 | 238 | identyfikowalna | 0,92 |
| B DK/DW poza miastem | **1,02** | 0,94–1,10 | 12 | 210 | identyfikowalna | 1,02 |
| C tertiary/unclassified poza miastem | **0,58** | 0,50–0,65 | **11** | 189 | **nie (< 12 tras)** | 0,80 |
| D osiedlowe poza miastem | 0,77 | 0,61–0,95 | 11 | 37 | nie (< 12 tras, przedział ±0,17) | 0,80 |
| E główne w mieście | 0,88 | 0,73–1,06 | 12 | 119 | nie (przedział ±0,17) | 0,80 |
| F lokalne w mieście | **0,50** | 0,50–0,55 | 12 | 55 | identyfikowalna, **ale na dolnej granicy** | 0,50 |

Dopasowanie w próbie (zestaw analizy, przewidywanie bez nowego runu MATSim):

| | MAPE | RMSPE | mediana model / TomTom | trasy w kryterium TAG (15% lub 1 min) |
|---|---|---|---|---|
| R6 (f = 0,8) | 18,5% | 24,9% | 0,97 | 52% |
| wszystkie f dopasowane | 13,6% | 20,3% | 1,00 | 72% |
| f_final wg reguły | 15,1% | 21,7% | 0,96 | 65% |

## Interpretacja

1. **C (tertiary/unclassified poza miastami, 65% km sieci): f ≈ 0,58, czyli ok. 52 km/h przy limicie 90.** To najmocniejszy sygnał. Model jest dziś na tych drogach o ok. 40% za szybki (72 wobec ok. 52 km/h). Zgadza się kierunkiem z audytem, z walidacją GUS i z ORS (30–50 km/h). Reguła z planu odrzuca tę grupę tylko dlatego, że po kontroli 50 m zostało 11 tras zamiast 12. Przedział (±0,075) mieści się w progu ±0,1.
2. **B (DK/DW poza miastem): f ≈ 1,02, czyli ok. 92 km/h przy limicie 90.** Prędkość powyżej limitu zgadza się z `freeFlowSpeed` TomTom (87–92 km/h na segmentach DK). W modelu oznacza to, że DK/DW poza miastem nie mają dziś żadnego narzutu.
3. **A (autostrada): f ≈ 0,92, czyli ok. 129 km/h**, zgodnie z `freeFlowSpeed` TomTom (129–130).
4. **F (lokalne w mieście): f na dolnej granicy 0,5 (≤ 25 km/h przy limicie 50).** Prawdziwe minimum leży poniżej przedziału. Najpewniej współczynnik pochłania opóźnienia skrzyżowań i manewrów na krótkich trasach (2–4 km). Model bez G1 nie ma innego miejsca na ten czas. To ryzyko z planu (§4 pkt 5).
5. **D i E: nieidentyfikowalne** (przedziały ±0,17). Zostają 0,8.
6. **Dopasowanie poprawia błąd w próbie umiarkowanie** (MAPE z 18,5 do 13,6%). Duża część różnic między trasami nie wynika z prędkości grup, tylko ze skrzyżowań, wyboru trasy i samego TomToma. RMSPE 20% zostaje.
7. **To przewidywanie przy stałej kongestii R6.** Prawdziwy efekt pokażą runy R7 (krok 3) i walidacja (krok 5). Zmiana prędkości zmieni wybór tras: szybsze DK, wolniejsze drogi lokalne, więc ruch przejdzie z dróg lokalnych na DK. To dotyczy też natężeń GPR (krok 4).

## Do decyzji przed krokiem 3

Reguły z planu dają f_final = (A 0,92; B 1,02; C 0,80; D 0,80; E 0,80; F 0,50). Trzy punkty wymagają decyzji:

1. **C:** zostawić regułę (0,8, bo 11 tras) czy przyjąć 0,58? Przyjęcie to wyjątek od reguły ustalonej przed dopasowaniem, a walidacja go oceni. Trzecia opcja: dobrać brakujące trasy C (ok. 3–6 requestów na trasę) i powtórzyć dopasowanie. Kosztuje to nowe dopasowanie (ok. 230 requestów, można jutro).
2. **F na granicy 0,5:** przyjąć 0,5 (25 km/h na ulicach osiedlowych miasta, w praktyce opóźnienia skrzyżowań w prędkości) czy zostawić 0,8 do czasu G1?
3. **B > 1** (prędkość powyżej limitu): przyjąć 1,02 czy obciąć do 1,0?
