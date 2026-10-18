# Plan poprawek po audycie G5 (D21)

Źródło: `audyt_g5.md` (2 krytyczne, 4 istotne, 9 drobnych ustaleń), kolejność z sekcji 5 audytu. Każda poprawka jest osobnym krokiem: wdrożenie → test → wpis w `PROGRESS.md` i D21 → commit → stop na decyzję użytkownika.

Stan: 2026-10-18.

| # | krok | status | wynik / raport |
|---|---|---|---|
| 1 | **K1**: strefy graniczne na ślepych końcach DK92 W i DK60 N | ✅ zrobione (902903a) | `k1/k1_poprawka.md`: fantomowa para Dąbrowice ↔ Krośniewice 24 041 → 54 podróży/dobę |
| 2 | **K2**: cel GPR ze strukturą SDRDR (DW: SDRR jako ZAŁOŻENIE), skrypt tabeli PCE | ✅ zrobione (e1d7daf) | `k2/k2_poprawka.md`: R4 lekkie A1 115%, ciężkie A1 68% (5/14) |
| 3 | **I4**: strefy graniczne zgrupowane per droga i kierunek, waga a priori z ruchu drogi (GPR/SCPR) zamiast liczby linków w węźle; sprawdzić SCPR 30025 (DK92 W) i 14005 Lisica (DK60) jako cele dla nowych wjazdów | ✅ zrobione (83582eb) | `poprawki/k3_i4_strefy.md`: 11 + 11 stref per droga, wagi z GPR (DK60 płd. 29% → 6%, A1 płn. 6% → 25%); nowy cel 11104 DK60 Gostynin; diag.: Objazdowa + Bitwy 117% → 99% |
| 4 | **Nowa estymacja O-D** lekkich i ciężkich (K1 + K2 + I4) i kontrola sygnałów ostrzegawczych macierzy: top pary vs powierzchnia budynków stref, udział km tła na drogach bez licznika, końce ciężkich w budynkach mieszkalnych i gospodarczych | ✅ zrobione (1c30876) | `poprawki/k4_od.md`: R6 lekkie 65 905, ciężkie 22 990/dobę; sygnały S1–S4 ok (R4 flagowane); ciężkie do budynków pracy; cel na strefach odrzucony |
| 5 | **I1**: `link_delay.py` z tym samym czasem swobodnym co `queues.py`; przeliczyć opóźnienia R3–R5 i D18 | ✅ zrobione (e5a55d6) | `poprawki/k5_i1_opoznienia.md`: floor(ff) + 1 s; R3 154, R4 540, R5 419 poj.-h próbki (było 359 / 820 / 693) |
| 6 | **D6**: config wskazuje plany i plik pojazdów bazy; nowe plany 25%; run 25% na 1 seedzie (ok. 20 min); porównanie z GPR (struktura SDRDR) | ✅ zrobione (110e7f2) | `g5_kalibracja/g5_r6.md`: R6 A1 99% / 101%, 12/15 i 12/15 w ±15%, 243 poj.-h; D1/D2 wdrożone przy okazji |
| 7 | **I2**: Objazdowa 91124 i Bitwy 91866 opisywane jako odcinki kontrolne użyte w wyborze wariantu, nie walidacja niezależna; szukać niezależnej walidacji spoza GPR | ✅ zrobione (9e2cef7) | `poprawki/k7_i2_walidacja.md`: odcinki kontrolne zamiast „walidacji”; SCPR 30025 jako częściowo niezależny test (R6a 5 196 vs 4,8–5,4 tys.) |
| 8 | **I3**: referencja = 3 seedy MATSim + 2 seedy planów (czas podany przed startem, możliwe > 30 min) | ✅ zrobione (791da6b) | `g5_kalibracja/g5_r6_ref.md`: rozrzut seedów planów 9–12% (mediana), MATSim 0,1–0,4%; A1 99% / 101% na wszystkich 5 runach |
| 9 | **Drobne D1–D9** przy okazji: D1/D2 kierunki A1 i udziały kierunków DK z GPR (najpierw konwencja „lewy/prawy” GDDKiA), D3 R3 to 13/14, D4 GEH w szczycie, D7 okno 6–9 w `queues.py`, D8 archiwizacja źródła ORS, D9 typ `ciezki` (długość, ciągniki 40 km/h) | ✅ zrobione (COMMIT_K9; D1/D2 w 110e7f2) | `poprawki/k9_drobne.md`: P = rosnący pikietaż (A1 odwrócone), GEH Objazdowej w szczycie 6,7, długość pojazdu bez wpływu na QSim, ciągniki 0,4% |

Do decyzji przy okazji (nie są w audycie):
- wariant pełny K1: sieć z PBF łódzkie + wielkopolskie + mazowieckie (zmienia sieć i wszystkie wejścia);
- kalibracja czasów przejazdu z TomTom/HERE: po kroku 8, bo zła macierz tła psułaby dopasowanie prędkości (nowa decyzja w `DECISIONS.md`).
