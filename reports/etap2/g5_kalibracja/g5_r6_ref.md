# G5 / D21: referencja R6, 3 seedy MATSim + 2 seedy planów (audyt I3)

Data: 2026-10-18. Krok 8 planu poprawek. Baza: `g5_r6.md`. Skrypt podsumowania: `reports/etap2/audyt_g5/poprawki/skrypty/c8_ref.py`, wyniki w `reports/etap2/audyt_g5/poprawki/k8_ref/`.

## Układ

| run | plany (seed `plans.py` i punktów estymacji) | seed MATSim | tło / ciężkie (25%) | nogi car |
|---|---|---|---|---|
| `output/g5r6_25pct_s4711` | 4711 (`plans_g5r6_25pct`, macierze `r6b`) | 4711 | 16 439 / 5 743 | 29 660 |
| `output/g5r6_25pct_s1` | 4711 | 1 | jw. | 29 660 |
| `output/g5r6_25pct_s2` | 4711 | 2 | jw. | 29 660 |
| `output/g5r6p1_25pct_s4711` | **1** (`plans_g5r6p1_25pct`, macierze `r6b_p1`) | 4711 | 18 643 / 5 647 | 31 768 |
| `output/g5r6p2_25pct_s4711` | **2** (`plans_g5r6p2_25pct`, macierze `r6b_p2`) | 4711 | 16 298 / 5 581 | 29 357 |

- Seed planów zmienia losowanie budynków (domy, praca, końce tła), godzin i zaokrągleń próbki. Zmienia też **20 punktów na gminę w estymacji O-D** (`background_od.py seed=`, decyzja: tak, bo to element tej samej losowości, I3). Estymacja dla seedów 1 i 2 zostaje ta sama (R1 z planów seed 4711; ZAŁOŻENIE: model pracujących różni się między seedami planów o setki poj./dobę, por. R1 po K1). Wszystkie macierze przechodzą `od_warnings.py` (`k8_ref/warn_p*.log`).
- 25%, 100 iteracji, 5 runów równolegle (THREADS 2, XMX 3g, ok. 1 GB RAM na run). Czas podany przed startem: 40–50 min. Faktycznie **23 min** (16:13–16:36).
- Testy: 5 × `check_events.py` (nogi = oczekiwane, 0 stuck), 5 × inwarianty (`c8_invariants.log`), 0 przepełnionych linków we wszystkich runach.

## Rozrzut per odcinek: (max − min) / średnia, 15 odcinków dopasowania

| | seedy MATSim: mediana | maks. | seedy planów: mediana | maks. |
|---|---|---|---|---|
| lekkie | **0,4%** | 1,8% (91123) | **9,3%** | 40,7% (91123) |
| ciężkie | **0,1%** | 8,1% (10044) | **11,8%** | 47,1% (91115) |
| Objazdowa 91124 (kontrolny), lekkie / ciężkie | 0,3% / 0,5% | | 18,4% / 16,2% | |
| Bitwy 91866 (kontrolny), lekkie / ciężkie | 1,3% / 2,2% | | 17,6% / 39,1% | |

Wykres: `k8_ref/c8_spread.png`. **Losowanie planów i punktów estymacji daje 20–100× większy rozrzut niż losowość MATSim.** Rozrzut „3 seedów” z R3 (mediana 0,6%) mierzył tylko replanning (potwierdzenie audytu I3).

## Wyniki względem GPR (5 runów: mediana, min–maks.)

| | lekkie | ciężkie |
|---|---|---|
| A1 (3 odcinki) | **99%** (98–99%) | **101%** (99–101%) |
| DK w Kutnie (3) | **105%** (104–113%) | **68%** (67–71%) |
| DK pozostałe | 82% (80–90%) | 83% (76–83%) |
| DW | 60% (60–63%) | 75% (74–83%) |
| 15 odcinków w ±15% | **12/15** (11–13) | **12/15** (12–15) |
| mediana odchyłki | 6,0% (5,3–6,5%) | 2,9% (2,6–4,6%) |
| Objazdowa (kontrolny) | 128% (127–153%) | 35% (35–41%) |
| Bitwy pod Kutnem (kontrolny) | 78% (77–91%) | 55% (53–80%) |

Opóźnienie dobowe (I1, poj.-h próbki): seedy MATSim 238,7 / 241,6 / 242,7 (rozrzut 1,7%), seedy planów 242,7 / 298,2 / 248,4 (rozrzut 22%). Run p1 ma o 13% więcej tła lekkiego (estymacja z innymi punktami gmin daje 74 573 zamiast 65 755 podróży/dobę). Udział czasu w opóźnieniu w oknie 6–9 (`queues.py`): 3,4–4,3%.

## Wnioski

1. Wyniki na A1 są stabilne na wszystkich 5 runach (98–101%). Zgodność A1 dla obu klas jest więc wynikiem bazy R6, a nie przypadkiem seeda.
2. Odcinki w mieście i DW zależą od seeda planów o ±10–20 pp. Różnice wariantów na pojedynczych odcinkach mniejsze niż ok. 20 pp **nie są wynikiem**. Dotyczy to wstecz także decyzji R4 vs R5 (Objazdowa 132% vs 148%, różnica 16 pp, czyli mniej niż rozrzut seedów planów na tym odcinku, 25 pp): audyt I2 słusznie uznał „przeuczenie” za nadinterpretację.
3. Liczba podróży tła zależy od wyboru 20 punktów na gminę w estymacji (−1% … +13%). Większe K zmniejszyłoby tę losowość. To kandydat do poprawki metody (lista otwarta), nie do tego kroku.
4. Referencja R6: **mediana z 5 runów** i przedział min–maks. jak w tabeli. Do porównań wariantów używać przedziału z seedów planów, nie z seedów MATSim.
