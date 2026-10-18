# Krok 5 (I1): jedna definicja czasu swobodnego w `link_delay.py` i `queues.py`

Data: 2026-10-18. Ustalenie: `audyt_g5.md` I1. Decyzja: D21 (pkt I1).

## Przewidywanie

Opóźnienia spadną do wartości z audytu: R3 ok. 150–155, R4 ok. 520–540, R5 ok. 400–420 poj.-h próbki. W nocy będzie ~0. `queues.py` zmieni się o kilka procent w górę, bo ff + 1 ≥ floor(ff) + 1.

## Która definicja (kontrola `skrypty/c5_night.py`, `c5_night_r4.log`)

Przejazdy pośrednie R4 w godz. 0–5 (59 279, pusta sieć), dt − czas swobodny:

| definicja | mediana | udział = 0 | udział < 0 | suma > 0 [poj.-h] |
|---|---|---|---|---|
| ff = length / v (stara `link_delay.py`) | +0,50 s | 0% | 0% | 10,85 |
| ff + 1 (stara `queues.py`) | −0,50 s | 0% | 98,8% | 2,53 |
| **floor(ff) + 1** | **0,00 s** | **98,8%** | **0%** | 2,64 |

Najkrótszy czas przejazdu w QSim to floor(ff) + 1 s (krok 1 s i przejście węzła). Przyjmuję go w obu skryptach (ciężkie z v = min(freespeed, 80 km/h)) i opisuję w docstringach. Pozostałe 1,2% nocnych przejazdów to rzeczywiste interakcje (ciężkie i osobowe w nocy na A1).

## Przeliczone opóźnienia (`k5_delay/*.json|png`, mapy w ciemnym motywie)

| run | stara `link_delay.py` | **audyt I1** | audyt (floor(ff) + 1) |
|---|---|---|---|
| R1 s4711 / s1 / s2 | 106–113 | **50,7 / 50,5 / 58,0** | – |
| R2 s4711 | 304 | **110,0** | – |
| R3 s4711 / s1 / s2 | 359 / 367 / 362 | **154,3 / 162,8 / 157,3** | 154,3 (s4711) |
| R4 s4711 | 820 | **540,3** | 540,3 |
| R5 s4711 | 693 | **419,3** | 419,3 |
| D18 s4711 / s1 / s2 | 735–854 | **646,4 / 640,8 / 758,9** | – |

- Zgodność z audytem do 0,1 poj.-h. Audyt podawał też wariant „−1 s” (R3 149,5, R4 521,3, R5 401,9), czyli tę samą definicję co stara `queues.py`. Ta definicja zaniża opóźnienie o ułamek sekundy na przejazd.
- Noc (0–4 h): R3, R1, D18 0; R4 0,2–1,4 poj.-h/h, R5 0,1–0,5 poj.-h/h (ciężkie). **~0, zgodnie z przewidywaniem.**
- `queues.py` R4 (okno 6–9): 125,1 → 129,1 poj.-h (+3%), udział czasu w opóźnieniu 5,6% → 5,8%, przepełnione linki 0 → 0.

## Zmienione wnioski

- R3 → R4: kongestia rośnie **3,5×** (154 → 540), a nie 2,3× (359 → 820). Wzrost dodatkowo zawyża fantom K1 w R4 (największe opóźnienia wokół Krośniewic).
- R5 wobec R4: **−22%**, a nie −16%.
- R1 wobec D18: −92%, a nie −86%. Wniosek o silnej nieliniowości kongestii bez zmian.
- Adnotacje „audyt I1” dopisane obok starych liczb w: `g5_r2.md`, `g5_r3.md`, `g5_r4.md`, `g5_r5.md`, `g5_r4_vs_r5_decyzja.md`, `g5_czasy_pce.md`, `g6_kolejki.md` (D18), `docs/research/G5_plan_kalibracji.md`.
- Nie przeliczałem raportów sprzed G5, które podają opóźnienia starą definicją: F5/F6, R3 MVP, D16, G2. Artefakt wynosi tam ok. 0,5 s na przejazd linku. Porównania między tymi raportami są spójne (ta sama definicja), ale wartości bezwzględne są zawyżone. Przyszłe runy liczą już nową definicją.

## Testy

- Kontrola niezależna `c5_night.py` (bez `pipeline/`): definicja potwierdzona na 59 tys. przejazdów.
- Wyniki R3, R4, R5 równe kolumnie audytu (inny skrypt, `skrypty/a2_delay.py`).
- `queues.py`: przepełnione linki bez zmian.
