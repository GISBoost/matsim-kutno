# Krok 3 etapu 3: atrybuty osób (stan roboczy, D30 czeka na decyzję o grupie 65+)

Data: 2026-10-25. Kod: `pipeline/attributes.py`, `pipeline/plans.py` (`attributes = on|off`), config `[plans]`. Research: [G_atrybuty_osob.md](../../../docs/research/G_atrybuty_osob.md). Wykres: [atrybuty.png](atrybuty.png). Liczby: [atrybuty.json](atrybuty.json).

## Co zrobiono
- Dane: BDL P4181 (NSP 2021, wiek pojedynczymi rocznikami × płeć: Kutno, Łódzkie, Polska; sumy zgodne z plikiem obwodowym: Kutno 42 255, rozkład 10-letnich grup identyczny), CEPiK 2019 (prawa jazdy wg płci i 6 grup wieku), Eurostat `demo_pjan` 2019 (wariant mianownika). Pobrane do `data/raw/g_atrybuty/`, wpisy w `data/manifest.csv`.
- Udział prawa jazdy: r = CEPiK / populacja Polski NSP 2021 (baza; wariant Eurostat 1.01.2019), ograniczony do 0,98, przesunięty w skali logit (θ = 0,087), by przy strukturze wieku Łódzkiego udział A lub B wśród 6+ = 60,6% (GUS Mobilność 2024, Tabl. 5 / 3).
- Wiek i płeć pracujących: populacja Kutna (obwód: 10-letnie grupy BREC skalują rozkład gminy) × wskaźnik zatrudnienia miast Polski wg płci i wieku (NSP 2021, rynek pracy TABL. 1) × P(licencja).
- `carAvail` w pełnej populacji: bez prawa jazdy never, z prawem jazdy always z p = 958 925 aut / 1 314 406 posiadaczy = 0,7296 (łódzkie, GUS Mobilność 2024; ZAŁOŻENIE: jedno auto = jeden posiadacz), inaczej sometimes. Wariant `all_licence` (p = 1).
- Obecni agenci (jadący autem): `license=yes`; `carAvail` always z p = 0,925, reszta sometimes. Powód: jadących autem jest 59,3% pracujących (0,64 × (1 − 0,073)), a z `always` jest tylko 53,8% pracujących, więc ok. 5,5 p.p. jadących musi być w kategorii sometimes (test w kodzie: pracujących z prawem jazdy 74,1% ≥ 59,3%). Wiek ∝ populacja × zatrudnienie × P(licencja): mediana 43 lata, 58% mężczyzn.
- Pełna populacja Kutna: `scenarios/kutno/demand/population_kutno.csv` (42 255 os.: obwód, wiek, płeć, pracujący = 17 255 wg D17 z wagą zatrudnienia, license, carAvail). Piramida wieku zgodna z BDL (odchylenie 0,7 pp, losowanie), 46,4% mężczyzn (BDL 46,6%).

## Wyniki (Kutno, baza `nsp2021/cars_per_licence`)
- Prawo jazdy 18+: 67,7%; always 18+: 49,4%; pracujący: licencja 74,1%, always 53,8%.
- Warianty (`atrybuty.json`): mianownik Eurostat 2019 daje różnicę 0,2 pp (licencja 18+ 67,8%); `all_licence`: always 18+ 67,7%, pracujący always 74,1%.
- Kontrola krajowa: iloraz CEPiK / NSP 2021 daje 60,3% dla 6+, GUS (A lub B) 62,5%; rejestr nie jest więc zawyżony ogółem, ale jest w starszych grupach.

## Test braku wpływu na symulację (GitHub Actions, run 40189940976)
Plany r91 vs r91a (te same plany + atrybuty), seed 4711, 25%, 50 iteracji, 2 wątki. Plany bez atrybutów po usunięciu czterech atrybutów są identyczne z R9.1 (sha256 `89c5ff14…`), `attributes=off` odtwarza R9.1 bajt w bajt.
- **Identyczne** skróty sha256: `output_trips`, `output_legs`, `output_links` (natężenia) i `scorestats`.
- Skrót strumienia zdarzeń różny (`5adccbda…` vs `74ff1c4b…`). Przy tym samym wyniku tras, nóg, natężeń i wyniku funkcji celu najbardziej prawdopodobna przyczyna to kolejność równoczesnych zdarzeń przy 2 wątkach (znana własność: wątki zmieniają kolejność, ERRORS/CLAUDE.md), ale tego nie rozstrzygnąłem (zdarzeń nie ma w artefaktach). Wniosek: atrybuty nie zmieniają zachowania symulacji na poziomie podróży i natężeń.

## Znane ograniczenia
- **Grupa 65+ w CEPiK.** Mężczyźni 65+: 2 951 870 praw jazdy na 2 830 183 osób (iloraz 1,04; z populacją 2019: 1,11). Rejestr zawiera zmarłych i wyjechanych, a rośnie z wiekiem. Przy ograniczeniu 0,98 mężczyźni 65+ mają 98% (za dużo), kobiety 65+ 23%. W Kutnie prawo jazdy 65–74: 51,8%, 75+: 47,9%. Wpływ na obecnych agentów znikomy (pracujących 65+ jest mało), na pełną populację (kroki 4 i 6) istotny. Decyzja czeka na użytkownika (D30).
- Prawo jazdy A lub B w GUS vs wszystkie kategorie w CEPiK; grupy CEPiK 6 zamiast pojedynczych roczników; 65+ jedna grupa.
- Dostęp do auta: jedno auto = jeden posiadacz prawa jazdy (brak danych o gospodarstwach).
- Pracujący >75 lat: wskaźnik zatrudnienia 2,4% dla całej grupy 75+, więc wśród agentów trafiają się osoby w wieku do 90 lat (min. 18, maks. 90).
- Wiek przyjeżdżających (`commuter`) z rozkładu kutnowskiego (brak danych o gminach źródłowych).

## Odtworzenie
```
uv run python -W ignore pipeline/attributes.py              # licence_rates.csv, population_kutno.csv, atrybuty.json
uv run python -W ignore reports/etap3/g_atrybuty/atrybuty_wykres.py
uv run python -W ignore pipeline/plans.py <out> 0.25        # attributes=on (domyślnie); attributes=off odtwarza R9.1
```
