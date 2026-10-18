# K5: dlaczego model ma za dużo na Objazdowej (91124) i za mało na Bitwy pod Kutnem (91866)

Data: 2026-10-18. Run R3 (`output/g5r3_25pct_s4711`). Skrypty: `pipeline/dk60_corridor.py` (atrybuty i select-link, wynik `dk60_corridor_r3.txt`) i `pipeline/turn_violations.py` (zakazy skrętu, `turns_r3.json`).

## Układ (ważne dla interpretacji)

Według GPR to **kolejne odcinki tej samej obwodnicy DK60**, a nie trasy alternatywne:
- 91124 „Obwodnica 1: ul. Objazdowa (DK92) – DK92, DW702” to ulica Objazdowa, wspólny przebieg DK60 i DK92;
- 91866 „Obwodnica 2: DK92, DW702 – ul. Skrajna” to Bitwy pod Kutnem, sama DK60.

Rozdziela je węzeł DK60/DK92/DW702, z którego na wschód wychodzi Sklęczkowska (DK92, licznik 91869).

| licznik | GPR (lekkie, oba kier.) | R3 | model / GPR |
|---|---|---|---|
| 91124 Objazdowa | 7 959 | 10 228 | 129% |
| 91866 Bitwy pod Kutnem | 7 165 | 6 020 | 84% |
| 91869 Sklęczkowska (w dopasowaniu) | 8 541 | 8 428 | 99% |
| suma trzech ramion węzła | 23 665 | 24 676 | 104% |

GEH ze średniej godziny doby (orientacyjnie, GEH jest zdefiniowany dla godzin): Objazdowa 4,8, Bitwy pod Kutnem 2,9.

## 1. Sieć vs OSM: zgodna

- **Objazdowa:** primary, 2 pasy na kierunek przy pomiarze (capacity 3 000), `maxspeed=90` z OSM, czyli 72 km/h w modelu (× 0,8, D13). Krótkie odcinki 70 km/h.
- **Bitwy pod Kutnem:** primary, 1 pas na kierunek (capacity 1 500), odcinki 50/70/90 km/h z tagów albo 50 domyślne miejskie, ronda Dmowskiego i Jasiukowicza przy 40 km/h.
- Czas swobodny przejazdu korytarzem: 3,2 min w obu kierunkach, długość 3,1 km.
- Nie znalazłem rozbieżności między atrybutami linków a tagami OSM (prędkość, pasy, rondo).

## 2. Zakazy skrętu: nie są przyczyną

- Konwerter nie czyta relacji `restriction` (znane z G1). W obszarze sieci jest 63 takich relacji i wszystkie dają się przypisać do par linków.
- W R3 łamie je 255 przejść, czyli ok. 1% podróży, głównie zawracanie. Na Objazdowej tylko 2.

## 3. Skąd ruch na odcinkach (select-link, doba, 100%)

- **Objazdowa w kierunku SW, 5 380:** 2 836 wjeżdża ze Sklęczkowskiej (DK92 od wschodu), 2 504 z Bitwy pod Kutnem.
  - Tło 3 692, dojazdy 1 688.
  - Największe relacje tła: Kutno (gmina) → Krośniewice (628) i wjazd DK60 od A1 (Kutno Płn.) → wyjazdy na zachód i południe.
- **Bitwy pod Kutnem:** ok. 3 000 na kierunek, w tym tło ok. 2 450. Tranzyt DK60 północ ↔ południe i Kutno ↔ A1 Kutno Płn.
- Nadwyżka na Objazdowej to ruch skręcający na węźle między Sklęczkowską a Objazdową (DK92 wschód ↔ zachód/południe). Model daje go więcej, niż wynikałoby z GPR. Niedobór na Bitwy pod Kutnem zgadza się z niedopasowaniem północnego ramienia DK60 (Sójki 91878: 88%).
- Wniosek: rozbieżność bierze się ze **struktury macierzy tła** (ile ruchu DK92 skręca w Objazdową, a ile DK60 jedzie na północ), a nie z sieci. Liczniki dobowe na odcinkach nie wyznaczają skrętów na węźle.

## 4. Warianty

| wariant | co | koszt | spodziewany efekt |
|---|---|---|---|
| **A (rekomendacja)** | zostawić; rozbieżność opisana, GEH < 5, suma węzła 104% | 0 | brak zmian; następny krok to R3 × 3 seedy jako referencja |
| B | wczytać zakazy skrętu z OSM do sieci (`DisallowedNextLinks` w `CreateKutnoNetwork`; część G1) | zmiana w Javie, test regresji, nowa sieć, nowe runy | poprawność modelu, ale ok. 1% przejazdów, więc na Objazdową wpływ znikomy |
| C | Objazdowa do dopasowania, walidacja tylko na Bitwy pod Kutnem | 1 estymacja (sekundy) + run | Objazdowa ≈ 100% z konstrukcji; zostaje 1 odcinek walidacyjny |
| D | sygnalizacja na węźle DK60/DK92/DW702 (G1, odłożone przez użytkownika) | duży (contrib signals, dane o fazach) | możliwy wpływ na skręty; brak danych o sygnalizacji |
| E | wrażliwość prędkości miejskich (factor 0,8 jednolity) | runy wariantów | wpływa na całą sieć, brak źródła do wyboru wartości |
