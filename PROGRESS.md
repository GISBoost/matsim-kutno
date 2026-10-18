# PROGRESS

## 2026-10-16 — specyfikacja
- Folder uporządkowany, git zainicjowany (oryginalny stan w pierwszym commicie).
- Weryfikacja raportów AI: `FACT_CHECK.md` (23 twierdzenia + sprzeczności).
- Konsultacja: decyzje D1–D12 w `DECISIONS.md`.
- `CLAUDE.md`, `TASKS.md` (F0–F6).
- Kod: brak. Symulacja: nieuruchamiana.
- R1 (2026-10-16): przegląd źródeł godzin wyjazdu/czasu pracy → `docs/research/R1_godziny.md`; rekomendacja: GBR Gdańsk 2022 Rys. 46 (wykres 1 h), brak liczbowego rozkładu 15–30 min.

## 2026-10-16 — F0 zaliczona
- `matsim/` = matsim-example-project @ 74d23af (MATSim 2026.0), build `mvnw` OK (3:47 min), Java 25.
- Dowód: `equil` 1 iteracja → `reports/etap1_mvp/f0_env/f0_equil_events.json` `ok: true` (201 nóg car, 0 stuck). Szczegóły i nowe gotchas: `reports/etap1_mvp/f0_env/f0_env.md`.
- `.venv` (uv, Py 3.12), `data/manifest.csv` (5 plików, sumy SHA-256 zweryfikowane).

## 2026-10-16 — F1 zaliczona
- `scenarios/smoke/` (10 agentów, EPSG:2180): 20 nóg car, 0 stuck, współrzędne bez zamiany osi. Dowód: `reports/etap1_mvp/f1_smoke/f1_smoke.md`, `reports/etap1_mvp/f1_smoke/f1_smoke_events.json`.
- Scenariusz zostaje testem regresyjnym.

## 2026-10-16 — F2: topologia zaliczona, prędkości do decyzji
- Sieć powiat + 3 km: 4 453 węzły, 10 296 linków, SCC 100%, 90/90 tras testowych. Dowód: `reports/etap1_mvp/f2_network/f2_network.md`, `.json`, `.png`.
- Otwarte: domyślne prędkości Supersonic (15 km/h na ~3 000 km dróg lokalnych), decyzja użytkownika.
- Wizualizacje wsteczne: `reports/etap1_mvp/f0_env/f0_equil.png`, `reports/etap1_mvp/f1_smoke/f1_smoke.png` (`pipeline/plot_run.py`). Regresja smoke po przebudowie jara: ok.
- F2 zamknięta po D13 (limity ustawowe × 0,8): centrum → skraje powiatu 22–35 min, 90/90 tras, regresja ok.

## 2026-10-16 — F3 zaliczona
- Mieszkańcy pracujący w Kutnie 17 546 (bazowy) / 16 167 (niski) + 8 186 przyjeżdżających = 25 732 / 24 353 agentów przy 100%. Dowód: `reports/etap1_mvp/f3_demand/f3_demand.md`, `.json`, `.png`.
- Złączenie obwodów 232/232 (reguła rejon × 10 + nr). Otwarte do F4: kierunek wjazdu dla 1 157 osób spoza łódzkiego.
- Poprawka F2 (zgłoszenie użytkownika): A1 ucinana przez NetworkCleaner na granicy. Zawrotki na granicy → motorway 87,8 km (było 18). `reports/etap1_mvp/f2_network/f2_network.md`.

## 2026-10-16 — F4 zaliczona (test automatyczny), czeka na QGIS
- `plans.xml.gz` 10% bazowy: 2 573 osoby (1 762 mieszkańców, 605 z powiatu, 206 na wjazdach), łańcuch h-car-w-car-h 100%, sha256 powtarzalny. Dowód: `reports/etap1_mvp/f4_plans/f4_plans.md`, `.json`, `.png`.
- Kierunek wjazdu spoza łódzkiego rozwiązany krajowymi rejonami BREC 2021 (nowe pobranie 124 MB, manifest).
- Godziny nadal ZAŁOŻENIE (07:00 / 8 h), decyzja D10 otwarta.

