# D23: obserwacje o wartościach f_g (do dalszego dopracowania)

Data: 2026-10-21. Wartości w sieci R7b (decyzja użytkownika: „na dziś”, `f_D` bez zmian; zmiany później, po kolejnych sprawdzeniach):

| grupa | klasa drogi | f w sieci | dopasowanie z kroku 2 (90%) |
|---|---|---|---|
| A | autostrada (`motorway`) | 0,95 | 0,92 (0,83–1,00) |
| B | DK/DW poza miastem (`trunk`, `primary`, `secondary`) | 1,00 | 1,02 (0,93–1,10) |
| C | lokalne poza miastem (`tertiary`, `unclassified`) | 0,60 | 0,60 (0,53–0,68) |
| D | osiedlowe poza miastem (`residential`, `living_street`) | 0,70 | 0,75 (0,61–0,94) |
| E | główne w mieście (`trunk`…`tertiary`) | 0,85 | 0,88 (0,73–1,05) |
| F | lokalne w mieście (`residential`, `unclassified`, `living_street`) | 0,55 | 0,50 (0,50–0,55) |

Źródła: [krok2_dopasowanie.md](krok2_dopasowanie.md) (dopasowanie), [krok4b_5_r7b.md](krok4b_5_r7b.md) (R7b i walidacja). Zestaw walidacji jest już zużyty (jedna ocena), więc nowe sprawdzanie `f` wymaga nowego zestawu tras albo ponownego dopasowania na obu zestawach razem.

## Obserwacje

1. **A (autostrada):** `f` ≈ 0,92–0,95 daje ok. 129–133 km/h przy limicie 140, zgodnie z `freeFlowSpeed` TomTom (129–130). Walidacja: segmenty A1 model/TomTom 1,02–1,03. Stabilne.
2. **B (DK/DW poza miastem):** dopasowanie 1,02, więc prędkość swobodna na DK/DW to ok. 90–92 km/h przy limicie 90 (TomTom `freeFlowSpeed` 87–92). Segmenty DK po zmianie: 1,01–1,03. Segmenty DW poza miastem są nadal za wolne (0,86–1,05). Walidacja tras daje medianę 1,07 (model nieco wolniejszy). Wartość 1,00 jest bezpieczna; 1,02–1,05 do rozważenia, osobno dla DK i DW, jeśli to będzie potrzebne (DW to głównie `secondary`).
3. **C (lokalne poza miastem, 65% km sieci):** najmocniejszy wynik. Dopasowanie 0,60, walidacja wskazuje 0,59, MAPE czasu tras w tej grupie 17,9 → 7,3%. Prędkość swobodna ok. 54 km/h przy limicie 90 (tag lub domyślnie 90 dla `rural`), czyli 40% poniżej D13. Zgodne z audytem, ORS (30–50 km/h) i walidacją GUS. Nie zmieniać bez nowych danych.
4. **D (osiedlowe poza miastem):** jedyna grupa, w której R7b wyraźnie się pogorszył (MAPE walidacji 38 → 47%, mediana model/TomTom 1,21, model za wolny). Dopasowanie 0,75, wskazanie walidacji ok. 0,85, wartość w sieci 0,70. Mało tras (4 w walidacji, 11–12 w analizie, 37 km), przedział szeroki (±0,17), więc to kierunek, nie pewna wartość. **Kandydat nr 1 do poprawy** (0,75–0,85). Na wsiach OSM często ma `maxspeed`=50 na DK i 90 poza nimi, więc grupa miesza limity: pomysł z planu §4 pkt 3, osobny `f` dla `speed_source = default_*`.
5. **E (główne w mieście):** sygnały sprzeczne. Dopasowanie na trasach 0,88, walidacja tras wskazuje ok. 0,70, a segmenty miejskie (primary/secondary/tertiary, n = 3) pokazują model o 35% wolniejszy od TomTom (0,62–0,65). Trasy zawierają opóźnienia skrzyżowań, segmenty nie. Wniosek: `f` w mieście miesza prędkość z opóźnieniami węzłów; nie dopasowywać, dopóki nie ma G1 (skrzyżowania).
6. **F (lokalne w mieście):** dopasowanie na dolnej granicy 0,50 (prawdziwe minimum poniżej). Walidacja wskazuje ok. 0,46, MAPE bez zmian (25%). `f` ≈ 0,5 oznacza 25 km/h przy limicie 50 i jest w istocie czasem skrzyżowań i manewrów schowanym w prędkości. Do rozdzielenia po G1.
7. **Dopasowanie nie jest jedynym kryterium.** Dopasowanie z kroku 2 używało kongestii R6 jako stałej; kongestia R7b jest podobna (opóźnienie dobowe 209–247 vs 239–298 poj.-h), a MAPE w próbie wyszedł jak przewidziano (14,7% vs 14,3%), więc to założenie się sprawdziło.
8. **Zmiana `f` zmienia natężenia.** R7 (bez nowej estymacji O-D) przesunął ruch z dróg lokalnych na DK i zepsuł zgodność z GPR (lekkie w ±15%: 12/15 → 5/15). Dlatego każda zmiana `f` wymaga ponownej estymacji O-D (krok R7c: macierze, plany, 5 runów, ok. 1 h) i nowej oceny.
9. **TAG (> 85% tras w 15% lub 1 min) niespełnione**: 58% (walidacja), 64% (analiza). Pozostały błąd to głównie skrzyżowania (G1) i wybór trasy, nie prędkość swobodna.

