# PROGRESS

## 2026-10-16 — specyfikacja
- Folder uporządkowany, git zainicjowany (oryginalny stan w pierwszym commicie).
- Weryfikacja raportów AI: `docs/projekt/FACT_CHECK.md` (23 twierdzenia + sprzeczności).
- Konsultacja: decyzje D1–D12 w `docs/projekt/DECISIONS.md`.
- zasady projektu (plik lokalny), `docs/projekt/TASKS.md` (F0–F6).
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
- Lekcje z błędów tej sesji: `docs/projekt/ERRORS.md` i reguły 7–11 w zasadach projektu (Workflow).

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

- D17 w `docs/projekt/DECISIONS.md`: B (rejestr P4507) jako baza, C (skalowanie do P4508 = 17 486) jako wariant wrażliwości, wyjeżdżający O1 z odcięciem > 100 km, rok 2024.
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

- Raport zbiorczy: `reports/etap2/audyt_g5/poprawki/podsumowanie.md` (przed → po, nowa baza R6, ZAŁOŻENIA, otwarte). Test smoke ok (20 nóg car, `reports/etap2/audyt_g5/poprawki/smoke_check.json`). zasady projektu i ROADMAP zaktualizowane: baza R6.

## 2026-10-18: G5/D22: walidacja czasów i prędkości R6 względem TomTom (wariant A)

- Decyzja D22, wariant A (regulamin TomTom pkt 11.4, 11.6.1, 11.6.10): odpowiedzi tylko w pamięci, do repo same agregaty, bez porównania TomTom–HERE. Bez zmian modelu i bez nowych runów MATSim.
- Próbka (seed 4711): 30 par z planów R6 (r 8, c 6, o 4, t 6, h 6), 10 korytarzy GPR, 25 segmentów. `split.csv`: 1/3 każdej warstwy tylko do walidacji, zapisany przed policzeniem błędu.
- Czasy modelu: sonda po trasie modelu z czasami linków z eventów 5 runów R6. Kontrola z nogami agentów: mediana 1,000 (p5–p95 0,90–1,04, n 90).
- TomTom: 149 requestów właściwych = dry-run (2026-10-18 17:23–17:24 UTC, `departAt` wt. 20.10 07:30 / 12:30 / 15:30). Łącznie 316 z budżetu 400 (149 × 401 przez klucz w cudzysłowie, ERRORS 22). `departAt` w przyszłości daje typowy profil: wtorki 20.10 i 27.10 identyczne. Przeszłość jest przyjmowana.
- Wyniki (mediana model/TomTom; analiza | walidacja):
  - czas swobodny tras 1,18 | 1,08;
  - czas rano 1,06 | 1,02, w południe 1,04 | 1,00;
  - freespeed segmentów 0,84 | 0,87 (A1 112 vs 130 km/h, DK 72 vs 87–89). Tertiary/unclassified n = 1.
  - TomTom ma ok. 8% opóźnienia względem `noTraffic` przez cały dzień, model 1–4%. Niezależna kontrola zgodna.
- Wnioski do decyzji: factor 0,8 (D13) zaniża prędkość swobodną o ok. 15%, ale czasy w oknach zgadzają się na 0–6%, bo model nie ma opóźnień skrzyżowań. Freespeed nie ruszać bez G1, capacity nie ruszać, tertiary/unclassified nierozstrzygnięte. Wskaźnik bufora 25 m niewiarygodny przy prostych linkach (ERRORS 23).
- Raport: `reports/etap2/g5_czasy_tomtom/g5_czasy_tomtom.md`; kod: `pipeline/traffic_providers.py`, `pipeline/traffic_metrics.py`. HERE przygotowane, bez klucza.
- Uzupełnienie (prośba użytkownika): dwa ponowne przebiegi TomTom (2 × 149 requestów, łącznie 614, budżet 650) z MAE, kryterium TAG M3.1, wykresem błędów, rozrzutem prędkości i mapą próbki. Mediany, MAPE i RMSE identyczne jak w przebiegu 1.
  - MAE czasu: rano 128 s (analiza) i 93 s (walidacja); MAE prędkości segmentów 17,5 i 13,8 km/h.
  - TAG tab. 3 (15% lub 1 min, wytyczna > 85% tras): rano 48% i 77%, czyli niespełnione (TomTom historic to model dostawcy, nie pomiar).
  - Rozrzut segmentów: y = 0,972x + 17,26, R² 0,863.
  - Mapa i rozrzut per obiekt w `output/g5_czasy_tomtom/` (poza repo, D22). TAG M3.1 pobrany do `data/raw/g5/lit/` (manifest).
