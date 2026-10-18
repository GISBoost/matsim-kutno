# G6: wizualizacja MATSim w Blenderze (prototyp)

Metoda wg Bell, MUM 2026 (`data/raw/mum2026/107-20-bell.pdf`): węzły sieci → współrzędne sceny; eventy → pozycja pojazdu na klatkę → `.npz`; w Blenderze jedna siatka punktów aktualizowana handlerem `frame_change_pre`, kształt przez Geometry Nodes. Kodu Bella nie ma publicznie, całość napisana od zera. Stan: prototyp na runie `output/d16_25pct_s4711` (odczyt).

## Uruchomienie
```bash
uv run python pipeline/g6_bake.py                      # -> output/g6_blender/{vehicles,network}.npz, test (a)
"/c/Program Files/Blender Foundation/Blender 4.4/blender.exe" -b --factory-startup --python blender/g6_load.py -- --stills 600,1200,1800 --res 1280 720
"/c/Program Files/Blender Foundation/Blender 4.4/blender.exe" -b --factory-startup --python blender/g6_load.py -- --anim 1200 1440
"/c/Program Files/Blender Foundation/Blender 4.4/blender.exe" --python blender/g6_load.py   # GUI: scena, suwak klatek = handler
```
`--factory-startup` jest potrzebny: dodatki użytkownika (flip_fluids) rzucają błędy w handlerach klatek. Indeks klatki = `(t - t0)/step`; domyślnie klatka 1200 = 08:00.

## Parametry
- bake: `--run`, `--out`, `--t0/--t1` (s, domyślnie 21600–32400 = 06:00–09:00), `--step` (s symulacji/klatkę, domyślnie 5 → 2161 klatek), `--no-check`.
- scena: `--data --out --stills --anim A B --fps 24 --res W H --car-scale 8 --view 7000 --net-radius 9000 --net-width 12 --vmax 14`.
- Skala: **1 jednostka = 1 m**, origin sceny = (524805, 485023) w EPSG:2180 (x=E, y=N), z=0 to teren. Przy 1:1 auto 4,5 m jest niewidoczne z widoku 7 km, więc kształt jest powiększony ×8 (`--car-scale`); to wizualizacja, nie skala geometrii.

## Co robi bake
Strumieniowo czyta eventy `vehicle enters traffic / entered link / left link / vehicle leaves traffic`; każdy przejazd (pojazd może mieć 2 odcinki: tam i z powrotem) to osobny „track” z węzłami czasowymi (t,x,y) na końcach linków; pozycja klatki = `np.interp` (liniowo wzdłuż linku, prędkość zależna od czasu przejazdu, więc kolejki widać jako zwolnienie). Start: `relativePosition` linku. Widoczny tylko między wjazdem a zjazdem z ruchu. `.npz`: `ids, frames, pos (F,N,2 float32), visible (F,N), heading, speed (m/s na bieżącym linku, wlicza kolejkę)`. Sieć: `edges (E,4)` + `freespeed`.
Wynik runu: 539 tys. eventów w oknie → 4822 tracki, max 755 pojazdów jednocześnie (próbka 25%, skala × 4 do ruchu rzeczywistego), plik 33 MB.

## Test (a) – przechodzi
Bake losuje 3 tracki (seed 1), osobnym odczytem eventów buduje sekwencję linków (enter, left, link) i dla każdej widocznej klatki sprawdza `assert` odległość pozycji z `.npz` od odcinka linku < 0,5 m oraz że widoczność mieści się w [pierwszy enter, ostatni left]. Wynik w `output/g6_blender/bake.log`: 3× OK (245, 106, 23 klatek, 85/44/13 linków).

## Czasy (laptop użytkownika, Eevee Next, 64 próbki)
- bake 06–09, krok 5 s: **11,7 s** (+ test).
- start Blendera + 3 klatki 1280×720: **3 s** (~1 s/klatka).
- animacja 241 klatek 960×540 (10 s przy 24 fps = 20 min symulacji) → `reports/etap2/g6_blender/anim.mp4`: **57 s**; ffmpeg w Blenderze działa.
Wyniki: `reports/etap2/g6_blender/frame_{0600,1200,1800}.png`, `anim.mp4`.

## Ograniczenia
- Ruch tylko car; pojazdy to sześciany bez modelu; auta kolejkują się na jednej linii linku (brak pasów, brak przesunięcia na prawo).
- Czerwone kropki przy domach/pracy to pojazdy o niskiej średniej prędkości na linku (start z `relativePosition`, zawrotki); to nie błąd renderu.
- Dense `(F,N,2)` rośnie z oknem × N (83 MB w RAM dla 3 h); dla 100% próbki lub dłuższych okien przejść na format ragged (tylko aktywne).
- Próbka 25%: gęstość wizualna to ¼ rzeczywistego ruchu.
- Brak tła (budynki, ortofoto); sieć rysowana jako płaskie pasy 12 m.
- Pakiety Python: brak nowych (numpy, lxml, zstandard już w projekcie; numpy jest w Pythonie Blendera).