## 2026-10-16 — F5 zaliczona (run 10%)
- D14: godziny wyjazdu z GBR Gdańsk 2022 Rys. 46 (punkty wektorowe PDF), plans F4 przegenerowane (sha256 `525ed292…`, test F4 ok).
- Run 10%, 20 iteracji, 2,5 min: 5 146 nóg car = 2N, 0 stuck. Czas podróży mediana: mieszkańcy 17,3 min, przyjeżdżający 25,6 min. Kongestia 624 poj.-h, wąskie gardło: ciąg primary SE od centrum. Dowód: `reports/etap1_mvp/f5_run_10pct/f5_run.md`, `reports/etap1_mvp/f5_run_10pct/f5_events.json`, `reports/etap1_mvp/f5_run_10pct/f5_run.png`, `reports/etap1_mvp/f5_run_10pct/f5_delay.png`.

## 2026-10-16 — F5: sprawdzenie wąskiego gardła
- Główne wąskie gardło F5 to ul. Sklęczkowska (DK92), zwężenie z 2 do 1 pasa w kierunku NE. Rano popyt wynosi około 1 700 poj./h przy przepustowości 1 500. Atrybuty sieci zgadzają się z OSM, więc przyczyną jest popyt (D6/D7), a nie błąd sieci. `reports/etap1_mvp/f5_run_10pct/f5_run.md`.

## 2026-10-16 — F6 zaliczona (100%)
- 25 732 osoby, 51 464 nogi car = 2N, 0 stuck, 4 min 9 s na 20 iteracji, RAM maks. około 1 GB. Rozkłady czasu podróży zgodne z F5 (mediana 16,8 vs 17,3 min dla mieszkańców). Kongestia 6 830 poj.-h: DK92 i ulice lokalne do wschodniej strefy pracy. Dowód: `reports/etap1_mvp/f6_run_100pct/f6_run.md`, `reports/etap1_mvp/f6_run_100pct/f6_events.json`, `reports/etap1_mvp/f6_run_100pct/f6_compare.png`, `reports/etap1_mvp/f6_run_100pct/f6_delay.png`.
- MVP (F0–F6) technicznie zamknięte. Wyniki nie są prognozą ruchu (D2, D6).

## 2026-10-16 — R3: naprawy techniczne (częściowo policzone, przerwane przez użytkownika)
- W kodzie, plany 10/25/100% zwalidowane:
  - E1: start z wjazdu później o dojazd do granicy (mediana 13–14 min);
  - E5: aktywności przypięte do sieci bez motorway/trunk/łącznic (0 naruszeń);
  - poprawka OSM `building=no` (plac komisu był największym miejscem pracy);
  - `qsim.endTime` 48 h;
  - SimWrapper włączony (atrybut `subpopulation`);
  - `check_events.py` liczy `stuckAndAbort`;
  - skrypty `convergence.py`, `select_link.py`.
- MATSim 2026 odrzuca storage ≠ flow, więc E3 z R3 wycofane (`reports/etap1_mvp/r3_ocena/testy/r3_storage_factor_rejected.log`).
- **Policzony tylko 25%, seed 4711, 100 iteracji:**
  - 12 866 nóg car = 2N, 0 stuck, 13 min;
  - czas podróży: mediana 15,5 / 24,1 min (mieszkańcy / przyjeżdżający), p90 35,0 / 36,8;
  - opóźnienie 1 130 poj.-h;
  - wąskie gardło DK92 Sklęczkowska (zwężenie do 1 pasa) z kolejką cofającą się na odcinek 6 000 poj./h;
  - select-link: 38% agentów jedzie tym odcinkiem.
  - `reports/r3_25pct_*`, `reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_compare.*`.
- **Uzupełnione 2026-10-17:** seedy 1 i 2, zbieżność i porównanie seedów, raport `reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct.md`.
- Lekcje z błędów tej sesji: `ERRORS.md` i reguły 7–11 w Workflow `CLAUDE.md`.

