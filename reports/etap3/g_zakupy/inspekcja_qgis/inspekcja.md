# Inspekcja celów zakupów i usług w QGIS: BDOT10k a OSM (2026-10-30)

Sprawdzamy pulę budynków, z której `pipeline/errands.py` (D32, baza R9.3) losuje cele wypraw (waga = obrys). Pulę porównujemy z punktami sklepów i usług z OSM.

**Źródła:**

- BDOT10k `OT_BUBD_A` (wersja 2025-12-09, `config/kutno.toml: home_bdot`): budynki eksploatowane w gm. Kutno, z funkcjami z `errands.TYPES`.
- OSM `data/raw/osm/lodzkie-261015.osm.pbf`: węzły i obszary z `shop=*` oraz z wybranymi `amenity` (bank, poczta, urzędy, zdrowie, gastronomia, paliwo).
- POI dopasowany do budynku BDOT = budynek w odległości ≤ 15 m (ZAŁOŻENIE progu).

**Skrypty:** `prep.py` (warstwy) i `stats.py` (koncentracja i nazwy OSM). Uruchamiaj z katalogu projektu:

```
uv run python -W ignore reports/etap3/g_zakupy/inspekcja_qgis/prep.py <out.gpkg>
uv run python -W ignore reports/etap3/g_zakupy/inspekcja_qgis/stats.py <out.gpkg>
```

Projekt QGIS: `inspekcja.qgz` (warstwy w `inspekcja.gpkg`, plik poza gitem, odtwarzalny skryptem).

## Co jest w puli BDOT

| typ | funkcje BDOT | budynki | obrys m² | koncentracja wagi |
|---|---|---:|---:|---|
| c (centra handlowe) | centrum handlowe 3, hiper/supermarket 3 | 6 | 36 845 | Galeria Różana 34%, Leroy Merlin 20%, Carrefour 19% |
| s (inne zakupy) | dom towarowy 59, obiekt handlowo-usługowy 228 | 287 | 105 496 | top 10 = 29% |
| u (usługi) | bank 9, inny urząd 13, starostwo 5, urząd miasta 2, urząd gminy 1, poczta 3 | 33 | 12 785 | top 10 = 60% |

**Rozmieszczenie** (odległość od mediany POI OSM, czyli centrum przy ul. Królewskiej; średnia ważona wagą losowania):

- c: 1,13 km, nic dalej niż 2 km.
- s: 1,46 km, 23% wagi dalej niż 2 km.
- u: 0,72 km.

Dla porównania POI OSM mają medianę 0,67 km i tylko 6% dalej niż 2 km.

## Porównanie z OSM

POI OSM w gminie: 359. Kategorie: sklep 207, duży handel 58, gastronomia 32, zdrowie 30, urząd/bank/poczta 23, inne 9.

| kategoria OSM | POI | w budynku z puli c/s/u | w budynku mieszkalnym BDOT | bez budynku BDOT w 15 m |
|---|---:|---:|---:|---:|
| duży handel (supermarket, galeria, DIY, meble, auto…) | 58 | 47 (81%) | 2 | 0 |
| sklep (pozostałe `shop`) | 207 | 120 (58%) | 57 (28%) | 13 |
| urząd, bank, poczta | 23 | 10 (43%) | 8 | 1 |

Kolumna „w budynku mieszkalnym BDOT” obejmuje funkcje „budynek jednorodzinny” i „wielorodzinny”. „Bez budynku BDOT w 15 m” to POI bez żadnego budynku w promieniu 15 m.

**Wnioski:**

