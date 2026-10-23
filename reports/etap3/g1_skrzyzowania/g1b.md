# G1b: przepustowość wlotów do skrzyżowań (D27)

Data: 2026-10-23. Skrypty: `g1b_klasy.py`, `g1b_porownanie.py`; Java: `CreateKutnoNetwork.applyInflowCapacity`; workflow `.github/workflows/matsim-g1b.yml` (run 39926454585), wyniki w `g1b_porownanie.json`.

## Co zrobiono
Sieć R8 z `capacity` wlotów × k: wszystkie wloty do 33 węzłów z sygnalizacją OSM (85 linków) i 948 wlotów niższej rangi drogi na skrzyżowaniach (residential 446, unclassified 381, living_street 76, tertiary 43, secondary 2). Znaki give_way/stop nie mają osobnej reguły (tag bez kierunku wlotu). k = 1,0 (kontrola, identyczna z R8 co do bajtu), 0,8, 0,6, 0,4 (ZAŁOŻENIE: dolne granice Berlina, nie pomiary z Kutna). 4 sieci × 5 runów (3 seedy MATSim, 2 seedy planów), 25%, 50 iteracji. 18 runów policzył GitHub Actions, 2 (k=0,4 s4711, k=0,6 p1; błąd pobrania DTD) policzono lokalnie tą samą konfiguracją. Wszystkie: 0 stuck, liczba nóg zgodna z planami. Test 2 iteracji: ok.

## Wyniki (mediana 5 runów, odniesienie k = 1,0)
| k | opóźnienie dobowe (poj.-h próbki) | zmiana | rozrzut planów | GPR lekkie w ±15% | GPR ciężkie w ±15% | maks. zmiana natężenia odcinka lekkie / ciężkie | przyczyny (węzeł / spillback / przepustowość) | linki >2x pojemności (maks.) |
|---|---|---|---|---|---|---|---|---|
| 1,0 | 226,6 | – | 30,5 | 14/15 | 14/15 | – | 49 / 33 / 18% | 1 |
| 0,8 | 242,7 | +7% | 41,9 | 14/15 | 14/15 | 0,9 / 2,0% | 39 / 33 / 29% | 1 |
| 0,6 | 285,7 | +26% | 44,4 | 14/15 | 14/15 | 0,9 / 6,7% | 32 / 37 / 30% | 2 |
| 0,4 | 473,2 | +109% | 72,2 | 14/15 | 14/15 | 2,9 / 6,7% | 22 / 40 / 31% | 4 |

Kontrola metody: k = 1,0 na 50 iteracjach daje 226,6 poj.-h wobec 216,2 dla R8 na 100 (różnica 5%, w rozrzucie planów 38), więc 50 iteracji nie psuje obrazu opóźnień. Mediana rozrzutu planów na odcinek GPR: 4,4% (lekkie), 5,4% (ciężkie).

## Wnioski (tylko na poziomie danych)
1. **Natężenia (GPR) nie reagują na k**: mediana zmiany ≤ 0,13%, 14/15 w każdym wariancie. Odcinki ponad rozrzut planów: 0–1 z 15. Wlot dławiony przez przepustowość nie zmienia wyboru trasy w skali odcinków GPR.
2. **Opóźnienie rośnie z malejącym k**: k = 0,8 mieści się w rozrzucie planów (+16 przy rozrzucie 42), k = 0,6 go przekracza (+59 wobec 44), k = 0,4 podwaja opóźnienie i podnosi liczbę przepełnionych linków (do 4). To opóźnienie kolejkowe: rośnie udział spillbacku, maleje udział „węzła”.
3. **To nie rozdziela `f_E`/`f_F` od węzłów.** Opóźnienie swobodne (czas przejazdu w ruchu swobodnym) jest nadal w `freespeed`; k dodaje tylko opóźnienie przy obciążeniu. Czy któryś k poprawia zgodność z czasami TomTom, nie sprawdzono (nowe requesty poza zakresem, D22, i zestaw walidacji zużyty).
4. Bazą pozostaje R8 (D26), `f` bez zmian. k = 0,8 jest bezpieczne (bez efektu poza szumem), k ≤ 0,6 zmienia opóźnienia ponad szum bez niezależnej walidacji, więc wartości są ZAŁOŻENIEM z Niemiec.

## Ograniczenia
- Wartości k nie mają źródła z Polski. Brak walidacji opóźnień (czasy tras TomTom) dla tych wariantów.
- Ocena opóźnienia: jeden zestaw planów p0 plus dwa inne; rozrzut z trzech planów (max − min).
- Znaki i kierunek pierwszeństwa nie są modelowane; tagi give_way/stop nie dodały reguły.
