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

## Co znaczy „teleportowane” (ustalone w rozmowie)

Przykład: jedna osoba z runu B (id `10630`), eventy z jednej doby, wybór:

| Czas (s) | Co | Event |
|---|---|---|
| 16291 | wychodzi z domu, tryb `walk` | `departure` |
| 16304 | przeszła 14 m w 13 s | `travelled`, `arrival` |
| 16304 | auto wjeżdża w sieć (link 223827) | `vehicle enters traffic` |
| 17008 | wyjeżdża z sieci (link 189057) | `vehicle leaves traffic` |
| 17118 | przeszła 116 m w 110 s, jest w pracy | `travelled` |
| 46085 | wychodzi z pracy, idzie 382 m na przystanek | `travelled` |
| 46447–47182 | czeka na przystanku | `waitingForPt` |
| 47182–47652 | jedzie autobusem `veh_33876_bus` | `PersonEntersPtVehicle`, `PersonLeavesPtVehicle` |

- Dla nogi teleportowanej model zna moment wyjścia, moment przyjścia i dystans (`travelled`), ale **nie trasę**. Czas wynika ze wzoru: odległość w linii prostej × współczynnik ÷ prędkość (14 m w 13 s to ok. 1,1 m/s).
- **W obliczeniach teleportowane tryby są:** ich czas wchodzi do czasu podróży, oceny planu (scoring), wyboru trybu i tabel wyników.
- **W obciążeniu sieci ich nie ma:** pieszy, teleportowany rowerzysta i pasażer `ride` nie zajmują miejsca na drodze i nie tworzą korków. Dla `ride` to uproszczenie modelu Wiednia, a nie wizualizera: pasażer jest teleportowany, więc na drodze nie ma samochodu, którym jedzie (kompensacja przez autorów niesprawdzona).
- **PT nie jest teleportowane:** autobusy, tramwaje i pociągi to pojazdy w symulacji (52 054 odjazdy w modelu Wiednia). Autobusy jadą po sieci (linki `bus,car,pt`), zajmują miejsce na drodze (pce 0,35) i wpływają na auta. Czas pasażera wynika z rzeczywistego przejazdu pojazdu.

| Tryb | W obliczeniach | W obciążeniu sieci | W oknie |
|---|---|---|---|
| car | tak | tak | tak |
| PT (pojazdy) | tak | tak | tak (jako puste pojazdy) |
| PT (pasażerowie) | tak | nie dotyczy | nie, choć dane są w eventach |
| walk, bike, ride (teleportowane) | tak (czas i dystans) | nie | nie, bo nie ma danych o trasie |

## Decyzje i ustalenia z rozmowy (2026-10-22)

1. **Nogi teleportowane nie są ruszane.** Pieszych, teleportowanych rowerzystów i `ride` nie próbujemy rekonstruować (linia prosta, trasa z routera): to byłaby wymyślona geometria, a nie wynik symulacji. Zostają niewidoczne w oknie. (Rower lub pieszy przeniesiony na sieć w samym MATSim byłby widoczny, ale to osobna decyzja o modelu, nie o wizualizerze.)
2. **Dla Kutna bloker 1 prawie nie istnieje.** Dzisiejszy model to samochód `home → work → home`, a teleportowane są tylko krótkie dojścia i odejścia do auta. Pojawia się z pierwszym runem z PT (etap 3).
3. **Właściciel chce licznik pasażerów PT w symulacji** i wskazał punkty 2 (przedziały pasażerów) i 3 (ukrywanie pustych pojazdów) jako te, które mu się najbardziej podobają. Punkty 1 i 4 są propozycją, bez decyzji.
4. **Ten raport ma służyć dalszej pracy.** Zakres poniżej nie został jeszcze wysłany do sesji `viz-fundamenty`. Przed wysłaniem trzeba sprawdzić jej plan (`docs/projekt/wizualizer_aplikacja.md`), żeby się nie dublowało.

## Skala PT w indeksie (run A, 1% agentów, pełny rozkład PT)

- Pojazdy PT to **91,3% węzłów indeksu** (9 757 908 z 10 682 631) i **98,1% wpisów w klatkach**. Auta to 8,7% węzłów.
- Średnio 2201 pojazdów w klatce (kubełek 1 min), max 4405; w klatkach co 30 min PT dochodzi do 4312 pojazdów.
- PT **nie skaluje się z próbką**: autobusy jadą w 100%, auta w 1%. Wynik pokazuje strukturę, a nie proporcje dla Kutna 25%. Dla Kutna nie mierzone, bo model nie ma jeszcze PT.
- Skutek: licznik i wykres szczytu mieszają auta (próbka) z PT (100%).

## Proponowany zakres prac (tylko PT)

Wszystko wymaga jednej zmiany formatu indeksu (`FORMAT`), więc najlepiej zrobić razem. Szacunki pracy to moja ocena, bez pomiaru.

| # | Co | Praca | Status |
|---|---|---|---|
| 1 | **Klasy PT z `TransitDriverStarts`** (linia, trasa, tryb) zamiast `?`. Filtr dostaje „autobus”, „tramwaj”, „kolej”, „metro”. | mała | propozycja |
| 2 | **Przedziały pasażerów:** w indeksie „osoba X w pojeździe Y od t1 do t2” z `PersonEntersPtVehicle` i `PersonLeavesPtVehicle`. Pojazd dostaje **licznik obłożenia**, osoba w trakcie jazdy pozycję pojazdu i da się ją wyszukać. Czekanie na przystanku to punkt stały w miejscu czynności `pt interaction` (współrzędne są w eventach `actstart`). | średnia | **wskazane przez właściciela** |
| 3 | **Ukrywanie pustych pojazdów PT:** przełącznik „tylko z pasażerami”. Odciąża ekran i wydajność (91% pojazdów jest pustych w teście). Zależy od punktu 2. | mała | **wskazane przez właściciela** |
| 4 | **Osobne liczenie PT w liczniku pojazdów** (auta w próbce, PT w 100%), żeby wykres szczytu ich nie mieszał. | mała | propozycja |

**Warunki akceptacji (do sprawdzenia na runie z PT):** liczba wejść pasażerów w indeksie = liczba `PersonEntersPtVehicle` w eventach (5507 w runie A), liczba wyjść = `PersonLeavesPtVehicle` (5504, różnica to osoby, które nie wysiadły przed końcem symulacji), klasa żadnego tracka PT nie jest `?`, wyszukanie osoby w trakcie przejazdu PT zwraca jej pozycję i pojazd, a przełącznik pustych pojazdów zmniejsza liczbę rysowanych tracków do wartości zbliżonej do liczby pojazdów z pasażerem (4629 z 52 054 w runie A, 8,9%).

**Czego nie robić:** nie rekonstruować nóg teleportowanych, nie zmieniać modelu MATSim (np. rower na sieci) dla potrzeb wizualizacji bez osobnej decyzji w `DECISIONS.md`.

## Pliki i dane testowe

- Skrypty testu leżą poza repo (katalog sesji: `blokery.py`, `ids.py`, `census.py`). Jeśli mają być wersjonowane, trzeba je przenieść do `viz_player/tests/` (osobna decyzja).
- Runy: `output/vienna_1pct_test`, `output/vienna_bike_test` (gitignore, mają ok. 120 MB eventów każdy). Model Wiednia jest na licencji CC BY-NC 4.0 i nie wolno go dodawać do repo (`docs/ZRODLA.md` §8).