1. **Handel na parterach kamienic i bloków nie ma szans być celem.** 49 sklepów OSM stoi w budynkach BDOT „wielorodzinny”, w tym prawie cały ciąg ul. Królewskiej (rys. `centrum.png`). Takie budynki nie wchodzą do puli. Podobnie 8 z 23 banków i poczt. Model przesuwa więc wyprawy z centrum do wolnostojących pawilonów.
2. **Podział c/s wg funkcji BDOT nie odpowiada podziałowi GUS.**
   - Kaufland, Lidl, Aldi i 4 z 5 Biedronek mają w BDOT funkcję „dom towarowy lub handlowy”, więc trafiają do s.
   - Jedno Dino (583 m²) ma funkcję „hipermarket”, więc trafia do c, a Leroy Merlin dostaje 20% wagi c.
   - Pula c ma 6 budynków, a waga obrysu daje Galerii Różanej co trzecią wyprawę „centrum handlowe”.
3. **Część puli s to nie sklepy dla mieszkańców.** 148 z 287 budynków s (34% wagi) nie ma żadnego POI OSM. Trzeci co do wagi budynek s to 3 866 m² w strefie przemysłowej na wschodzie (528 756, 484 116; 4,2 km od centrum). Na ortofoto (`wsch_3866.png`) to hala przy placach maszyn rolniczych, a OSM ma tam `building=industrial`. Kolejne budynki bez POI: 2 279 m² (521 195, 485 558; 3,6 km na zachód, OSM `building=yes` bez tagów), 1 945 m² (OSM `retail` bez nazwy) i 1 823 m² w centrum.
4. **Usługi u: 57% wagi w budynkach bez POI OSM.** To głównie urzędy, czyli starostwo, „inny urząd” i urząd gminy. OSM rzadko taguje urzędy, więc tutaj brak POI nie dowodzi błędu BDOT.

**Ograniczenia:**

- OSM nie jest kompletny, więc brak POI to przesłanka, nie dowód.
- Próg 15 m przypisuje POI z chodnika do najbliższego budynku.
- Ocenę z ortofoto zrobił agent dla jednego budynku. Resztę (rys. `cale.png`, `centrum.png`) powinien obejrzeć człowiek w `inspekcja.qgz`.

**Do decyzji** (dopisz do punktu otwartego D32 o wyborze celu):

- (a) Dołączyć do puli s budynki z POI OSM `shop` (także mieszkalne), z wagą liczoną liczbą POI zamiast obrysu.
- (b) Wyłączyć z puli „obiekt handlowo-usługowy” w strefach `landuse=industrial` bez POI.
- (c) Typ c wyznaczać po OSM `shop=supermarket|mall|department_store` zamiast po funkcji BDOT.

Każdy wariant wymaga nowych planów i testu GHA. Zmiana dotyczy tylko celów wypraw `e`.

## Rysunki

### `cale.png`: cała gmina

Jak czytać wykres:

- **Tło:** OSM, granica gminy jako czarna linia.
- **Wielokąty:** budynki z puli BDOT. Czerwone to c (centra, hiper- i supermarkety), pomarańczowe to s (dom towarowy, obiekt handlowo-usługowy), niebieskie to u (urzędy, banki, poczta). W tej skali są małe.
- **Kropki:** POI OSM. Bordowe to duży handel, różowe to sklepy, turkusowe to urząd, bank lub poczta, zielone to zdrowie, żółte to gastronomia, szare to inne (paliwo).
- **Liczby:** z `prep.py`.

### `centrum.png`: centrum, ok. 1,8 × 1,3 km

Jak czytać wykres:

- **Tło:** ortofoto Esri World Imagery.
- **Kolory:** jak w `cale.png`.
- **Co widać:**
  - Różowy ciąg kropek wzdłuż ul. Królewskiej i placu: sklepy w budynkach spoza puli, bez wielokątów pod spodem.
  - Duży czerwony wielokąt po prawej: Galeria Różana.

### `wsch_3866.png`: strefa przemysłowa na wschodzie (ok. 700 × 500 m)

Jak czytać wykres:

- **Tło:** ortofoto Esri.
- **Wielokąty:** pomarańczowe budynki to pula s, z etykietą typu i obrysu w m².
- **Co widać:** budynek s 3 866 m² to hala w strefie przemysłowej. Bordowa kropka na północy to POI OSM (handel samochodami lub maszynami) na placu, nie w hali.
