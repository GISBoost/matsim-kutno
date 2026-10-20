# Krok 7 (I2): uczciwy opis walidacji

Data: 2026-10-18. Ustalenie: `audyt_g5.md` I2. Decyzja: D21 (pkt I2).

## Zmiany w opisach (adnotacje, bez kasowania historii)

- `reports/etap2/g5_kalibracja/g5_r3.md` i `g5_r4_vs_r5_decyzja.md`: na początku dopisana ramka „Audyt I2”. Objazdowa 91124 i Bitwy pod Kutnem 91866 to **odcinki kontrolne użyte w wyborze wariantu** (W2, wyłączenie liczników lokalnych, R4 vs R5), a nie walidacja niezależna. W decyzji R4/R5 przy pkt 1 dopisałem, że „przeuczenie” to nadinterpretacja (2 odcinki, 1 seed). Poparte jest tylko „R5 gorszy na Objazdowej”.
- `docs/projekt/DECISIONS.md` D19 i D20: adnotacje kursywą przy „walidacja poza próbą” i „test niezależny”.
- `docs/projekt/ROADMAP.md`: G5 opisane jako kalibracja z odcinkami kontrolnymi (przy aktualizacji po kroku 8).
- Raporty kroków 3–6 nazywają 91124 i 91866 „odcinkami kontrolnymi”. W `g5_baseline.py` i `background_od.py` zostaje dawna nazwa zmiennej i klucza JSON (`walidacja_poza_proba`), bo zmiana złamałaby porównania ze starymi wynikami.

## Niezależna walidacja spoza GPR: co jest w pobranych danych

Przejrzałem `data/raw/g5/` i `docs/ZRODLA.md` §5 (bez nowych pobrań poza instrukcją GPR z kroku 9, 5,5 MB):

| źródło | czy niezależne od dopasowania | wynik |
|---|---|---|
| SCPR 30025 Dzięgielewo (DK92, pikieta 332,310, za Kłodawą, poza siecią): SDRR 2025 4 618, dni robocze ok. 4,8–5,4 tys. poj./dobę (R03_01) | częściowo: ta sama droga ma dopasowany licznik GPR 91121, a między stacją a granicą sieci leży Kłodawa | **R6a: 5 196 poj./dobę** na DK92 przy wjeździe zach. (link `3021014880013f/r`, wszystkie klasy, × 4). Rząd wielkości zgodny (+0–8% względem dni roboczych), 91121 w modelu 4 384 (cel 4 739) |
| SCPR 14005 Lisica (DK60 N) | nie: to ten sam pomiar co GPR 11104, od kroku 3 cel dopasowania; profil godzinowy Lisicy jest wejściem tła (D19/K3-2) | brak testu |
| GUS: macierz dostępności czasowej gmin (`gus_vs_siec*.csv`) | tak, inne zjawisko (czasy, nie natężenia) | `g5_czasy_pce.md`: czasy z gmin względem GUS, mediana 0,87 (R3). Do powtórzenia na bazie R6 przy kalibracji czasów (ROADMAP §4) |
| liczniki lokalne 10045, 91892, 91119 | nie w pełni: wyłączone z dopasowania na podstawie wyniku na Objazdowej (D19) | raportowane osobno; w R6a 17–24% (znana rozbieżność, ruch lokalny i DK91d) |
| pomiary miejskie (UM, ZDP, ZDW) | – | **brak w danych**; trzeba je pozyskać od zarządców (`docs/research/G5_walidacja.md` §2, pkt 4 listy otwartej) |

Wniosek: model ma dziś **jeden** częściowo niezależny test natężeń (SCPR 30025, rząd wielkości) i niezależny test czasów (GUS). Odcinki w Kutnie są kontrolne. Twierdzenia o zgodności w mieście formułuję na poziomie „zgodność na odcinkach kontrolnych”, a nie „walidacja”.