## 2026-10-17: R3, wyniki z 25% (3 seedy, 100 iteracji)

- Seedy 1 i 2 liczone równolegle (po 4 wątki, 13 min). Liczba wątków QSim nie skraca runu. Wyniki przy 4 i 8 wątkach są identyczne, przy 1 wątku się różnią.
- Wszystkie 3 seedy: 12 866 nóg car, 0 stuck (`reports/r3_25pct_s*_events.json`).
- GEH < 5 w szczycie 7–8 (natężenia przeskalowane do 100%): 98,9–99,5% linków. Mediany czasów różnią się o ≤ 0,4 min, suma opóźnień o 11%.
- Raport: `reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct.md`. Mapy są teraz w ciemnym motywie (prośba użytkownika).

## 2026-10-17: D16, przyjeżdżający spoza powiatu

- A: start z wjazdu = godzina z profilu GBR (bez doliczania dojazdu). B: gminy dalej niż 100 km od wjazdu pominięte (12 gmin, 47 osób w 100%).
- Plany 10/25/100%: walidacja ok, sha256 powtarzalny (`reports/etap1_mvp/d16_przyjezdzajacy/plans_*.json`).
- Run 25%, 3 seedy równolegle (14 min): 12 842 nóg car, 0 stuck. Wskaźniki zbiorcze bez zmian poza rozrzutem seedów. Raport: `reports/etap1_mvp/d16_przyjezdzajacy/d16_przyjezdzajacy.md`.
- Porządki: `reports/` w folderach faz, spis w `reports/README.md`. 3 seedy 10% vs 25%: `reports/etap1_mvp/r3_ocena/r3_10_vs_25pct.md`.

## 2026-10-17: G2 / D17, liczba miejsc pracy i wyjeżdżający

- D17 w `DECISIONS.md`: B (rejestr P4507) jako baza, C (skalowanie do P4508 = 17 486) jako wariant wrażliwości, wyjeżdżający O1 z odcięciem > 100 km, rok 2024.
- `demand.py`: kolumna `work_in_kutno_reg` (14 586 w 100%), `outbound_by_gmina.csv` (83 gminy, 2 669 os.). `plans.py`: rodzaj `outbound` (dom w budynku w Kutnie, praca w budynku gminy powiatu albo na linku wyjazdowym; 31 linków wyjazdowych), `jobs_total` do wariantu C (nadpisanie z linii poleceń `jobs_total=17486`).
- Odcięte > 100 km: 30 gmin, 235 os. w 100% (47 przyjeżdżających, 188 wyjeżdżających). Warszawa (457) zostaje, wyjazd na A1.
- Plany 10%: B 2 521 os. (1 465 mieszk., 808 przyjeżdż., 248 wyjeżdż.), C 1 997 os. (1 133 / 616 / 248). Walidacja ok, sha256 powtarzalny (`reports/etap2/g2_miejsca_pracy/{B,C}/plans_10pct_plans.json`). Pierwsza wersja nie przeszła walidacji (ERRORS 14).
- Runy 10% × 3 seedy dla B i C (6 równolegle, po 2 wątki, 11 min): nogi car zgodne z planami (5 042 / 3 994), 0 stuck. Opóźnienia [poj.-h próbki]: B 370–405, C 146–166, wobec 540–567 w starych runach 10% (A). GEH < 5 w szczycie między seedami: B 93–95%, C 96%. Raport: `reports/etap2/g2_miejsca_pracy/g2_miejsca_pracy.md`.
- B na 25% × 3 seedy (nowe wyniki referencyjne, domyślne `plans_25pct.xml.gz` z D17/B): 6 302 osoby, 12 604 nóg car, 0 stuck. Opóźnienia 754–777 poj.-h próbki (D16: 1 076–1 091, −30%), GEH < 5 w szczycie między seedami 99,4–99,9%. `reports/etap2/g2_miejsca_pracy/B_25pct/`.

## 2026-10-17: kolejki z G6, poprawka D18