- Uzupełnienie 2 (pytanie użytkownika o kalibrację i walidację): przebieg 4 TomTom (149 requestów, łącznie 763, budżet 800) z metrykami w %.
  - Rano (analiza / walidacja): MAPE 17,6 / 13,3%, RMSPE 26,4 / 20,5%, %RMSE (FHWA) 15,6 / 10,7%.
  - Segmenty: MAPE 21 / 17,5%.
  - Ocena (TAG M3.1, FHWA 2010, pobrane do data/raw/g5/lit/): R6 skalibrowany tylko w popycie do GPR. Niezwalidowany wg TAG: kryterium czasów 15% lub 1 min spełnia 48–77% tras wobec wytycznej 85%, a TomTom to model dostawcy, nie pomiar.
  - Raport: g5_czasy_tomtom.md §11.

## 2026-10-18: D23 krok 1: rozszerzenie próbki tras per grupa dróg

- D23 (wariant a): `f_g` per grupa A–F, kalibrowane na zestawie analizy (plan `reports/etap2/g5_predkosci_d23/plan.md`, zaakceptowany przez użytkownika).
- `traffic_providers.py sample_d23`: 74 nowe trasy (≥ 50% długości w grupie, 3–15 km; D i F od 2 km). Każda grupa ma teraz 12 tras w analizie i 6 w walidacji. `split.csv` dopisany przed requestem, stare wiersze bez zmian.
- Czasy modelu R6 dla 114 tras (`model_times.csv`).
- Budżet zmniejszony po informacji o limicie konta (2 500/dobę): krok 1 bez requestów, D23 razem ok. 620. Skrypt ma limit `BUDGET_DAY = 2000` (doba UTC, liczona z logu).
- Raport: `reports/etap2/g5_predkosci_d23/krok1_probka.md`.

## 2026-10-18: D23 krok 2: dopasowanie f_g na zestawie analizy (TomTom)

- Narzędzia: `traffic_metrics.py` (`RouteModel`, `fit_factors`, `selftest_fit`: syntetyczne f_g odtworzone, błąd maks. 0,015) i `traffic_providers.py run tomtom --fit` (dane w pamięci, D22). Dodane `scipy` (`uv add`).
- 231 requestów (3 testowe + 228), łącznie 994. 74 trasy analizy × 3 okna (2 trasy wyłączone, start > 50 m).
- f dopasowane (przedział 90%): A 0,92 (0,82–1,01), B 1,02 (0,94–1,10), C 0,58 (0,50–0,65), D 0,77 (0,61–0,95), E 0,88 (0,73–1,06), F 0,50 (na granicy).
- Reguła z planu: C nieidentyfikowalne (11 tras < 12), D i E za szerokie, F na dolnej granicy.
- W próbie: MAPE 18,5 → 13,6%, TAG 52 → 72% tras.
- Do decyzji: C (0,8 wg reguły czy 0,58), F (0,5 czy 0,8), B (1,02 czy 1,0). Raport: `reports/etap2/g5_predkosci_d23/krok2_dopasowanie.md`.
- Decyzja użytkownika: dobrać trasy C i powtórzyć dopasowanie następnego dnia. Do tego czasu sieć bez zmian, F i B rozstrzygnąć po nowym dopasowaniu.
  - `sample_d23 C 4 2`: 6 nowych tras C (4 analiza, 2 walidacja), split przed requestem; C ma teraz 16 tras w analizie i 8 w walidacji.
  - `model_times.csv` dla 120 tras, `selftest_fit` ok. Polecenia na jutro: `krok2_dopasowanie.md` (sekcja „Jutro”).

