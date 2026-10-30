# D34: cel zakupów według sklepów OSM (wariant (a)+(c), 2026-10-30)

Wariant wybrał użytkownik po inspekcji QGIS ([inspekcja.md](../inspekcja_qgis/inspekcja.md)). Liczby pochodzą z [cel_osm.json](cel_osm.json), wykres z `cel_osm.py`.

**Zmiana w kodzie:**

- `pipeline/osm_poi.py` zapisuje sklepy OSM (`shop=*` bez `vacant`, węzły i obszary) z gminy Kutno do `scenarios/kutno/osm/shops.csv`. Jest ich 264.
- `pipeline/errands.py` z `errand_dest = "osm"` (`config/kutno.toml`):
  - Typ c (centra handlowe) to sklepy OSM `supermarket`, `mall` i `department_store`.
  - Typ s (inne zakupy) to pozostałe sklepy, także te na parterach budynków mieszkalnych.
  - Punkt celu to budynek BDOT w odległości do 15 m od sklepu, a gdy takiego nie ma, sam punkt sklepu.
  - Waga budynku to liczba sklepów danego typu w budynku, a nie obrys.
  - Usługi (u) zostają bez zmian, z BDOT.
- `errand_dest = "bdot"` jest domyślne i daje plany R9.3 bajt w bajt (sha256 `efcbe80…` = `scenarios/kutno_r91/plans_r93_p0.xml.gz`).

## Wynik na planach 25% (p0)

Oba warianty mają te same osoby, domy i godziny wyjść. Zmienia się tylko cel.

| | BDOT (R9.3) | OSM (D34) |
|---|---:|---:|
| wyprawy (c / s / u) | 204 / 456 / 51 | 204 / 456 / 51 |
| różne cele c | 5 | 21 |
| największy cel c, % wypraw c | 36,8 (Galeria Różana) | 9,3 |
| 5 największych celów s, % wypraw s | 18,9 | 21,9 |
| mediana odległości celu od centrum, km | 1,27 | 0,76 |
| cele w promieniu 0,5 km od centrum | 24,5% | 34,6% |
| cele s dalej niż 2 km od centrum | 23,5% | 6,6% |
| mediana odległości dom–cel, km | 1,62 | 1,41 |
| wyprawy krótsze niż 1 km | 24,2% | 31,6% |

**Co z tego wynika:**

- Cele przesuwają się do centrum i do sklepów osiedlowych.
- Wyprawy „centrum handlowe” nie skupiają się już w jednej galerii, tylko rozkładają się na 20 supermarketów.
- Największym celem s jest Galeria Różana (10%, około 30 sklepów w jednym budynku).
- Wypraw autem poniżej 1 km jest więcej (31,6%). Z dwóch powodów: model nadal nie wiąże wyboru celu z odległością (punkt otwarty D32), a trybów nie ma.

**ZAŁOŻENIA:**

- Waga to liczba sklepów, nie powierzchnia sprzedaży ani obroty.
- Wariant liczy wszystkie `shop=*`, także `car` i `car_repair`.
- Eurocash to hurtownia, ale w OSM ma tag `supermarket`, więc trafia do c (10 wypraw).
- OSM może być niekompletny. Nie ma źródła zewnętrznego, które by to sprawdziło.

## Dalej (test, jak D32)

1. Push i workflow `matsim-od` z `tag=r93o`, `compare=` (puste) i `plans=plans_k1_r93o.xml.gz`. Wynikiem są macierze `background_od_r93o*`.
2. Plany p0–p2: `plans.py ... errand_dest=osm seed=n errand_seed=32+n background_od=...r93o[_pn]_lcv... heavy_od=...`, zapis do `scenarios/kutno_r91/{plans,vehicles,meta}_r93o_p{0,1,2}`.
3. Workflow `matsim-r93o`: 5 runów r93o i 5 runów r93, porównanie skryptem jak `zakupy_porownanie.py`.

## Wykres `cel_osm.png`

![cel_osm](cel_osm.png)

Jak czytać wykres:

- **Lewy panel:** histogram odległości w linii prostej od domu do celu wyprawy, w koszykach co 0,25 km, do 6 km.
- **Prawy panel:** histogram odległości celu od centrum. Za centrum przyjęto medianę współrzędnych sklepów OSM, która wypada przy ul. Królewskiej.
- **Oś pozioma:** km. **Oś pionowa:** liczba wypraw w próbce 25% (711 wypraw, wszystkie typy razem).
- **Kolory:** pomarańczowy to BDOT (baza R9.3), turkusowy to sklepy OSM (D34). W legendzie podana jest mediana.
- **Źródło liczb:** `output/r93o/{bdot,osm}_p0_errands.csv` z `plans.py` (25%, seed 4711, `errand_seed` 32).