- `pipeline/queues.py`: diagnoza na eventach (przejazdy linków, przyczyna: capacity / spillback / węzeł, przepełnienie). Run B 25%: 26% czasu pojazdów w opóźnieniu (zgodne z 26% klatek w G6). 51% opóźnień na ulicach tertiary z 600 poj./h/pas, 44% to kolejka spod zwężenia Sklęczkowskiej (2 → 1 pas).
- Artefakt: `stuckTime` 10 s → 82 pojazdy na linku o pojemności 1,2. Test na tych samych trasach (stuckTime 10/30/60/300, kinematicWaves 30/300): przy queue suma opóźnień ±7%, przy kinematicWaves +56%, a z 300 s gridlock.
- D18: stuckTime 30 (Berlin v6.3, Kelheim v3.1). Run 25% × 3 seedy: 12 604 nóg car, 0 stuck, opóźnienia 735–854 poj.-h próbki, przepełnione linki 4–7 zamiast 13, GEH < 5 w szczycie 98,8–100%. Raport: `reports/etap2/g6_kolejki/g6_kolejki.md`. Nowe wyniki referencyjne: `reports/etap2/g6_kolejki/d18_25pct/`.

## 2026-10-17: G5, punkt startowy i plan kalibracji

- `pipeline/g5_baseline.py`: model D18 (25%, 3 seedy) vs GPR 2025 (lekkie, SDRDR, na kierunek). A1 7%, DK w Kutnie 56% (Sklęczkowska 71%, Objazdowa 65%, Bitwy pod Kutnem 28%), pozostałe DK 16%, DW 7%. `reports/etap2/g5_kalibracja/g5_0_baseline.*`.
- Plan z wariantami (K1 dojazdy autem, K2 tło, K3 profil, K4 walidacja z 3 odcinkami miejskimi poza próbą, K5 wrażliwość sieci): `docs/research/G5_plan_kalibracji.md`. Czeka na decyzje użytkownika, runów nie ma.

## 2026-10-17: G5 / D19, kroki bez MATSim i run R1

- D19: K1-1 (popyt car × 0,593), K2-2 (tło lekkie z O-D estymowanego z GPR), K3-2 (profil Lisica), K4 (3 odcinki miejskie poza próbą).
- `digitize_lisica.py`: profil godzinowy dnia roboczego (lekkie i ciężkie, sumy 100%).
- R1 (D18 + K1-1, 25% × 3 seedy): 7 478 nóg car, 0 stuck, opóźnienia 106–113 poj.-h próbki (D18: 735–854). Model / GPR: A1 3%, DK w mieście 30%.
- `background_od.py`: odcinki dopasowania ok, ale walidacja w mieście daje 140–173% GPR na Sklęczkowskiej i 155–168% na Objazdowej. Luka A1 nie rozróżnia tranzytu od relacji z Kutnem. Opcje W1–W3 w `docs/research/G5_plan_kalibracji.md` §4. Czeka na decyzję. Agentów tła jeszcze nie ma w planach.
- W2 (decyzja użytkownika): Sklęczkowska w dopasowaniu. Tło 59 879 podróży/dobę w 100% (tranzyt 21 428, granica–gmina 30 590, gmina–gmina 7 861). Walidacja poza próbą na trasach swobodnych: Objazdowa 141%, Bitwy pod Kutnem 94%. Sesja zakończona przed symulacją z tłem; dalsze kroki w `docs/research/G5_plan_kalibracji.md` §5.

## 2026-10-18: G5 / D19, run R2 (dojazdy K1-1 + tło)

- `plans.py`: agenci tła (`subpopulation=tlo`, `tlo_start`–car–`tlo_end`, O-D z `background_od_r1_w2_cap.csv`, profil Lisica). Configi: activityParams bez score i strategie dla `tlo`. `validate_plans.py`: test tła. Test 2 iteracji ok.
- R2 (25%, 1 seed): 22 448 nóg car, 0 stuck. A1 98% GPR, DK w mieście 110%, odcinki dopasowania 86%. Walidacja poza próbą: Objazdowa 131%, Bitwy pod Kutnem 90%. Opóźnienie 304 poj.-h próbki/dobę, 0 przepełnionych linków.
- Braki na DK60 Leszno, DK91d i DK92 Pomarzany (ok. 50%) widać już w iteracji 0. Estymacja O-D miała jeden węzeł na gminę, a agenci startują z budynków w całej gminie. Następny krok: incydencja ułamkowa z wielu punktów na gminę. Raport: `reports/etap2/g5_kalibracja/g5_r2.md`.

