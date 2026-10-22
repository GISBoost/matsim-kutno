# Test blokerów wizualizera na modelu Wiednia

Data: 2026-10-22. Cel: sprawdzić na prawdziwych danych dwa blokery z `docs/research/wizualizer_audyt_kodu.md` (tylko samochód; zlewanie id pojazdu z id osoby). Wizualizer porównany w dwóch wersjach: stara z `main` (przed poprawkami) i nowa z gałęzi `claude/viz-fundamenty-e093b2` (commit `9a272b9`).

## Dane i metoda

**Model.** `ait-energy/matsim-model-vienna` 2023.2 (commit `e8dc348`, 2025-03-26), licencja CC BY-NC 4.0. Repo ma same wejścia (sieć 375 tys. linków, populacja 332 tys. agentów, rozkład PT 52 062 odjazdy, config). Nie ma żadnych wyników symulacji, więc runy zrobiliśmy sami. Klon i scenariusze leżą w katalogu tymczasowym sesji, poza repo (licencja NC, nie redystrybuujemy danych).

**Dwa runy (MATSim 2026.0, `-Xmx10g`).**

| Run | Agenci | Iteracje | Tryby na sieci | Capacity factor | Wynik |
|---|---|---|---|---|---|
| A `vienna_1pct_test` | 3323 (1% populacji, seed 4711) | 10 | `car` | 0,01 | `output/vienna_1pct_test` |
| B `vienna_bike_test` | te same 3323 | 0 | `car` i `bike` | 0,01 | `output/vienna_bike_test` |

- Run A to config `config-baseline-subtourModeChoice.xml` z podmienioną populacją i frakcją próbki. Czas: ok. 8 min. Run kończył się z zakończeniem poprawnym (shutdown completed).
- Run B: bike dopisany do modów wszystkich linków, które mają `car` (inaczej sieć rowerowa była niespójna i MATSim przerywał). Z configu usunięta domyślna teleportacja roweru (`clearDefaultTeleportedModeParams`, walk i ride dodane jawnie). Rower jedzie po sieci tak szybko jak auto (domyślny typ pojazdu), bo test dotyczy tylko identyfikatorów.
- Capacity factor 0,01 jest zawyżony wobec spójnego 0,00108 (0,10836 × 0,01). Ruch w runie A nie jest wiarygodny. Wnioski dotyczą struktury pokrycia, nie realnego popytu.

**Pomiar.** Skrypty (poza repo, katalog sesji `scratchpad/vienna/tools/`: `blokery.py`, `ids.py`, `census.py`):
1. Jeden strumień po `output_events.xml.zst` (10,5 mln linii). Z niego „prawda”: nogi i osobo-godziny per `legMode` (arrival sparowany z departure danej osoby; kierowcy PT `pt_*` pominięci), eventy `travelled`, pary (vehicle, person) z `vehicle enters traffic`, wejścia pasażerów (`PersonEntersPtVehicle`).
2. Zawartość indeksu z `viz/index.npz` i `meta.json`: `track_id`, `track_person_i`, `ids`, `track_class`.
3. A/B kodu: ten sam run zindeksowany starym i nowym `viz_index.py` (stary na kopii eventów, żeby nie nadpisać cache nowego).

## Wyniki

### Bloker 1: pokrycie trybów (run A, agenci bez kierowców PT)

| Tryb | Nogi | Osobo-godz. | Udział | W indeksie |
|---|---|---|---|---|
| pt | 5504 | 1975 | 37,6% | tylko pojazdy, bez pasażerów |
| walk | 20 907 | 1637 | 31,2% | nie |
| car | 4213 | 1209 | 23,0% | tak (4214 tracków) |
| ride | 912 | 312 | 5,9% | nie |
| bike | 426 | 122 | 2,3% | nie |

- Nogi teleportowane (walk + ride + bike) to 22 245 i dokładnie tyle samo jest eventów `travelled`. Mają dystans i czas, nie mają pozycji po drodze: 39,4% osobo-godzin nie istnieje w oknie.
- Wszystkie 52 054 pojazdy PT trafiły do indeksu (emitują te same cztery eventy ruchu co auta), ale pasażerów brak. Tylko 4629 pojazdów (8,9%) przewiozło kogokolwiek (5507 wejść). 91% tracków to puste pojazdy.
- Klasy: stary kod bierze klasę z pierwszej litery id: PT dostaje `v`, osoby `1…9` (pierwsza cyfra id osoby, bez znaczenia). Nowy czyta `subpopulation` z planów, PT dostaje `?`.

### Bloker 2: vehicle_id a person_id

- Run A (jeden tryb sieciowy): 1229 pojazdów nie-PT, wszystkie z id pojazdu równym id osoby, żaden z >1 kierowcą. PT: pojazd `veh_…`, kierowca `pt_veh_…`.
- Run B: **hipoteza z audytu potwierdzona**. Rower dostaje id pojazdu `<osoba>_bike` (166 pojazdów, 362 przejazdy; np. `101677_bike`), auto dalej `<osoba>`.
- Stary kod: 166 z 166 id `*_bike` istnieje w indeksie jako osobna tożsamość obok osoby bez suffiksu. Wyszukanie osoby znajdzie tylko auto, czynności (dom, praca) wiszą na id osoby, więc przejazd rowerowy ich nie ma.
- Nowy kod: 362 z 362 tracków `_bike` wskazuje przez `track_person_i` właściwą osobę, klasa poprawna (żaden nie ma `?`), 20 osób ma tracki `car` i `bike` pod jednym id i `lookup` zwraca oba. Liczba tracków 56 725 = 4309 + 362 + 52 054 (każdy przejazd rowerowy stał się trackiem).

## Wnioski

1. Bloker 2 jest naprawiony przez `person_id` w indeksie. Dokładanie trybów na sieci nie zepsuje identyfikacji.
2. Bloker 1 nie jest naprawiony. Okno pokazuje ok. 23% osobo-godzin w ruchu (auta) i puste autobusy. Pieszych, teleportowanych rowerzystów, ride i pasażerów PT nie ma.
3. PT wymaga osobnej klasy (linia, tryb z `TransitDriverStarts`) i powiązania pasażerów z pojazdem.
4. Teleportacja nie zostawia geometrii. To ogranicza także architekturę silnika: sam precompute po stronie klienta poprawi wydajność, ale nie brak trasy pieszych.

## Ograniczenia

- Jeden run na wariant, run B ma 0 iteracji, capacity factor nieskalibrowany.
- Test na danych i funkcji `lookup`, nie na kliknięciach w oknie.
- 744 `stuckAndAbort` w runie A (głównie `pt`) nie zbadane.
- Wynik dotyczy modelu, w którym `walk`, `bike` i `ride` są teleportowane. W modelu z rowerem na sieci (jak w runie B) rower jest widoczny.