## 2026-10-19: dokumentacja etapu 2, filmy G6, licencje (wg historii gita)

- Opisy research G2, G3, G4, R1 zaktualizowane (`docs/research/`), dodany przegląd przykładów kalibracji MATSim i `docs/ZRODLA.md`.
- G5: macierze O-D tła R4, R5 (warianty ograniczenia) i diagnostyka K1.
- G6: filmy v5–v7 w Blenderze (Workbench, klasy dróg, granica powiatu, podkład OSM, wersja pionowa), skrypty składania z lektorem i muzyką; wyniki lokalnie w `blender/g6_blender/` (poza gitem).
- Licencje: kod GPL-3.0-or-later, dane GUS CC BY 4.0, OSM ODbL (`LICENSE`, `LICENSE-DATA.md`).
- Repo: logi (`*.log`), dane TomTom i filmy poza gitem (D22, wariant A: w repo tylko metryki i raporty).

## 2026-10-20: przygotowanie do publikacji

- Historia gita przepisana: usunięte klatki PNG i `anim.mp4` z G6, materiały robocze z pracy z AI (zasady agenta, prompty, archiwum raportów innych modeli); 82 → 76 commitów, `.git` 65 → 35 MB. Kopie plików zostają lokalnie, są w `.gitignore`.
- Porządki: usunięte ścieżki lokalne z kodu i raportów, poprawione odwołania do usuniętych plików, README zaktualizowane, daty uzupełnione w `docs/projekt/TASKS.md`.

## 2026-10-20: D24 krok 1, rzadki indeks runu

- Do tego wpisu dziennik milczał. Stan był tylko w commicie `754db93` (`pipeline/viz_index.py`), a `ROADMAP.md` nadal mówił „kod niezaczął”.
- Indeks: `uv run python pipeline/viz_index.py output/g5r6_25pct_s4711`. Budowa 22,4 s. Drugi start: `reuse tracks=29660 knots=3787376 sec=0.0`, bez drugiego skanu XML. Log: `output/g5r6_25pct_s4711/viz/index.log` (poza gitem).
- Akceptacja R6: 29 660 przejazdów, 6 641 wjazdów w 06:00–09:00, szczyt 961 o 58 170 s, szczyt okna 849 o 28 591 s (licznik eventów, bez doliczania aut już w ruchu o 06:00). Klasy: c 2 410, r 4 336, o 732, t 16 439, h 5 743. Węzły 3 787 376, czynności 59 320 (bez `car interaction`). Plik 12 051 495 B. Geometria: 0,0002 / 0,0003 / 0,0004 m.
- Self-test: `uv run python pipeline/viz_index.py --self-test` → `self-test OK`.
- Po recenzji kroku 1: czynność bez `x` albo `y` przerywa budowę (wcześniej lądowała na węźle from; na R6 ta gałąź się nie wykonała, bo każda czynność ma współrzędne). Usunięte nieużywane `parse_sec`. Ten sam zestaw liczb po przebudowie.
- Dalej, niezacząte: krok 2 (silnik klatki bez okna), potem spike Qt kontra WebView2, klucz CARTO, okno. MVP i D23 bez zmian.

## 2026-10-20: D24 krok 2, silnik klatki bez okna