## 2026-10-18: G5 / D19, run R3 (estymacja O-D z incydencją ułamkową)

- `background_od.py`: 20 punktów na gminę, incydencja ułamkowa, krok ∝ udział, pary wewnątrzgminne; liczniki lokalne 10045, 91892 i 91119 poza dopasowaniem (test 5 wariantów offline).
- R3 (25%, 1 seed): 26 455 nóg car, 0 stuck. 14 odcinków dopasowania: 97% sumy, 13/14 w ±15% (R2: 90%, 6/14). Walidacja: Objazdowa 129%, Bitwy pod Kutnem 84% (suma obu 107%). Opóźnienie 359 poj.-h próbki. Raport: `reports/etap2/g5_kalibracja/g5_r3.md`. Opis metody: `docs/research/G5_plan_kalibracji.md` §6.

## 2026-10-18: G5 / D19, K5 wariant A i R3 na 3 seedach (wynik referencyjny)

- K5: rozbieżność Objazdowa 128% / Bitwy pod Kutnem 84% zostaje jako znana. Decyzja użytkownika: wariant A, wpis w D19. Diagnoza: `reports/etap2/g5_kalibracja/k5/k5_objazdowa.md`.
- R3 25% × 3 seedy (4711, 1, 2): każdy seed 26 455 nóg car, 0 stuck, 0 przepełnionych linków; opóźnienie 359 / 367 / 362 poj.-h próbki.
- Średnia z 3 seedów vs GPR: A1 101%, DK w Kutnie 104%, 14 odcinków dopasowania 97% (12/14 w ±15%; 10044 na granicy 85,0%), rozrzut seedów mediana 0,6%. Raport: `reports/etap2/g5_kalibracja/g5_r3.md` (sekcja „R3 na 3 seedach”).
- **Nowa referencja 25%: `output/g5r3_25pct_s{4711,1,2}`, plany `scenarios/kutno/plans_g5r3_25pct.xml.gz`.**

## 2026-10-18: G5, walidacja czasów (GUS) i źródło PCE

- Czasy: dojazdy z gmin powiatu w R3 (3 seedy, 2 691 nóg). Kongestia 1,05 × czas swobodny (p90 1,13). Run / GUS: mediana 0,87. Model jest szybszy od GUS/ORS, a ok. 1/3 różnicy wyjaśniają domyślne prędkości ORS dla dróg bez tagu maxspeed (z nimi mediana 0,84 zamiast 0,76). Skrypty: `pipeline/g5_gus_czasy_r3.py`, `pipeline/g5_gus_czasy.py ors <run>`.
- PCE: WR-D-13-01 (2023) tab. 4.3.1. Ciężarowe 2,0–3,0, dostawcze 1,0–1,5, osobno dla miasta i poza miastem. Brakujący ruch ciężki i dostawczy w pojazdach umownych: A1 104%, DK w Kutnie 82%, DW 35% ruchu lekkich.
- Raport z wariantami P1–P3 (bez wdrożenia): `reports/etap2/g5_kalibracja/g5_czasy_pce.md`. Źródła w ZRODLA §5, PDF-y w manifeście.

## 2026-10-18: G5 / D20, run R4 (dostawcze w tle lekkim i ciężkie, pce 2,5)

