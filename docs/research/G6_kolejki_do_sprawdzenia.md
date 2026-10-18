# G6 → główny agent: czy kolejki w wizualizacji to błąd? (do zweryfikowania)

**Odpowiedź (2026-10-17):** sprawdzone w `reports/etap2/g6_kolejki/g6_kolejki.md`. Kolejki to w większości realne wąskie gardła modelu (ulice tertiary z 600 poj./h/pas i zwężenie Sklęczkowskiej 2 → 1 pas). Artefakt: `stuckTime` 10 s kompresował kolejki na krótkich linkach. Poprawka D18 (30 s).

Źródło: wizualizacja G6 (`blender/g6_*.py`, bake `pipeline/g6_bake.py`), run `output/d16_25pct_s4711` (sampleSize 0,25, flow = storage = 0,25).
Status: obserwacja, przyczyna NIE zbadana. Wizualizacja odtwarza eventy wiernie (test (a) OK), więc to pytanie o model, nie o Blendera.

## Obserwacja
- ok. 26% klatek widocznych pojazdów (okno 06:00–09:00) ma prędkość < 1,5 m/s (prędkość = długość linku / czas przejazdu, bez przycinania cięciwą).
- Przykład: link `2446692260002r` — do 07:15 ponad 360 przejazdów dłuższych niż 60 s, pojedyncze auta stoją do ~360 s.
  Parametry z `output_network.xml.zst`: length 143,9 m (w notatce wejściowej było „60 m” — do sprawdzenia, który link/odcinek), freespeed 15,56 m/s, capacity 3000, permlanes 2, oneway, car.
  Przy takich parametrach przejazd wolny to ~9 s; 360 s oznacza kolejkę stojącą kilka minut.

## Hipotezy do sprawdzenia (od najtańszej)
1. Realne wąskie gardło: zbieg dojazdów do Kutna (przyjeżdżający D16 + mieszkańcy) na jednym wylocie; sprawdź przepustowość linku następnego (`left link` → następny `entered link`).
2. Artefakt skalowania 25%: capacity 3000 × 0,25 = 750 poj./h/pas; sprawdź, czy link następny (po węźle) ma `capacity` zaniżone przez konwersję OSM (D13 i `setSpeed/capacity` w `CreateKutnoNetwork`), np. skrzyżowanie/rondo bez rozróżnienia pasów, link jednopasowy o capacity z małej drogi.
3. Węzeł/zawrotka: zawrotki dodane na granicy (przed NetworkCleanerem) lub aktywność przypięta do linku (powrót wymaga zawrotki) → wszyscy zawracają jednym linkiem.
4. Spillback z linku z ograniczoną pojemnością składowania (`storageCapacityFactor` 0,25 przy krótkich linkach: miejsce na bardzo mało pojazdów, kolejka blokuje węzły).
5. Brak sygnalizacji/priorytetów w QSim: MATSim domyślnie wpuszcza po kolei z wielu wlotów; sprawdź węzły, gdzie zbiegają się główne drogi.

## Jak sprawdzić (skrypt, nie na oko)
- Z `output_events.xml.zst` policz per link: liczbę przejazdów > 60 s w oknach 15 min i medianę czasu; top-20 linków. (Mam gotowe strumieniowe czytanie eventów: `pipeline/g6_bake.py`, funkcje `lines`/`bake`.)
- Porównaj z `output_links.csv.zst` / linkstats (po przeskalowaniu × 1/sampleSize): czy wolumen/godz. na tych linkach przekracza `capacity`.
- Test kontrolny: ten sam run na 10% (`D17` B/C) — czy odsetek stojących pojazdów jest podobny (artefakt skali ≠ zależy od próbki).
- Referencja: czy dane z GPR 2025 / pomiarów (zob. `docs/research`, G5 walidacja) potwierdzają zatory w tym miejscu rano. Bez tego nie nazywać tego błędem ani prawdą.

## Gdzie to widać w filmie
`reports/etap2/g6_blender/story_v2.mp4`, 06:12–06:34: agent `r6509026_1` w kolejce (3 km/h w klatce kontrolnej). Czerwone auta = < ~15 km/h w skali koloru.

## Co zrobić z wynikiem
- Błąd sieci/capacity → poprawka w `CreateKutnoNetwork` + wpis w `DECISIONS.md` (D13 dotyczy prędkości) i test 2 iteracji.
- Realne zatory → zostawić, opisać w raporcie; nie kalibrować bez danych (zakres MVP zamrożony).