## Plan dalszego sprawdzania (propozycja)

1. Po G1 (skrzyżowania): ponowne dopasowanie E i F (opóźnienia węzłów w modelu zamiast w `f`), prawdopodobnie wzrost `f_E` i `f_F`.
2. Rozważyć `f_D` 0,75–0,85 i podział grupy D wg `speed_source` (tag vs domyślny).
3. Nowy zestaw walidacji: kolejne losowe trasy (seed z `config/kutno.toml`), 12 tras na grupę D i F najpierw, bo mają najmniej danych. Koszt: ok. 3 requesty na trasę.
4. Przy każdej zmianie `f`: R7c (nowa estymacja O-D), 5 runów, GPR (14/15 odcinków w ±15% jako próg „nie gorzej niż R7b”), potem walidacja na świeżych trasach.

## Gdzie są dane TomTom i czy można je użyć ponownie

- **Zapisane lokalnie (agregaty, D22 wariant A):** wyniki dopasowania (`fit_f_g_tomtom.csv`, `fit_tomtom.json` z 21.10 i `fit_tomtom_2026-10-18.json`), metryki per grupa i okno (`metrics_r6_analiza_tomtom.csv`, `r7b/walidacja_r{6,7b}_tomtom.csv`, `r7b/walidacja_r6_vs_r7b_grupy.csv`), czasy modelu i trasy modelu (`g5_czasy_tomtom/model_times.csv`, `r7b/model_times_r7b.csv`, `r7b/pairs_routes_r7b.csv`), podział trasy → zestaw (`split.csv`), współrzędne par (`pairs.csv`), log requestów (`fetch_tomtom.log`: czas, kod, licznik, URL z `***`), wykresy z wartościami per obiekt w `output/g5_czasy_tomtom/` (poza gitem).
- **Nie zapisane:** same odpowiedzi TomTom (czas `historic`, `freeFlow`, geometria trasy). Regulamin TomTom (pkt 11.4) zabrania przechowywania, więc skrypt trzyma je tylko w pamięci i na dysk zapisuje agregaty (D22).
- **Skutek:** nowa kalibracja albo walidacja po zmianie modelu wymaga ponownych requestów (dopasowanie: ok. 240 na 80 tras analizy, walidacja: ok. 385). Strona modelu (trasy, czasy, grupy) jest zapisana, więc koszt to tylko zapytania do TomTom. Zużyte: 1 627 z 2 000 (`BUDGET`); limit dobowy 2 000, więc kolejna doba daje pełny budżet po zwiększeniu `BUDGET`.
- Gdyby chcieć przechowywać dane TomTom (np. `hist_s` per trasa) do wielokrotnej kalibracji, trzeba najpierw sprawdzić licencję (osobna decyzja, zmiana D22). Do tego czasu zostaje powtarzanie requestów.