- Estymacja O-D `background_od.py cls=lcv|heavy`: lekkie z dostawczymi 85 203 podróży na dobę, ciężkie 25 312 (trasy z limitem 80 km/h). Plany `plans_g5r4_25pct` (+ `_vehicles.xml.gz`: pce 2,5, 80 km/h), walidator ok. Plany R3 odtworzone bit w bit (regresja).
- `qsim.linkDynamics=PassingQ` w configach (test 2 iteracji: przy FIFO osobowe jechały po A1 80 km/h za ciężarowymi).
- R4 25% 1 seed: 35 107 nóg car, 0 stuck, 0 przepełnionych linków. Opóźnienie 820 poj.-h próbki (R3: 359), po poprawce czasu swobodnego ciężarowych w `link_delay.py` i `queues.py`.
- Względem GPR: A1 99% (lekkie) i 100% (ciężkie); DK w Kutnie 108% i 83%; 14 odcinków dopasowania 10/14 i 11/14 w ±15%. Węzeł Krośniewic rozjeżdża się po kongestii: DK92 91121 i 91122 mają 150–190%, DK91d 20–46%. Raport z wariantami E1–E3: `reports/etap2/g5_kalibracja/g5_r4.md`.

## 2026-10-18: G5 / D20 E1, estymacja O-D z tras R4 i run R5

- `background_od.py routes= init= bound=`: incydencja z tras R4 i start z macierzy R4. Bez ograniczenia jedna para urosła 9× (Objazdowa 211%), więc wybrane ograniczenie 2× (test 1,5/2/3 offline).
- R5 25% 1 seed: 33 121 nóg car, 0 stuck, 1 przepełniony link. Opóźnienie 693 poj.-h próbki (R4: 820).
- Lekkie: 12/14 w ±15%, mediana odchyłki 0,4%, obwodnica Krośniewic 91122 100% (R4: 191%). Ciężkie: 10/14. Walidacja: Objazdowa 148% (lekkie) i 74% (ciężkie), Bitwy pod Kutnem 93% i 71%. Raport: `reports/etap2/g5_kalibracja/g5_r5.md`.

## 2026-10-18: G5 / D20, baza R4

- Decyzja użytkownika: R4 jest bazą, R5 wariantem wrażliwości. Uzasadnienie: `reports/etap2/g5_kalibracja/g5_r4_vs_r5_decyzja.md`. `config/kutno.toml` wskazuje macierze R4.
- Wstrzymane do czasu audytu w osobnej sesji: R4 na 3 seedach.

## 2026-10-18: audyt G5, poprawka K1 (D21)

- Audyt w osobnej sesji: `reports/etap2/audyt_g5/audyt_g5.md` (2 krytyczne, 4 istotne, 9 drobnych).
- K1: `plans.py` traktuje ślepe końce dróg wjazdowych jak granicę sieci. Skan sieci: 9 ślepych końców primary/secondary, 7 było już wjazdami, nowe są 2 (DK60 N, DK92 W). `border_links.csv` 33 + 33.
- Test: walidator planów `plans_k1_25pct` ok (sha256 powtarzalny). Diagnostyczna estymacja O-D (cel jeszcze z K2): para Dąbrowice ↔ Krośniewice 24 041 → 54 lekkich i 9 523 → 27 ciężkich na dobę, dopasowanie bez zmian 100%, tło −22% (lekkie) i −30% (ciężkie). Raport: `reports/etap2/audyt_g5/k1/k1_poprawka.md`.
- Bez runu MATSim. Baza R4 jest nieaktualna do czasu nowej estymacji po K2 i I4.

## 2026-10-18: audyt G5, poprawka K2 (D21)

- `g5_gpr.py` zapisuje strukturę rodzajową SDRDR (`<klasa>_dr`, DW: SDRR jako ZAŁOŻENIE). Na 14 odcinkach DK suma klas = SDRDR, stare kolumny `gpr_linki.csv` bez zmian. `background_od.py` i `g5_baseline.py` liczą cel z `_dr`.
- R4 vs poprawiony cel: lekkie A1 115%, DK w Kutnie 112%, 9/14; ciężkie A1 68%, DK w Kutnie 70%, 5/14; R3 A1 122%. Zgodne z audytem.
- Nowy `g5_pce.py`: tryb `sdrr` odtwarza starą `pce_wrd13_gpr.csv` bit w bit; ze strukturą SDRDR A1 173%, DK w Kutnie 99%. Raport: `reports/etap2/audyt_g5/k2/k2_poprawka.md`.
- Bez nowej estymacji i runu (czeka na I4).

