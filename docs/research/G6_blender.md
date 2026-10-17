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
- animacja 241 klatek 960×540 (10 s przy 24 fps = 20 min symulacji) → `reports/g6_blender/anim.mp4`: **57 s**; ffmpeg w Blenderze działa.
Wyniki: `reports/g6_blender/frame_{0600,1200,1800}.png`, `anim.mp4`.

## Ograniczenia
- Ruch tylko car; pojazdy to sześciany bez modelu; auta kolejkują się na jednej linii linku (brak pasów, brak przesunięcia na prawo).
- Czerwone kropki przy domach/pracy to pojazdy o niskiej średniej prędkości na linku (start z `relativePosition`, zawrotki); to nie błąd renderu.
- Dense `(F,N,2)` rośnie z oknem × N (83 MB w RAM dla 3 h); dla 100% próbki lub dłuższych okien przejść na format ragged (tylko aktywne).
- Próbka 25%: gęstość wizualna to ¼ rzeczywistego ruchu.
- Brak tła (budynki, ortofoto); sieć rysowana jako płaskie pasy 12 m.
- Pakiety Python: brak nowych (numpy, lxml, zstandard już w projekcie; numpy jest w Pythonie Blendera).

## Pomysły na rozwój
Budynki OSM 3D (Geometry Nodes z wysokości z OSM / extrude footprintów); kolor wg opóźnienia (czas przejazdu / czas free-flow z `freespeed`); BlenderGIS (ortofoto/podkład, tylko po zgodzie na dodatek); porównanie scenariuszy side by side (dwa `vehicles.npz`, dwa obiekty); kamera animowana i oznaczenia czasu (Text object z `frame → hh:mm`); ragged `.npz`; render Cycles/bloom dla finalnej wersji.