- `pipeline/viz_engine.py`. Czyta indeks z kroku 1 (albo buduje go przez `viz_index.py`) i zwraca klatkę, klik, lookup i czynności. Bez okna, bez rysowania, bez XML po stronie silnika. Java i `g6_bake.py` bez zmian.
- Self-test: `uv run python pipeline/viz_engine.py --self-test` → `self-test OK`. Węzeł co do 1 mm, auto znika poza `[t0, t1]`, filtr bez `t`, lookup `r1` (dwa przejazdy, prefiks `r1b`), pick auta i cięciwy, `home`/`work` bez `car interaction`, sufit prędkości 30 m/s.
- R6: `uv run python pipeline/viz_engine.py output/g5r6_25pct_s4711`. Indeks wzięty z dysku (`reuse`, bez skanu XML). Log: `output/g5r6_25pct_s4711/viz/engine.log`.
  - Klatka o 58 170 s: 961 aut przy pełnym filtrze (tyle, ile licznik enter/leave), 420 bez klasy `t`. Dwie klatki w 0,008 s. RAM indeksu 89 497 631 B.
  - Pierwsze `r…` w pliku: `r6510903_5`, dwa przejazdy. Najgorszy węzeł tego przejazdu: 0,000000 m. Pick na współrzędnej auta zwraca ten przejazd.
  - Czynności `c1002062_103`: jest `home`, nie ma `car interaction`.
- Całość sprawdzenia R6: 0,3 s. Błędów uruchomienia nie było, więc `ERRORS.md` bez nowej lekcji.
- Dalej, niezacząte: spike Qt kontra WebView2 (`output/viz_spike/`, poza gitem), potem krok 3 (okno). Klucza CARTO nadal nie ma. MVP i D23 bez zmian.

## 2026-10-20: D24 spike stosu okna

- Dwie minimalki na tej samej klatce R6 (`output/g5r6_25pct_s4711`, t = 58 170 s, 961 aut, 8 362 cięciwy). Kod w `output/viz_spike/`, poza gitem. Zależności (`PySide6`, `pywebview`, `pillow`) w osobnym venv pod tym katalogiem, nie w `pyproject.toml`.
- Osie: 524 805 E, 485 023 N → 52,2307° N, 19,3633° E.
- CARTO `dark_nolabels` bez klucza: HTTP 200, 35 razy ten sam PNG 2 513 B z napisem API KEY REQUIRED. Podkładu nie było. Oba okna napisały „Podkład wyłączony.” `tile.openstreetmap.org` nie był użyty.
- Tempo 30 Hz przez 2 s, klik w auto 0 (zwrócony indeks 0), working set procesu i potomków:

  | wariant | Hz | klik | RAM |
  |---|---:|---:|---:|
  | PySide6 | 29,56 | 0,24 ms | 165 MB |
  | WebView2 + Leaflet | 29,22 | 0,92 ms | 503 MB |

- WebView2: jedna tablica JSON na klatkę, jedno `evaluate_js`. Progi (15 Hz, 1 GB, 50 ms) oba warianty mieszczą. Zostaje WebView2 + Leaflet. Zrzut: `docs/research/wizualizer_spike.png`. Liczby: koniec `docs/research/wizualizer_plan.md`.
- Pierwszy start WebView2 urwał się na przecinku w odczycie RAM (`526,9`) i zostawił okno. Proces został ubity, parser poprawiony, liczba w tabeli jest z powtórzenia. `ERRORS.md` bez nowej lekcji: kod spike'u i tak idzie do kosza.
- Okno v1 (krok 3) nie jest zaczęte. Klucza CARTO nadal nie ma. MVP i D23 bez zmian.

## 2026-10-20: D24 spike stosu, powtórka

- Powód: przy pierwszym pomiarze w RAM były inne programy. Powtórka na tej samej klatce (961 aut, 8 362 cięciwy), Qt i WebView2 jeden po drugim. Przed startem, przez 2 s: 5,8 s CPU z 24 (12 rdzeni), głównie `dllhost` i VS Code.
- PySide6: 29,70 Hz, klik 0,24 ms, 165 MB, indeks 0. WebView2: 29,58 Hz, klik 0,65 ms, 503 MB, indeks 0, kafelki `0,0`.
- Progi bez zmian. Do okna zostaje WebView2 + Leaflet. Krok 3 niezaczął. Klucza CARTO nadal nie ma.

## 2026-10-20: D24 krok 3, okno