## 2026-10-18: audyt G5, poprawka I4 (D21, krok 3)

- `pipeline/border_zones.py` (nowy): łańcuchy linków granicznych → 11 stref wjazdu i 11 wyjazdu per droga, id = link zewnętrzny (`border_zones.csv`). `background_od.py`: waga a priori strefy = natężenie klasy (SDRDR) w najbliższym punkcie GPR tej drogi, bez zawracania na tej samej drodze. `g5_gpr.py`: nowy cel 11104 (DK60 Kutno–Gostynin = SCPR Lisica) na wjeździe DK60 N; stare wiersze `gpr_linki.csv` bez zmian.
- Udział wag wjazdów (lekkie): DK60 płd. 29,1% → 5,9%, A1 płn. 5,5% → 24,5%, A1 razem 57%; niezależna kontrola `c3_border_weights.py` zgodna do 0,1 pp.
- Diagnostyczna estymacja (stary R1): tranzyt lekkich −39%, Objazdowa + Bitwy 117% → 99% (121% / 75%). Plany z macierzami diag.: walidator ok. Raport: `reports/etap2/audyt_g5/poprawki/k3_i4_strefy.md`.

## 2026-10-18: audyt G5, krok 4 (D21): R1 po K1, estymacja R6, sygnały ostrzegawcze

- R1 na planach po K1 (`plans_g5r1k1_25pct`, walidator ok): 3 seedy × 7 478 nóg car, 0 stuck. Zmiana tylko na wjazdach: A1 71410 568 → 72, DK60 N 11104 0 → 512 poj./dobę.
- Estymacja `background_od_r6_{lcv,heavy}_gpr.csv`: lekkie 65 905, ciężkie 22 990 podróży/dobę (R4: 85 203 i 25 312); gmina–gmina lekkie 29 954 → 8 364. Odcinki dopasowania 100%; offline Objazdowa / Bitwy: lekkie 123% / 75%, ciężkie 29% / 78%.
- Nowy `pipeline/od_warnings.py` (S1 gęstość gminy vs Kutno ≤ 10×, S2 km po drogach bez licznika ≤ 35%, S3 końce ciężkich w mieszk. + gosp. ≤ 25%, S4 trójka Dąbrowice/Krośniewice ≤ 500): R4 flagowane (S1 45×/73×, S4 24 041), R6 ok (5,1×, 30,5%, 0,0%, 142).
- `heavy_ends = "work"` (ZAŁOŻENIE, D9): końce ciężkich w budynkach pracy (było 54% w mieszkalnych i gospodarczych). Wariant z celem GPR na strefach granicznych odrzucony (S2/S4, nowy fantom gmin). Raport: `reports/etap2/audyt_g5/poprawki/k4_od.md`.

## 2026-10-18: audyt G5, krok 5 (D21/I1): opóźnienia

- `link_delay.py` i `queues.py`: czas swobodny = floor(length / v) + 1 s (najkrótszy czas QSim; w nocy 98,8% przejazdów R4 dokładnie tyle, żaden krócej, `c5_night.py`).
- Przeliczone (poj.-h próbki): R1 50,5–58,0 (było 106–113), R2 110,0 (304), R3 154,3–162,8 (359–367), R4 540,3 (820), R5 419,3 (693), D18 641–759 (735–854). R3, R4, R5 równe audytowi. R3 → R4 3,5×, R5 −22% vs R4. Noc ~0.
- Adnotacje „audyt I1” w raportach G5 i D18. Raport: `reports/etap2/audyt_g5/poprawki/k5_i1_opoznienia.md`.

## 2026-10-18: audyt G5, krok 7 (D21/I2): opis walidacji

