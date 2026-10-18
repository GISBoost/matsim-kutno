# Audyt G5, poprawka K2: cel GPR ze strukturą rodzajową dnia roboczego (SDRDR)

Data: 2026-10-18. Ustalenie: `reports/audyt_g5/audyt_g5.md` K2. Decyzja: D21 (pkt K2).

## Błąd

Cel GPR był liczony jako SDRDR × (klasa_SDRR / SDRR) × kierunek. `dk_sdrdr.xlsx` (tablica 3, kol. 9 SDRDR, kol. 10–17 struktura) ma jednak własną strukturę dnia roboczego, w której ciężkich jest więcej. Przykład 71410 (A1): 10 + 14 723 + 40 + 2 915 + 704 + 9 732 + 79 + 0 = 28 203 = SDRDR.

## Poprawka

- `pipeline/g5_gpr.py`: zapisuje kolumny `<klasa>_dr` (struktura SDRDR) i `lekkie_osob_dr` w `gpr_linki.csv` i `gpr_punkty.csv`. Dla DW (tylko SDRR) `_dr` = struktura SDRR (**ZAŁOŻENIE**: dzień roboczy = średnia roczna). Stare kolumny bez zmian (sprawdzone porównaniem). Na 14 odcinkach DK suma `_dr` = SDRDR.
- `pipeline/background_od.py` i `pipeline/g5_baseline.py`: cel = Σ klas `_dr` × udział kierunku.
- `pipeline/g5_pce.py` (nowy, audyt D5): tabela `pce_wrd13_gpr.csv` ze skryptu. Tryb `sdrr` odtwarza starą tabelę bit w bit (`pce_wrd13_gpr_sdrr.csv`).

## R4 i R3 względem poprawionego celu (`r4_lcv.*`, `r4_heavy.*`, `r3_light.*`)

| | stary cel | **cel SDRDR** | audyt |
|---|---|---|---|
| R4 lekkie, A1 | 99% | **115%** | 115% |
| R4 lekkie, DK w Kutnie | 108% | **112%** | 112% |
| R4 lekkie, 14 odcinków w ±15% | 10/14 | **9/14** | 9/14 |
| R4 ciężkie, A1 | 100% | **68%** | 68% |
| R4 ciężkie, DK w Kutnie | 83% | **70%** | 70% |
| R4 ciężkie, 14 odcinków w ±15% | 11/14 | **5/14** | 5/14 |
| R3 lekkie (3 seedy), A1 | 101% | **122%** | 122% |
| R4 ciężkie, Objazdowa / Bitwy (kontrolne) | 70% / 77% | 61% / 60% | – |

Cel dnia roboczego na A1 (oba kierunki, 3 odcinki): lekkie z dostawczymi 62 186, ciężkie 31 637 poj./dobę.

## Tabela PCE (`g5_pce.py`, mediana brakującego ruchu w pojazdach umownych, w % lekkich)

| grupa | SDRR (stara) | **SDRDR** |
|---|---|---|
| A1 (3) | 104% | **173%** (135–195%) |
| DK poza miastem (24) | 80% | 103% |
| DK w Kutnie (3) | 82% | **99%** (Objazdowa 99%, Bitwy 64%, Sklęczkowska 99%) |
| DW (35) | 30% | 30% (bez zmian, ZAŁOŻENIE) |

Stare mediany „DK poza miastem 76%, DW 35%” z `g5_czasy_pce.md` nie odtwarzają się z CSV żadnym grupowaniem, które sprawdziłem (wszystkie punkty, punkty przypisane do linków). Skrypt podaje grupy jawnie. A1 i DK w Kutnie zgadzają się ze starym raportem.

## Wnioski

1. Liczby audytora potwierdzone co do punktu procentowego.
2. Zgodność R4 na A1 (99% / 100%) była efektem złego celu. W dzień roboczy model ma za dużo lekkich (+15%) i za mało ciężkich (−32%).
3. Macierze R4 trzeba policzyć od nowa (po I4). Ciężkich na dobę będzie więcej, a lekkich mniej niż w R4.