- `viz_player/`. Uruchomienie: `uv run python -m viz_player output/g5r6_25pct_s4711`. Stos: WebView2 (`pywebview` 6.2.1 w `pyproject.toml`) i Leaflet 1.9.4 w `viz_player/vendor/`. `PySide6` nie wszedł. Java i `g6_bake.py` bez zmian. Okno nie parsuje XML: czyta indeks przez `viz_engine`.
- Akceptacja automatyczna. Self-testy indeksu i silnika nadal przechodzą. `uv run python -m viz_player --self-test` → `self-test OK` (zegar 06:00:00 i 30:12:00, próbka `0,25`, rampa G6, czynność zamiast ducha, klik auta i linku, prefiks id).
- R6, bez rysowania: `uv run python -m viz_player --check output/g5r6_25pct_s4711`. Log: `output/g5r6_25pct_s4711/viz/player.log`. Start 06:00:00, próbka `0,25`, podkład wyłączony, 10 383 linki, osie 52,2307° N 19,3633° E. Klatka 07:56:31 (28 591 s): 849 aut, bez `t` 447. Szczyt 58 170 s: 961. Lookup `r6510903_5` trafia. Indeks z dysku (`reuse`, bez skanu XML).
- Smoke okna na tym samym runie: mapa 1106×811, narysowane 849 i po wyłączeniu chipa `t` 447, podpis próbki `0,25`, zdanie „Podkład wyłączony.”, panel pokazuje `r6510903_5`, Escape czyści wybór. Zrzut (pauza 07:56, nie stan otwarcia): `docs/research/wizualizer_okno.png`.
- Akceptacji ludzkiej nie zaliczam. Zostaje obejrzenie: pauza 07:56, play, suwak 06:30 i z powrotem, szukanie, śledzenie, Escape, klik linku, czytelność panelu. Klucza CARTO nadal nie ma. MVP i D23 bez zmian. Krok 4 nie ruszany.
- Po obejrzeniu, tego samego dnia: ukrycie panelu zabierało pasek razem z przyciskiem (siatka), a kolejne okno po krzyżyku wstawało bez aut i linków (`pull` łapał `busy`, zanim mostek dostał `frame`). Lekcja 28 w `ERRORS.md`. Przycisk zostaje na pasku i nazywa się „panel”, gdy panel jest schowany. Smoke czeka na zegar 06:00:00 z odtwarzania i sprawdza prostokąt przycisku.

## 2026-10-20: D24 krok 4, oś harmonogramu

- Panel wybranego id rysuje oś czasu zamiast listy czynności. Czynność z `actstart`/`actend`, jazda z przejazdów. Jazda wycina nachodzącą czynność. Klik w oś ustawia czas. Dziury to dojście (`car interaction` nie wchodzi do indeksu). Zakres osi jest zakresem runu, nie wycinkiem osoby. To nie jest wykres natężenia.
- `uv run python -m viz_player --self-test` → `self-test OK`. Oś syntetyczna: dom, jazda, praca, jazda, dom. Jazda 180–220 wycina pracę. W mini-runie `r1` o 06:00 stoi na domu, jazda jest 23 000–23 100 s, o 24 000 s zaznaczona jest praca.
- Self-testy indeksu i silnika nadal przechodzą.
- R6: `uv run python -m viz_player --check output/g5r6_25pct_s4711`. Indeks z dysku (`reuse`). Log: `output/g5r6_25pct_s4711/viz/player.log`. 849 aut o 07:56:31, bez `t` 447, szczyt 961, próbka `0,25`. `r6510903_5` ma 5 odcinków: dom 00:00:14–00:04:32, jazda 00:05:09–00:12:40, praca 00:17:33–08:17:33 (zaznaczona o 07:56), jazda 08:22:27–08:31:17, dom do 32:23:09.
- Smoke: mapa 1106×811, pasek osi widoczny po wyborze tego id (szerokość > 40 px, jest odcinek). Zrzut bez zmian treści: pauza 07:56, `docs/research/wizualizer_okno.png`.
- Poza tym krokiem, bo każde rusza zakres i czeka na własny wpis: łamane OSM w konwerterze (Java), podkład z kluczem CARTO, drugi run, spięcie `g6_bake.py`, Łódź. Java i bake nietknięte. `ERRORS.md` bez nowej lekcji. Akceptacji ludzkiej obrazu nie zaliczam. MVP i D23 bez zmian.
- Tego samego dnia, po obejrzeniu: oś liniowa na dobę runu dawała jazdę jako pasek rzędu piksela. Postój ma teraz wagę 1, jazda co najmniej wagę 8 minut. Pasek ma 36 px i podpis w odcinku. Klik liczy czas wewnątrz odcinka. Self-test: 22 h domu i 8 h pracy mają tę samą szerokość, jazda zajmuje ponad 15% paska. Smoke na `r6510903_5`: niebieski odcinek szerszy niż 12% paska.

