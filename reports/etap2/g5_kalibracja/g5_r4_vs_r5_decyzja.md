# G5 / D20: R4 czy R5 jako baza (decyzja 2026-10-18)

> **Audyt I2 (2026-10-18):** Objazdowa 91124 i Bitwy pod Kutnem 91866 to **odcinki kontrolne użyte w wyborze wariantu** (W2, wyłączenie liczników lokalnych, R4 vs R5), a nie walidacja niezależna. Słowa „walidacja” / „test niezależny” w tym raporcie czytaj w tym sensie (`reports/etap2/audyt_g5/audyt_g5.md` I2).

**Decyzja użytkownika: R4 jest bazą.** R5 zostaje wariantem wrażliwości. Raporty: `g5_r4.md`, `g5_r5.md`.

## Co jest wspólne

Sieć, pracujący, ciężarówki (pce 2,5, 80 km/h) i ustawienia symulacji są identyczne (D19, D20, PassingQ). **Różni się tylko macierz ruchu tła**, czyli ile aut jedzie między którymi strefami (gminy powiatu i wjazdy na granicy sieci).

## Skąd się bierze różnica

- **R4:** macierz policzona przy założeniu, że każdy jedzie najszybszą trasą w pustej sieci. Na takich trasach liczniki zgadzały się w 100%. W symulacji pojawiła się jednak kongestia, część aut zmieniła trasy i w rejonie Krośniewic ruch się rozjechał: obwodnica DK92a dostała 191% pomiaru, a DK91d tylko 20–46%.
- **R5:** jedna runda poprawki. Macierz policzona ponownie na trasach, które agenci faktycznie wybrali w R4.
  - Bez hamulca jedna relacja (Kutno → Krośniewice) urosła 9×, do 13 tys. podróży na dobę.
  - Dlatego każda relacja może się zmienić najwyżej 2× względem R4. To dodatkowe ZAŁOŻENIE.

## Wyniki obok siebie

| | R4 | R5 | lepiej |
|---|---|---|---|
| liczniki użyte do kalibracji (14 odcinków, lekkie) | 10/14 w ±15%, mediana odchyłki 6% | 12/14, mediana 0,4% | R5 |
| to samo, ciężkie | 11/14 | 10/14 | R4 (nieznacznie) |
| obwodnica Krośniewic 91122 (lekkie) | 191% | 100% | R5 |
| **test niezależny:** Objazdowa (lekkie) | 132% | 148% | R4 |
| **test niezależny:** Bitwy pod Kutnem (lekkie) | 86% | 93% | R5 |
| suma obu odcinków testowych (lekkie) | ok. 111% | ok. 122% | R4 |
| DK w Kutnie (3 odcinki, lekkie) | 108% | 114% | R4 |
| opóźnienia (poj.-h próbki) | 820 | 693 | – |
| opóźnienia, audyt I1 (poj.-h próbki) | 540 | 419 | – |
| ruch tła na dobę (lekkie / ciężkie) | 85 tys. / 25 tys. | 81 tys. / 22 tys. | – |

## Uzasadnienie wyboru R4

1. **R5 jest lepszy na licznikach, do których go dopasowano, a gorszy na tych, których nie widział.** (Audyt I2: „nie widział” w estymacji, ale oba odcinki służyły wcześniej do wyboru wariantów; „przeuczenie” to nadinterpretacja przy 2 odcinkach i 1 seedzie. Poparte jest tylko „R5 gorszy na Objazdowej”.) To sygnał przeuczenia: poprawa w próbie nie przełożyła się na test niezależny, a w samym Kutnie jest gorzej.
2. **Zysk R5 dotyczy głównie Krośniewic,** 20 km od Kutna. Projekt dotyczy Kutna, więc ważniejsze jest, co dzieje się na obwodnicy miasta.
3. **R5 to łańcuch:** zależy od tras z R4 i od arbitralnego ograniczenia 2×, a kolejne rundy nie mają gwarancji zbieżności. R4 da się odtworzyć wprost z liczników i sieci, bez dodatkowych założeń.

## Czego R4 nie robi dobrze (znane rozbieżności)

- Węzeł Krośniewic po kongestii: DK92 91121 i 91122 mają 150–190%, DK91d 91892 i 91119 20–46%. Drogi lokalne pod Krośniewicami są przeciążone, więc mapa kongestii powiatu pokazuje tam korek, którego w rzeczywistości prawdopodobnie nie ma.
- Objazdowa 132% przy Bitwy pod Kutnem 86% (K5: struktura skrętów na węźle DK60/DK92, której liczniki dobowe nie wyznaczają).

## Konsekwencje

- `config/kutno.toml`: `background_od` = `background_od_r4_lcv_cap.csv`, `heavy_od` = `background_od_r4_heavy_cap.csv`.
- Plany bazowe: `scenarios/kutno/plans_g5r4_25pct.xml.gz` (+ `_vehicles.xml.gz`).
- Do zrobienia (wstrzymane przez użytkownika do czasu audytu): R4 na 3 seedach jako referencja.