- Objazdowa 91124 i Bitwy 91866 opisane jako odcinki kontrolne użyte w wyborze wariantu (adnotacje w `g5_r3.md`, `g5_r4_vs_r5_decyzja.md`, D19, D20).
- Niezależna walidacja w pobranych danych: tylko SCPR 30025 Dzięgielewo (DK92 za Kłodawą, częściowo niezależna): R6a 5 196 poj./dobę wobec 4,8–5,4 tys. w dni robocze. Pomiarów miejskich brak. Raport: `reports/etap2/audyt_g5/poprawki/k7_i2_walidacja.md`.

## 2026-10-18: audyt G5, krok 6 (D21/D6): baza R6, run 25%

- Configi 10/25/100% wskazują `plans_g5r6_*pct.xml.gz` i plik pojazdów (`vehiclesSource=fromVehiclesData`); `kutno.toml` wskazuje macierze `r6b` (z D1/D2). Plany 10/25/100% walidator ok, sha256 powtarzalny.
- D1/D2 rozstrzygnięte w trakcie kroku (instrukcja GPR 2020: P = rosnący pikietaż; A1 było odwrócone): estymacja `r6b`, zmiana macierzy −0,2%. Run na macierzach sprzed D1/D2 to R6a.
- R6 25% seed 4711 (`output/g5r6_25pct_s4711`): 29 660 nóg car, 0 stuck, inwarianty ok. Lekkie: A1 99%, DK w Kutnie 105%, 12/15 w ±15% (R4: 115%, 112%, 9/15). Ciężkie: A1 101%, DK w Kutnie 68%, 12/15 (R4: 69%, 70%, 5/15). Opóźnienie 243 poj.-h próbki (R4 540), 0 przepełnionych linków, korek pod Krośniewicami znika. Raport: `reports/etap2/g5_kalibracja/g5_r6.md`.

## 2026-10-18: audyt G5, krok 8 (D21/I3): referencja R6, 3 seedy MATSim + 2 seedy planów

- 5 runów 25% × 100 it. (23 min równolegle): `output/g5r6_25pct_s{4711,1,2}`, `output/g5r6p{1,2}_25pct_s4711` (seed planów i punktów estymacji `background_od.py seed=`). Każdy: nogi = oczekiwane, 0 stuck, inwarianty ok, 0 przepełnionych linków.
- Rozrzut per odcinek (mediana / maks.): seedy MATSim 0,4% / 1,8% (lekkie), seedy planów 9,3% / 40,7% (lekkie) i 11,8% / 47,1% (ciężkie). Opóźnienie 239–243 (seedy MATSim) i 243–298 poj.-h (seedy planów).
- Mediana z 5 runów: A1 99% / 101%, DK w Kutnie 105% / 68%, 12/15 w ±15% dla obu klas. Raport: `reports/etap2/g5_kalibracja/g5_r6_ref.md`.

## 2026-10-18: audyt G5, krok 9 (D21/D1–D9): drobne

- D1/D2: konwencja z instrukcji GPR 2020 (P = rosnący pikietaż); A1 było odwrócone, DK mają udziały GPR zamiast 0,5 (wdrożone w kroku 6, macierze `r6b`).
- D3: R3 to 13/14. D4: GEH Objazdowej w szczycie 6,7 (nie < 5). D5: tabele PCE odtwarzają się bit w bit. D6: krok 6. D7: okno 6–9 opisane przy liczbach. D8: `VehicleFlagEncoder.java` (main i v6.6.0 z 2021) w `data/raw/g5/ors/`, manifest, ZRODLA.
- D9: ciągniki rolnicze 0,42% celu ciężkich (pomijalne). Długość pojazdu nie wpływa na QSim (15 vs 30 m: identyczne natężenia i opóźnienia). Raport: `reports/etap2/audyt_g5/poprawki/k9_drobne.md`.

## 2026-10-18: audyt G5, poprawki zakończone (D21, kroki 1–9)

- Raport zbiorczy: `reports/etap2/audyt_g5/poprawki/podsumowanie.md` (przed → po, nowa baza R6, ZAŁOŻENIA, otwarte). Test smoke ok (20 nóg car, `reports/etap2/audyt_g5/poprawki/smoke_check.json`). CLAUDE.md i ROADMAP zaktualizowane: baza R6.