## 2026-10-21: D24, łamane OSM w oknie

- Tylko odtwarzacz. `viz_player/curves.py` czyta PBF (`data/raw/osm/lodzkie-*.osm.pbf`, bez zapisu) i sieć runu, składa łańcuch między węzłami from/to i zapisuje `output/<run>/viz/curves.npz`. Java, `viz_index.py`, `viz_engine.py`, sieć, eventy i plany bez zmian.
- Łuk wchodzi, gdy zgadza się z `length` co do 1 m i choć jeden punkt odchodzi od cięciwy o więcej niż 2 m. Inaczej zostaje prosta. Brak PBF nie wywala okna. Auto, ślad i klik drogi idą po łamanej. Ułamek bierze się z cięciwy, bo tak stoi pozycja w indeksie.
- R6: 4705 z 10 383 linków, skan OSM 7,2 s, potem cache. `1807611370009f`: length 1969 m, cięciwa 842 m, 11 punktów, środek łamanej ponad 100 m od środka cięciwy. Klatki bez zmian: 849 o 07:56:31, bez `t` 447, szczyt 961.
- HTML ma 659 KB. 50 196 punktów łamanych dochodzi po starcie okna, kawałkami. Wklejenie ich w stronę dało 1,7 MB i `NavigateToString` odrzucił dokument (lekcja 29).
- `uv run python -m viz_player --self-test` → `self-test OK`. Self-testy indeksu i silnika też. `--check` i `--smoke` na `output/g5r6_25pct_s4711` przeszły. Smoke: mapa 1106×811, 849 aut, łamane namalowane. Zrzut (pauza 07:56, nie stan otwarcia): `docs/research/wizualizer_okno.png`.
- Akceptacji ludzkiej obrazu nie zaliczam. Drugi run, spięcie bake'u, klucz CARTO i Łódź bez zmian. MVP i D23 bez zmian.

## 2026-10-21: D24, dokumentacja odtwarzacza

- Opis programu: `docs/research/wizualizer_odtwarzacz.md`. Plan, koncepcja i recenzja zostają. Kod odtwarzacza bez zmian (ostatni commit kodu `d62c8ee`). Wskaźnik stoi na początku `docs/research/wizualizer_plan.md` i w punkcie otwartym D24.

## 2026-10-21: D24, plan poprawek okna

- Michał: łamane działają, auta jadą po łuku.
- Plan, bez kodu: `docs/research/wizualizer_plan.md`, sekcja „Poprawki okna”. Kolejność: znacznik (dłuższy grot i półkole z tyłu, punkt w środku podstawy), checkbox koloru dróg według `type` z legendą, strzałki mnożnika co 1 przy zostawionych presetach, kolor auta prędkość albo klasa z legendą. Raster, WMS i wybór folderu runu są następną turą.
- Michał zaakceptował plan w całości, także tabelę klas. Kod czeka na osobne zlecenie.

## 2026-10-21: D23 kroki 2–4 (sieć R7)