## Pomysły na rozwój
Budynki OSM 3D (Geometry Nodes z wysokości z OSM / extrude footprintów); kolor wg opóźnienia (czas przejazdu / czas free-flow z `freespeed`); BlenderGIS (ortofoto/podkład, tylko po zgodzie na dodatek); porównanie scenariuszy side by side (dwa `vehicles.npz`, dwa obiekty); kamera animowana i oznaczenia czasu (Text object z `frame → hh:mm`); ragged `.npz`; render Cycles/bloom dla finalnej wersji.

## Wersja narracyjna (`blender/g6_story.py`)
Inspiracja: film „MATSim Singapore in operation” (Future Cities Lab / senozon Via). Przeniesione koncepty: (1) błyski aktywności na ciemnym tle + zegar, (2) mapa ruchu kolorowana prędkością z legendą-gradientem, (3) śledzenie jednego agenta (kamera podąża, trasa „zapala się” za nim, pasek harmonogramu dom→podróż→praca, wykres jego prędkości), (4) wykresy narastające w kadrze (pojazdy w sieci, średnia prędkość). Pominięte: podkład mapowy/budynki, transport publiczny, wykres użyteczności (score) agenta, schemat pętli iteracji.
```bash
"/c/Program Files/Blender Foundation/Blender 4.4/blender.exe" -b --factory-startup --python blender/g6_story.py -- --res 1280 720 --story
```
Parametry: `--story`, `--story-stills 100,500`, `--story-range A B`, `--fps 30`, `--res`. Ujęcia (klatki wyjścia): A błyski (8 s, 06:00–06:40), B ruch z kolorem prędkości (14 s, → 07:40), C agent (czas ×~50, zoom in/out), D poranny szczyt do 09:00. Agent wybierany automatycznie (mieszkaniec, najdłuższy pełny przejazd po 07:40, ≤ 260 klatek). Nakładki to obiekty Blendera (tekst, krzywe, plansze) w dziecku kamery, skalowane z `ortho_scale`; wszystko aktualizuje handler `frame_change_pre`. Render ~0,4 s/klatkę (1280×720, 16 próbek).

### Wersja 2 (`story_v2.mp4`, 63 s)
Komenda: `blender -b --factory-startup --python blender/g6_story.py -- --res 1280 720 --net-radius 1e9 --story` (render ok. 9 min). Tempo 1 s filmu = 1 min symulacji (pokazane w kadrze). Ujęcia: 10 s cały powiat → 3 s zoom na agenta → follow do pracy (22 s) → 3 s zoom na Kutno (widok 14 km) → 10 s → 5 s zoom na powiat → 10 s. Szerokość dróg, rozmiar aut i błysków rosną z zoomem; w kadrze podziałka metryczna, podpis „co się dzieje”, na żywo prędkość agenta. Agent: `r6509026_1`, 06:12–06:33 (21,75 min). Wersja 1 (`story.mp4`) zostaje.

## Wersja 3 (`story_v3.mp4`, 75 s): historia jednego agenta

Skrypt `blender/g6_story3.py`, dane z osobnego bake'u całego dnia pracy agenta
(`uv run python pipeline/g6_bake.py --out output/g6_blender_day --t1 54600 --step 10 --no-check`, 3301 klatek co 10 s, 06:00–15:10, 7699 przejazdów).
Render: `blender -b --factory-startup --python blender/g6_story3.py -- --data output/g6_blender_day --res 1280 720 --net-radius 1e9 --story`.

Agent `r6509026_1` (ten sam co w v2): dojazd 06:13–06:34 (21,5 min), praca do 14:42, powrót 14:42–15:00.

| s filmu | ujęcie | tempo |
|---|---|---|
| 0–10 | cały powiat (błyski aktywności tylko do 7. s) | 1 s = 1 min |
| 10–13 | zoom na agenta | 1 s = 1 min |
| 13–36,5 | śledzenie dojazdu do pracy | 1 s = 1 min |
| 36,5–39,5 | zoom out na Kutno | 1 s = 1 min |
| 39,5–49,5 | Kutno, czas pracy agenta (ok. 8 h) w 10 s; płynne przyspieszenie do ok. 53 min/s, auta nadal jadą | do ~53 min/s |
| 49,5–52,5 | zoom na agenta | 1 s = 1 min |
| 52,5–72,3 | śledzenie powrotu do domu | 1 s = 1 min |
| 72,3–75,3 | agent w domu | 1 s = 1 min |

