# R3: wyniki z próbki 25% (100 iteracji, 3 seedy)

Data: 2026-10-17. Config `scenarios/kutno/config_25pct.xml`, plany `plans_25pct.xml.gz` (6 433 osoby, po naprawach E1, E5 i `building=no`).
Seedy 4711, 1, 2. Seedy 1 i 2 liczone równolegle po 4 wątki, każdy run ok. 13 min.

## Wydajność (dlaczego nie da się przyspieszyć pojedynczego runu)

- Mobsim zajmuje ok. 7 s z 8 s iteracji (`stopwatch.csv`). Przy 8, 4 i 1 wątku QSim trwa tyle samo (test 3 iteracji).
- Wyniki przy 4 i 8 wątkach są identyczne (it. 0–1: 11 624 i 8 331 h w aucie). Przy 1 wątku się różnią (11 619 i 8 340).
- Przyspiesza tylko równoległe liczenie seedów: 2 runy × 4 wątki na 12 rdzeniach w 13 min zamiast 26 min (`output/r3_runs.sh`).

## Testy semantyczne

| seed | nogi car | stuck | test |
|---|---|---|---|
| 4711 | 12 866 | 0 | `reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct_s4711_events.json` ok |
| 1 | 12 866 | 0 | `reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct_s1_events.json` ok |
| 2 | 12 866 | 0 | `reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct_s2_events.json` ok |

## Zbieżność (`reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct_convergence.json/png`)

- **Godziny w aucie (próbka 25%):** w iteracji 0 jest 11 624 h (wszyscy jadą trasą najszybszą przy pustej sieci). Po ok. 5 iteracjach spada do ok. 3 800 h. Do 80. iteracji waha się ±5%, po wyłączeniu innowacji wynosi 3 312–3 432 h. Rozrzut z ostatnich 10 iteracji to 0,7–1,3%.
- **Natężenia top-50 linków (zmiana co 10 iteracji, średnia z 5):**
  - dobowo 0,3–1,5% w it. 100;
  - w szczycie 7–8 0,9–2,6% w it. 100;
  - przed it. 80 w szczycie 7–8 było to 2–8%.
- Wniosek: przy 100 iteracjach natężenia dobowe są stabilne. W godzinie szczytu zostaje kilka procent szumu między iteracjami. Nie twierdzę, że to równowaga w ścisłym sensie, bo nie ma miary luki względnej.

## Zgodność między seedami

- **Uwaga: GEH porównuje tu dwa runy modelu (stabilność względem losowości), nie model z pomiarami.** Walidacja wymaga pomiarów ruchu, których jeszcze nie mamy.
- **GEH na natężeniach przeskalowanych do 100%** (× 1/0,25), linki z ≥ 100 poj./dobę (3 046 linków):

| para | GEH < 5, szczyt 7–8 | GEH < 5, średnia godzinowa doby | max GEH 7–8 |
|---|---|---|---|
| 4711 vs 1 | 99,5% | 100% | 6,2 |
| 4711 vs 2 | 98,9% | 100% | 9,3 |
| 1 vs 2 | 99,4% | 100% | 10,2 |

- **Wskaźniki zbiorcze (`reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct_seeds.json/png`):**

| seed | mediana czasu podróży, mieszkańcy / przyjeżdżający [min] | p90 [min] | opóźnienie razem [poj.-h próbki] |
|---|---|---|---|
| 4711 | 15,5 / 24,1 | 35,0 / 36,8 | 1 129,7 |
| 1 | 15,2 / 24,2 | 33,3 / 36,2 | 1 036,8 |
| 2 | 15,6 / 24,0 | 31,6 / 35,8 | 1 013,7 |

- Mediany różnią się między seedami o ≤ 0,4 min. P90 mieszkańców różni się o 3,4 min. Suma opóźnień różni się o 11% (1 014–1 130).
- Opóźnienie jest w pojazdo-godzinach próbki. Dla pełnej populacji to w przybliżeniu × 4, czyli ok. 4 000–4 500 poj.-h. To przybliżenie, bo przy 25% kolejki są modelowane ze skalowaną przepustowością.
- **Najbardziej opóźnione linki są te same we wszystkich seedach:**
  - 5452223090000r (primary, kolejka cofająca się z wąskiego gardła): 135 / 105 / 111 poj.-h;
  - 410250640002r (Sklęczkowska, DK92): 101 / 50 / 58 poj.-h.
- Opóźnienie na pojedynczym linku zmienia się między seedami nawet dwukrotnie. **Wniosków o pojedynczych linkach nie wolno opierać na jednym seedzie.** Ranking wąskich gardeł jest stabilny.

## Select-link DK92 (seed 4711, `reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct_select_dk92.*`)

- Przez Sklęczkowską jedzie 2 463 z 6 433 osób, głównie z gm. wiejskiej Kutno (1002062) i z obwodów 65115–65117.
- Ten wynik pochodzi z jednego seeda. Ranking źródeł należy potwierdzić na pozostałych seedach.

## Ograniczenia (bez zmian względem R3)

- Brak ruchu tła i wszyscy jeżdżą autem (D6).
- Miejsca pracy są ważone powierzchnią (D7).
- Profil godzin pochodzi z Gdańska (D14).
- Przepustowości są domyślne z OSM.
- Model nie jest walidowany na pomiarach. Zgodność seedów mówi o stabilności modelu, nie o jego zgodności z rzeczywistością.
