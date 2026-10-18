# D23 krok 1: rozszerzenie próbki tras per grupa dróg

Data: 2026-10-18. Plan: [plan.md](plan.md). Bez requestów do TomTom: kontrole geometrii (punkty < 50 m, osie) zostały przeniesione do przebiegu kroku 2, bo trzeba oszczędzać budżet (limit konta: 2 500 non-tile na dobę).

## Co zrobione

- `uv run python pipeline/traffic_providers.py sample_d23` (seed 4711 + 23, ok. 24 s).
  - Trasa = najszybsza po czasie swobodnym w sieci R6.
  - Akceptowana, gdy dana grupa ma ≥ 50% długości, a długość wynosi 3–15 km (dla D i F od 2 km).
  - Końce bez motorway, trunk, łącznic i zawrotek. Jedna trasa na link startowy.
- **74 nowe trasy** dopisane do `reports/etap2/g5_czasy_tomtom/pairs.csv` (id `D23<grupa>_NN`, `kind = D23_<grupa>`).
- Przydział do zestawów w `split.csv` dopisany **przed pierwszym requestem**: najpierw uzupełnia brak w walidacji (do 6), resztę daje analizie.
- Stare 40 tras i ich przydział bez zmian (`cmp` z kopią sprzed zmiany).
- Grupy: `speed_groups()` w `traffic_providers.py`, czyli typ OSM bez `_link` i środek linku w `towns.wkt` (miasta BREC razem z Kutnem, tak jak w D13).
- Czasy modelu R6 dla wszystkich 114 tras: `traffic_metrics.py model` → `model_times.csv` (342 wiersze = 114 tras × 3 okna). Kontrola sondy bez zmian: mediana 1,000.

## Pokrycie po rozszerzeniu (trasy z ≥ 50% długości w grupie)

| grupa | analiza | walidacja | km grupy w trasach: analiza / walidacja |
|---|---|---|---|
| A autostrada | 12 | 6 | 238 / 136 |
| B DK/DW poza miastem | 12 | 6 | 211 / 107 |
| C tertiary/unclassified poza miastem | 12 | 6 | 202 / 80 |
| D osiedlowe poza miastem | 12 | 6 | 41 / 27 |
| E główne w mieście | 12 | 6 | 119 / 54 |
| F lokalne w mieście | 12 | 6 | 55 / 25 |
| bez przewagi jednej grupy | 4 | 2 | |
| **razem** | **76** | **38** | |

Próg identyfikowalności z planu (≥ 12 tras w analizie) jest teraz osiągalny dla wszystkich grup. To, czy przedział `f_g` będzie węższy niż ±0,1, pokaże dopiero bootstrap w kroku 2. Grupy D i F mają mało kilometrów (trasy 2–5 km), więc przedziały mogą być szersze.

Długości nowych tras (min–mediana–maks., km): A 11,3–13,8–14,7; B 3,7–10,5–14,3; C 4,2–10,0–13,2; D 2,2–4,9–14,2; E 3,1–3,4–6,0; F 2,3–3,3–4,4.

## Budżet requestów (zmniejszony po informacji o limicie dziennym)

- Limit konta TomTom według użytkownika: **2 500 non-tile na dobę**. Cennik z 2026-10-18 podawał 20 tys. miesięcznie, ale informacja o koncie ma pierwszeństwo.
- W skrypcie są dwa twarde limity:
  - `BUDGET_DAY = 2000` na dobę UTC, liczone z logu;
  - `BUDGET = 1400` łącznie.
- Zużyte do D22: 763.

| krok | requesty |
|---|---|
| 1 (ten) | **0** |
| 2: dopasowanie, 76 tras analizy × 3 okna, tylko Routing, z kontrolami geometrii; przed nim `--test` | ok. 230 + 9 |
| 5: walidacja, 114 tras × 3 okna + 25 segmentów + probe | ok. 370 + 9 |
| **razem D23** | **ok. 620** (plan pierwotny: ok. 750) |

Kroki 2 i 5 mieszczą się nawet w jednej dobie (763 + 620 < 2 000), ale i tak będą w osobnych przebiegach, bo między nimi są runy MATSim.

## Dalej (krok 2)

Tryb `run tomtom --fit` (dopasowanie `f_g` w pamięci, bootstrap, kontrole geometrii nowych tras), najpierw selftest na syntetycznym dostawcy ze znanymi `f_g`.