Zmiany względem v2:
- Błękitne prostokąty na skrzyżowaniach to były auta niewidoczne (jeszcze nie wyjechały albo już dojechały), „zaparkowane" na z = −10 000 pod węzłem sieci. Kamera ortogonalna ignoruje głębię, więc wystawały w lukach między czworokątami dróg. Teraz są odsuwane poza kadr (x, y = 1e7), podobnie ukryte błyski.
- Czcionka Segoe UI (`C:/Windows/Fonts/segoeui*.ttf`, polskie znaki) zamiast domyślnej Blendera.
- Tempo w prawym górnym rogu liczone na żywo (w przyspieszeniu pokazuje np. „1 s filmu = 53 min").
- Panel agenta: oś 06:00–15:10 z odcinkami dom / podróż / praca; bez krzywej prędkości (dojazd to ok. 1% osi). Prędkość na żywo w podpisie.
- Ograniczenie: krok danych 10 s, a w przyspieszeniu klatka filmu to ok. 100 s symulacji, więc auta w tym ujęciu „skaczą" (to próbkowanie, nie ruch ciągły).

## Otwarta obserwacja: kolejki
Zob. `docs/research/G6_kolejki_do_sprawdzenia.md` (ok. 26% klatek pojazdów < 1,5 m/s; hipotezy i plan weryfikacji dla głównego agenta).

## Wersja 4 (`story_v4.mp4`, 88 s): v3 + powiat do 20:00 + wykres wyniku agenta

Skrypt `blender/g6_story4.py`; dane: `uv run python pipeline/g6_bake.py --out output/g6_blender_day20 --t1 72000 --step 10 --no-check` (5041 klatek, 11 836 przejazdów, 250 MB).
Render: `blender -b --factory-startup --python blender/g6_story4.py -- --data output/g6_blender_day20 --res 1280 720 --net-radius 1e9 --story`.

Zmiany względem v3:
- Po powrocie agenta do domu (72,3–75,3 s): 3 s zoom out na cały powiat (1 s = 1 min), potem 10 s przyspieszenia (ok. 32 min/s) do 20:00.
- Na górze, między podpisami: wycentrowany wykres „wynik agenta narastająco" (kursor na bieżącym czasie, wartość liczbowa).
- Podpisy skrócone i łamane na dwie linie, żeby nie wchodziły na wykres.

Wynik agenta (utility): całka krańcowej użyteczności z parametrów `output_config.xml` (performing 6/h, home 16 h, work 8 h, priorytet 1,
`typicalDurationScoreComputation=relative`: U(d) = 6·typ·(ln(d/typ)+1) dla d ≥ typ·e⁻¹, liniowo poniżej; podróż −6/h dla car i walk). Dla pełnego dnia agenta ta formuła daje ok. 133,0 (sprawdzone ręcznie, wynik planu w MATSim: 133,04).
Uproszczenia wykresu (to ilustracja, nie wynik z MATSim): krzywa liczy przyrost od 06:00 bez „kar początkowych" aktywności (każda zaczyna od U(0) < 0 i rośnie), noc w domu liczona od 15:03 poprzedniego dnia (zakładamy ten sam dzień), a wieczór po powrocie to nowa aktywność od d = 0. Dlatego wartość na końcu (ok. +172) nie jest score'em planu (133,04).

## Opis do README (L-11)

Wizualizacja G6 pokazuje, jak w czasie przemieszcza się ruch samochodów w powiecie kutnowskim: pojazdy na sieci kolorowane prędkością, śledzenie jednego agenta od domu do pracy i z powrotem oraz wykresy liczby pojazdów i średniej prędkości (filmy w `reports/etap2/g6_blender/`). Jest to wyłącznie warstwa prezentacji: czyta gotowe wyniki symulacji i niczego nie zapisuje z powrotem, więc nie wpływa na wyniki modelu ani na configi MATSim. Wejście to eventy z runu 25% (`output_events.xml.zst`: wjazdy i zjazdy z linków) oraz sieć `output_network.xml.zst`, przetworzone przez `pipeline/g6_bake.py` do plików `.npz`. Pozycje aut są interpolowane liniowo wzdłuż linków, a nie pochodzą z pomiaru; ruch to próbka 25% populacji. Auta są powiększone ok. ×8 (kostka 4,5 m byłaby niewidoczna z kilku kilometrów), więc rozmiar nie oddaje skali rzeczywistej. Sieć jest rysowana jako pojedyncze kreski kierunkowe bez podziału na pasy, a szerokość dróg zależy od zoomu. Wykres „wynik agenta" w v4 to ilustracja (przyrost użyteczności), a nie score z MATSim.
