# Poprawki po audycie G5: podsumowanie (D21, kroki 1–9)

Data: 2026-10-18. Audyt: `reports/etap2/audyt_g5/audyt_g5.md`. Plan i statusy: `reports/etap2/audyt_g5/plan_poprawek.md`. Raporty kroków: `poprawki/k3…k9*.md`, K1/K2 w `k1/`, `k2/`.

## Przed audytem → po poprawkach

Cel GPR dnia roboczego ze strukturą SDRDR (K2) i kierunkami z D1/D2. R4 = dawna baza (1 seed) przeliczona względem tego samego celu. R6 = nowa baza, mediana z 5 runów (min–maks.).

| | R4 (przed) | **R6 (po)** |
|---|---|---|
| lekkie: A1 | 115% (raport R4: 99%, zły cel) | **99%** (98–99%) |
| lekkie: DK w Kutnie | 112% | **105%** (104–113%) |
| lekkie: odcinki dopasowania w ±15% | 9/15 | **12/15** (11–13) |
| ciężkie: A1 | 69% (raport: 100%) | **101%** (99–101%) |
| ciężkie: DK w Kutnie | 70% | **68%** (67–71%) |
| ciężkie: odcinki w ±15% | 5/15 | **12/15** (12–15) |
| opóźnienie dobowe [poj.-h próbki] | 820 (raport) → 540 (I1) | **243** (239–298) |
| przepełnione linki | 0 | 0 |
| Objazdowa 91124 (kontrolny), lekkie / ciężkie | 137% / 61% | 128% (127–153%) / 35% (35–41%) |
| Bitwy pod Kutnem 91866 (kontrolny), lekkie / ciężkie | 90% / 60% | 78% (77–91%) / 55% (53–80%) |
| fantom Dąbrowice ↔ Krośniewice [podróży/dobę, lekkie] | 24 041 | 147 |
| tło lekkie / ciężkie [podróży/dobę, 100%] | 85 203 / 25 312 | 65 755 / 22 972 |
| końce ciężkich w budynkach mieszkalnych i gospodarczych | 50,6% | 0,1% |
| rozrzut wyników per odcinek | „0,6%” (tylko seedy MATSim) | seedy MATSim 0,1–0,4%, **seedy planów 9–12%** (mediana) |

„15 odcinków” to 14 dawnych odcinków dopasowania i nowy 11104 (DK60 Gostynin). Odcinki 91124 i 91866 są kontrolne (użyte w wyborze wariantów), a nie niezależne (I2).

## Nowa baza R6

| co | plik |
|---|---|
| strefy graniczne | `scenarios/kutno/demand/border_links.csv` (33 + 33 linki), `border_zones.csv` (11 + 11 stref per droga) |
| cel GPR | `scenarios/kutno/validation/gpr_linki.csv` (struktura `*_dr`, kierunki wg pikietażu, cel 11104) |
| macierze O-D | `scenarios/kutno/demand/background_od_r6b_lcv_gpr.csv`, `background_od_r6b_heavy_gpr.csv` (seedy planów: `r6b_p1_*`, `r6b_p2_*`) |
| model pracujących (wejście estymacji) | `output/g5r1k1_25pct_s{4711,1,2}`, plany `plans_g5r1k1_25pct.xml.gz` |
| plany i pojazdy | `scenarios/kutno/plans_g5r6_{10,25,100}pct.xml.gz` + `_vehicles.xml.gz` (z `config/kutno.toml`) |
| configi | `scenarios/kutno/config_{10,25,100}pct.xml` (plany i pojazdy bazy; run bez nadpisań) |
| runy referencyjne | `output/g5r6_25pct_s{4711,1,2}`, `output/g5r6p{1,2}_25pct_s4711` |
| raporty | `reports/etap2/g5_kalibracja/g5_r6.md`, `g5_r6_ref.md` |
| wariant bez D1/D2 | R6a: `background_od_r6_*_gpr.csv`, `output/g5r6a_25pct_s4711` |