- Krok 2: ponowne dopasowanie `f_g` na 77 trasach analizy (240 requestów TomTom, łącznie 1 237; `BUDGET` podniesiony do 2 000). C identyfikowalna: 0,60 (0,53–0,68, 14 tras). MAPE w próbie 18,4 → 14,3% (f wg reguły).
- Decyzja użytkownika: f = A 0,95, B 1,00, C 0,60, D 0,70, E 0,85, F 0,55 („na dziś”).
- Krok 3: `CreateKutnoNetwork.setSpeed` (`factor.<grupa>`, `speed_group`), sieć `network_d23.xml.gz`: te same id i atrybuty jak R6, różni się tylko freespeed (`check_network_r7.py`). `validate_network.py`, smoke (20 nóg car), test 2 iteracji ok. R7 25% × 5 (100 iteracji): `check_events` 5/5 ok, 0 stuck; opóźnienie dobowe +25% względem R6.
- Krok 4: natężenia vs GPR zmieniają się **ponad rozrzut seedów planów** (lekkie DK 82–105% → 147–152%, DW 60 → 90%, odcinki w ±15%: 12 → 5; A1 bez zmian). STOP: decyzje R7b i terminu kroku 5 u użytkownika. Raport: `reports/etap2/g5_predkosci_d23/krok3_4_r7.md`.

## 2026-10-21 (wieczór): D23 R7b i krok 5 (walidacja TomTom)

- R7b: model pracujących na sieci R7, estymacja O-D (`r7b`, tau 30 min, 3 seedy planów), plany `plans_g5r7b[p1|p2]_25pct`, 5 runów 25% × 100 it.: `check_events` 5/5 ok, 0 stuck, 0 przepełnionych linków, opóźnienie dobowe 209–247 poj.-h (R6 239–298). Natężenia vs GPR: 14/15 odcinków w ±15% w obu klasach (R6: 12/15), A1 98% / 101%, mediana odchyłki lekkie 1,5%.
- Błąd: skrypty estymacji i planów czytają na sztywno `scenarios/kutno/network.xml.gz` (R6). W worktree `d23` podmieniony na sieć R7 (kopia R6: `network_r6.xml.gz`), estymacja powtórzona. **Przy scalaniu do `main` trzeba to uwzględnić.**
- Krok 5: walidacja TomTom (385 requestów, łącznie 1 627 z 2 000), R6 i R7b ocenione na jednym zestawie odpowiedzi, trasy R7b z runów (`traffic_metrics.py model_r7b`, `traffic_providers.py run tomtom --validate`). Walidacja (38 tras): MAPE 20,5 → 18,2%, TAG 48 → 58%; analiza (77): 18,3 → 14,7%, TAG 52 → 64%; prędkość swobodna segmentów 0,86 → 0,99 mediany, MAPE 20 → 13%. Najlepsza grupa C (MAPE 17,9 → 7,3%); D pogorszona (38 → 47%); E, F bez zmiany. TAG 85% niespełnione.
- Analiza `f` po walidacji i decyzje: `reports/etap2/g5_predkosci_d23/krok4b_5_r7b.md`. `f` bez zmian (A 0,95, B 1,00, C 0,60, D 0,70, E 0,85, F 0,55), czeka na decyzję użytkownika.

## 2026-10-21 (noc): R7b bazą, zamknięcie G5 (D25), GitHub Actions

- D25: R7b nową bazą (configi `scenarios/kutno/config_{10,25,100}pct.xml` i `config/kutno.toml` wskazują `plans_g5r7b_*`, macierze `background_od_r7b_*`), `f_D` bez zmian, G5 zamknięte ze znanymi ograniczeniami. Plany 10% i 100% R7b wygenerowane i zwalidowane (sha256 powtarzalny).
- Zapisane: obserwacje o `f` (`reports/etap2/g5_predkosci_d23/obserwacje_f.md`), podsumowanie kalibracji i walidacji (`d23_podsumowanie.md`). Dane TomTom: tylko agregaty na dysku; ponowna kalibracja i walidacja wymagają nowych requestów (D22).
- GitHub Actions: samodzielny scenariusz `scenarios/kutno_r7b_25pct/`, szkic `.github/workflows/matsim-run.yml` (100 i 400 it.), analiza wykonalności `docs/research/GH_ACTIONS_run.md`. Nieuruchomione na GitHubie (push tylko na prośbę).

