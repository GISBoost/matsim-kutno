# D23 kroki 3–4: sieć R7 i natężenia R7 vs R6

Data: 2026-10-21. Plan: [plan.md](plan.md). Dopasowanie: [krok2_dopasowanie.md](krok2_dopasowanie.md).

## Przyjęte f_g (decyzja użytkownika 2026-10-21, „na dziś, potem pewnie się zmieni”)

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| 0,95 | 1,00 | 0,60 | 0,70 | 0,85 | 0,55 |

Wartości odbiegają od reguły z planu (D 0,70 zamiast 0,80, E 0,85 zamiast 0,80, B obcięte do 1,0). Zapisane w `config/network.properties` (`factor.<grupa>`; grupa bez wpisu, np. „inne”, dostaje `factor`=0,8; takich linków w sieci nie ma). Zawrotki graniczne bez zmian (30 km/h).

## Krok 3: sieć i testy

| test | wynik |
|---|---|
| `CreateKutnoNetwork.setSpeed`, atrybut `speed_group`, grupy jak `speed_groups()` w Pythonie | build ok (`build_r7.log`) |
| sieć R7 `scenarios/kutno/network_d23.xml.gz` vs R6 (`check_network_r7.py`) | **te same 4 534 węzły i 10 383 linki, brak różnic w atrybutach poza `freespeed`**; stosunek freespeed R7/R6 równy f/0,8 w każdej grupie (A 143 linki, B 1 035, C 4 264, D 1 617, E 977, F 2 345, zawrotki 2) |
| `validate_network.py` | ok (`validate_network_r7.json`; wynik raportu F2 w repo nie został nadpisany) |
| smoke + `check_events.py --expect-car-legs 20` | ok, 0 stuck (`smoke_r7_check.log`) |
| test 2 iteracji na sieci R7 (`config_25pct_r7.xml`, 59 s) | ok, 29 660 nóg car (jak R6), 0 stuck |
| R7: 5 runów 25% × 100 iteracji (ustawienia jak R6: 2 wątki, 3 GB, równolegle; ok. 22 min) | `check_events.py --expect-car-legs`: 5/5 ok, 0 stuck; nogi 29 660 ×3, 31 768, 29 357 jak w R6 |
| przepełnione linki (`queues.py`, `overfilled_links_gt2x`) | 0 / 1 / 1 / 0 / 1 (maks. obłożenie 5–7 pojazdów na linku, R6: 0) |
| opóźnienie dobowe, poj.-h próbki | R7 292–311 (seedy MATSim 4711/1/2: 299,7 / 292,2 / 311,0), plany p1 374,4, p2 306,5; R6: 239–243, p1 298, p2 248 (wzrost o ok. 25%) |

Runy: `output/g5r7_25pct_s{4711,1,2}`, `output/g5r7p{1,2}_25pct_s4711` (poza gitem). Logi i tabele: `r7/`. Skrypt: `run_r7.sh`.

## Krok 4: R7 vs R6 na odcinkach GPR (mediana z 5 runów; próg = rozrzut seedów planów R6 na odcinku)

Model / GPR, mediana (min–maks z 5 runów), obie klasy z `g5_baseline.py`:

| klasa | lekkie R6 | lekkie R7 | ciężkie R6 | ciężkie R7 |
|---|---|---|---|---|
| A1 (3 odc.) | 99% | **99%** | 101% | **98%** |
| DK w Kutnie (3) | 105% | **152%** | 68% | **109%** |
| DK pozostałe (9) | 82% | **147%** | 83% | **110%** |
| DW (5) | 60% | **90%** | 75% | **130%** |
| 15 odcinków w ±15% | 12 | **5** | 12 | **9** |
| mediana odchyłki 15 odcinków | 5,7% | **34,9%** | 2,6% | **8,1%** |
| mediana bezwzględnej zmiany odcinka R7/R6 | | 35% | | 11% |

Odcinki ze zmianą większą niż rozrzut seedów planów (9–12%, ok. 20 pp w mieście i DW): lekkie DK pozostałe 9/9, DK w Kutnie 3/3, DW 4/5; ciężkie DK pozostałe 7/9, DK w Kutnie 3/3, DW 3/5. A1 bez zmiany (lekkie 0/3, ciężkie 1/3). Tabela per odcinek: `r7/c7_r7_vs_r6.csv`, skrypt `c7_r7_vs_r6.py`.

## Wniosek

1. **Zmiana przekracza rozrzut seedów planów** na DK i DW, więc to efekt zmiany prędkości, nie losowości. Zgodnie z planem (§2 krok 4) robimy tu stop i nie robimy nowej estymacji O-D bez Twojej decyzji.
2. Kierunek zgodny z przewidywaniem z kroku 2: szybsze DK (B 1,00 zamiast 0,8, A 0,95) i wolniejsze drogi lokalne (C 0,60, F 0,55, D 0,70) przenoszą ruch na DK. Popyt był skalibrowany do GPR przy starych prędkościach (D19–D21), więc DK jest teraz przeładowane: lekkie 147–152% GPR na DK, ciężkie DW 130%. A1 się nie zmienia.
3. Gdy popyt O-D zostaje, sama zmiana prędkości psuje zgodność z GPR (lekkie 12 → 5 odcinków w ±15%). Ruch tła i ciężkich jest estymowany z czasów sieci, więc nowa estymacja (R7b) jest logicznym krokiem, ale to osobna decyzja.
4. Kongestia rośnie o ok. 25% (opóźnienie dobowe), co też łamie założenie z planu §4 pkt 2 (kongestia R6 stała w dopasowaniu `f_g`). Skutek dla dopasowania da dopiero walidacja (krok 5).
5. Ograniczenie: nie wiem, jak duża część przyrostu to przesunięcie tras, a jak duża to zmiana wyboru celów. Plany i macierze są te same, więc zmieniają się tylko trasy.

## Do decyzji

1. **R7b:** robić nową estymację O-D tła i ciężkich na czasach sieci R7 (macierze `background_od_r7b_*`, potem 5 runów, ok. 25 min), czy zostawić R7 jak jest i przejść od razu do kroku 5?
2. **Krok 5 (walidacja TomTom, jednorazowa):** teraz czy po R7b? Zestaw walidacji ocenia i niczego nie zmienia. Po R7b sieć się nie zmieni (prędkości te same), ale trasy modelu tak, więc walidacja po R7b jest sensowniejsza. Rekomendacja: po R7b.
3. Czy `f_g` (D 0,70, E 0,85, B 1,00 wbrew regule) zostają na stałe w D23, czy po walidacji wracamy do wartości z dopasowania.