Nowe narzędzia: `pipeline/border_zones.py` (strefy), `pipeline/od_warnings.py` (sygnały ostrzegawcze macierzy, kod 1 przy przekroczeniu). Kontrole niezależne w `poprawki/skrypty/c3…c8*.py`.

## ZAŁOŻENIA dodane w D21

1. Ślepy koniec drogi wjazdowej to granica sieci (K1).
2. DW: cel dnia roboczego = SDRR ze strukturą SDRR (K2).
3. Waga a priori strefy granicznej = natężenie klasy w najbliższym punkcie GPR tej drogi, oba kierunki, promień 15 km (I4). Strefa = link zewnętrzny łańcucha.
4. Cel 11104 przypisany jawnie do linków DK60 N, udział kierunku z GPR (I4, D2).
5. Progi sygnałów ostrzegawczych: S1 ≤ 10× gęstości Kutna, S2 ≤ 35% km tła po drogach bez licznika, S3 ≤ 25% końców ciężkich w budynkach mieszkalnych i gospodarczych, S4 ≤ 500 podróży w trójce Dąbrowice/Krośniewice (krok 4).
6. Końce ciężkich w budynkach pracy (`heavy_ends = "work"`), wariant `all` do porównań (krok 4).
7. Czas swobodny = floor(length / v) + 1 s (I1; reguła QSim, sprawdzona na danych, nie założenie).
8. GPR 2025 ma tę samą konwencję kierunków co instrukcja GPR 2020 (P = rosnący pikietaż) (D1/D2).
9. Estymacja dla seedów planów z modelu pracujących seedu 4711 (I3).
10. Ciągniki rolnicze bez osobnego typu (0,42% celu ciężkich); typ `ciezki` 15 m × 2,5 m (QSim tego nie używa) (D9).

## Pomyłki wyłapane w trakcie (wpisy w raportach kroków)

- Kontrola I4 brała najbliższy punkt z pełnego wykazu GDDKiA (A1 płd. → 91822, za węzłem Piątek). Poprawiona na odcinek wg opisu „od–do”. Pipeline wybierał dobrze (91821).
- Wariant „cel GPR na strefach granicznych” (krok 4) dał nowy fantom gmin (6 370 podróży/dobę) i przekroczył progi S2/S4. Odrzucony.
- Pierwszy test sha256 długości pojazdu (D9) był fałszywym sygnałem: eventy różnią się kolejnością zapisu między identycznymi runami (4 wątki). Porównanie zrobione na natężeniach i opóźnieniach.

## Co zostało otwarte

1. **Bilans stref DK91 (płn.-zach. 4,3×, płd.-zach. 0,16× GPR odcinka) i DK92 wsch. (0,29×):** te odcinki GPR leżą poza siecią. Rozwiązania: wariant pełny K1 (sieć z PBF wielkopolskie + mazowieckie) albo struktura relacji na DK91d (liczniki 91892, 91119 są wyłączone z dopasowania od R3).
2. **Liczniki lokalne** 10045 (Żychlin), 91892 i 91119 (DK91d Krośniewice): 14–24% GPR. Brakuje ruchu lokalnego i innych celów podróży (poza MVP).
3. **Podział Objazdowa / Bitwy (K5)** zostaje: 128% / 78% lekkich, a GEH Objazdowej w szczycie 6,7. Ciężkie na Objazdowej 35% po przeniesieniu końców ciężkich do budynków pracy.
4. **Losowość estymacji:** 20 punktów na gminę daje −1% … +13% podróży tła między seedami. Większe K albo średnia z kilku seedów estymacji to kandydat do poprawki metody.
5. **Brak niezależnej walidacji w mieście:** tylko SCPR 30025 (częściowo niezależny) i czasy GUS. Pomiary miejskie trzeba pozyskać od zarządców.
6. Raporty sprzed G5 (F5/F6, R3 MVP, D16, G2) podają opóźnienia starą definicją (ok. +0,5 s na przejazd linku).
7. Kalibracja czasów i prędkości (TomTom/HERE) zgodnie z ROADMAP §4: teraz możliwa na bazie R6, wymaga decyzji.