## 2026-10-22: GitHub Actions, R7b 100 vs 400 iteracji

- Workflow `matsim-run` uruchomiony na GitHubie (run 39668217361, po poprawce `bash ./mvnw`). 100 it. ok. 23 min, 400 it. ok. 109 min. Run 100 it. zgodny z lokalnym (scorestats bajt w bajt, GPR i opóźnienie identyczne).
- 100 vs 400: czasy podróży i prędkości różnią się o ≤ 0,4 km/h, GPR o ≤ 0,004, opóźnienie 221,5 → 215,1 poj.-h, 0 stuck, 0 przepełnionych. 100 iteracji wystarcza. Raport: `reports/etap2/g5_predkosci_d23/gha_100_vs_400.md`.

## 2026-10-23: G1, skrzyżowania (D26), baza R8

- `CreateKutnoNetwork` czyta relacje OSM `restriction` -> `DisallowedNextLinks` (55 relacji, 62 pary linków, 55 linków), `TurnRestrictionsNetworkCleaner` bez zmian w grafie. Sieć R8 = R7b + zakazy; `scenarios/kutno/network.xml.gz` nadpisana (kopia R7b: `network_r7b.xml.gz`). Smoke test i `check_events --expect-car-legs 20` ok.
- Naruszenia zakazów w eventach 170 -> 10 (ostatni link trasy). Runy R8 25% × 5 × 100 it.: 0 stuck, GPR 14/15 (lekkie i ciężkie) jak R7b, zmiana na odcinek ≤ 0,8% wobec rozrzutu planów 4–5%, opóźnienie 221,5 -> 216,2 poj.-h. Efekt poniżej rozrzutu; `f_E`/`f_F` bez zmian. Raport: `reports/etap3/g1_skrzyzowania/g1.md`.

- G1b (D27): mnożnik k przepustowości wlotów (33 węzły z sygnalizacją, 948 wlotów podporządkowanych), 4 sieci × 5 runów, 25%, 50 iteracji na GitHub Actions. GPR bez zmian (14/15), opóźnienie: k=0,8 w szumie, k=0,6 +26%, k=0,4 +109%. Baza R8 bez zmian. `reports/etap3/g1_skrzyzowania/g1b.md`.

- G3 (D28): domy z BDOT10k (jedno- i wielorodzinne, 19 520 budynków, waga obrys × kondygnacje), `plans.py home_source=bdot` (OSM odtwarza R7b bajt w bajt), zgodność z siatką GUS 250 m TV 10,3 → 8,1 pp. Baza R9 = R8 + domy BDOT + ponowna estymacja O-D (lekkie +0,05%, ciężkie bez zmian) + plany `plans_g3r9_{10,25,100}pct`. 5 runów 25% × 50 it.: 0 stuck, nogi car = plany, GPR 14/15 (lekkie i ciężkie), opóźnienie 231,5 vs 226,6 poj.-h (R8, 50 it.; rozrzut planów 25–30), natężenia i czasy podróży w rozrzucie planów. `reports/etap3/g3_domy/g3.md`.

- Zawrotki (D29, R9.1): pomiar R9 35,1% podróży z zawrotką na starcie lub końcu (1,99% czasu pojazdów); `plans.py snap_mode=route` (kierunek linku wg trasy swobodnej, osobne linki domu na start i koniec, lustro wjazdu dla przyjeżdżających). GHA run 39986337733 (5 + 5, 25%, 50 it.): zawrotki 12,4% (0,49% czasu), GPR lekkie 14/15, ciężkie 13/15 (DK 10044 −16,3% przy rozrzucie planów 12–14%), opóźnienie 224,3 vs 231,5 poj.-h (rozrzut 25). Baza R9.1 czeka na decyzję użytkownika. `reports/etap3/g_zawrotki/zawrotki.md`.
