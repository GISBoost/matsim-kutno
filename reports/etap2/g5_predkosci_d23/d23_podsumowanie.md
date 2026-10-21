# D23: podsumowanie kalibracji i walidacji prędkości sieci, stan prac

Data: 2026-10-21. Decyzja bazowa: D23 (`freespeed = limit × f_g`, grupy A–F). Baza po D23: **R7b** (D25).

## Na jakim etapie jesteśmy

| krok | stan | raport |
|---|---|---|
| 1 próbka tras (A–F, ≥ 12 w analizie, ≥ 6 w walidacji) | ✅ | [krok1_probka.md](krok1_probka.md) |
| 2 dopasowanie `f_g` na zestawie analizy (TomTom `historic`) | ✅ powtórzone 21.10 po dobraniu tras C | [krok2_dopasowanie.md](krok2_dopasowanie.md) |
| 3 sieć R7 (`setSpeed`, `factor.<grupa>`), smoke, test 2 iteracji, R7 25% × 5 | ✅ | [krok3_4_r7.md](krok3_4_r7.md) |
| 4 natężenia vs GPR | R7 (bez nowej estymacji) zepsuło zgodność (12/15 → 5/15 w ±15%) → **R7b** (nowa estymacja O-D) ✅ 14/15 | [krok3_4_r7.md](krok3_4_r7.md), [krok4b_5_r7b.md](krok4b_5_r7b.md) |
| 5 walidacja (jednorazowa, zestaw walidacji) | ✅ | [krok4b_5_r7b.md](krok4b_5_r7b.md) |
| decyzja: R7b nową bazą, `f` bez zmian, G5 zamknięte | ✅ D25 | `docs/projekt/DECISIONS.md` |
| dopracowanie `f` | otwarte, [obserwacje_f.md](obserwacje_f.md) | |

## Kalibracja (zestaw analizy, 77 tras, 231 obserwacji; TomTom `historic`, wt. 07:30 / 12:30 / 15:30)

| grupa | f dopasowane (90%) | f w sieci | trasy z przewagą grupy |
|---|---|---|---|
| A autostrada | 0,92 (0,83–1,00) | 0,95 | 12 |
| B DK/DW poza | 1,02 (0,93–1,10) | 1,00 | 12 |
| C lokalne poza | 0,60 (0,53–0,68) | 0,60 | 14 |
| D osiedlowe poza | 0,75 (0,61–0,94) | 0,70 | 11 |
| E główne w mieście | 0,88 (0,73–1,05) | 0,85 | 12 |
| F lokalne w mieście | 0,50 (0,50–0,55) | 0,55 | 12 |

W próbie (przewidywanie przy kongestii R6): MAPE 18,4 → 14,0% (wszystkie `f` z dopasowania), 14,3% (wg reguły identyfikowalności), TAG 51 → 69–71%.

## Wyniki w modelu R7b (po runach)

| | R6 | R7b |
|---|---|---|
| analiza (77 tras): MAPE / RMSPE / %RMSE | 18,3 / 24,7 / 20,9% | **14,7 / 21,5 / 16,1%** |
| analiza: MAE / RMSE [s], TAG | 114 / 153 s, 52% | **85 / 118 s, 64%** |
| **walidacja (38 tras): MAPE / RMSPE / %RMSE** | 20,5 / 26,2 / 18,6% | **18,2 / 25,7 / 15,9%** |
| walidacja: MAE / RMSE [s], TAG | 110 / 135 s, 48% | **90 / 116 s, 58%** |
| prędkość swobodna segmentów (16), mediana model/TomTom | 0,86 | **0,99** (MAPE 20 → 13%) |
| GPR: odcinki w ±15% (lekkie / ciężkie, z 15) | 12 / 12 | **14 / 14** |
| GPR: A1 lekkie / ciężkie | 99 / 101% | 98 / 101% |
| opóźnienie dobowe [poj.-h próbki, 5 runów] | 239–298 | 209–247 |

Walidacja per grupa (MAPE, walidacja, R6 → R7b): A 11,4 → 4,3% (n = 1), B 23,9 → 21,9% (4), **C 17,9 → 7,3% (7)**, **D 37,8 → 47,0% (4)**, E 21,2 → 22,2% (4), F 25,2 → 25,4% (5). Kryterium TAG (> 85% tras) niespełnione (58%). Szczegóły i zastrzeżenia (małe n, łączenie okien, brak niezależnej kontroli metryk R7b): [krok4b_5_r7b.md](krok4b_5_r7b.md).

## Co jest zapisane na dysku z TomTom

- **Agregaty (w repo i lokalnie):** `f_g` z przedziałami i n, metryki per grupa, okno i zestaw, log requestów (licznik, bez klucza), trasy i czasy modelu, współrzędne par, podział na zestawy.
- **Odpowiedzi TomTom per trasa i segment: nie zapisane** (D22 wariant A, regulamin TomTom 11.4). Wykresy z wartościami per obiekt są lokalnie w `output/g5_czasy_tomtom/` (poza gitem).
- **Ponowna kalibracja albo walidacja = nowe requesty** (ok. 240 i ok. 385; zużyte 1 627 z `BUDGET` 2 000, limit konta 2 000 na dobę). Strona modelu jest zapisana, więc kosztem są tylko zapytania. Szczegóły: [obserwacje_f.md](obserwacje_f.md) §„Gdzie są dane TomTom”.

## Pliki i polecenia (odtworzenie)

- Sieć R7: `java -cp matsim/matsim-example-project-0.0.1-SNAPSHOT.jar org.matsim.kutno.CreateKutnoNetwork data/raw/osm/lodzkie-261015.osm.pbf scenarios/kutno/area/network_area.wkt scenarios/kutno/area/towns.wkt config/network.properties scenarios/kutno/network.xml.gz`. Skrypty estymacji i planów czytają `scenarios/kutno/network.xml.gz`, więc ten plik **musi być siecią R7** przed uruchomieniem estymacji (R7b).
- R7b: model pracujących (`plans_g5r1k1_25pct`, 3 seedy, `run_r1.sh`), `background_od.py 30 r7b_{lcv,heavy}_gpr output/g5r7r1_25pct_s{4711,1,2} cls=… drop=10045,91892,91119` (p1/p2: `seed=1|2`), `plans.py … background_od= heavy_od=`, `run_r7b.sh`. Configi `scenarios/kutno/config_{10,25,100}pct.xml` i `config/kutno.toml` wskazują bazę R7b.
- Walidacja: `traffic_metrics.py model_r7b`, `traffic_providers.py run tomtom --validate`, `c7b_walidacja_raport.py`.
- Samodzielny scenariusz: `scenarios/kutno_r7b_25pct/` (config, sieć, plany, pojazdy; do runów poza tym repozytorium roboczym, np. GitHub Actions).
