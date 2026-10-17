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
- Dowód: `equil` 1 iteracja → `reports/f0_env/f0_equil_events.json` `ok: true` (201 nóg car, 0 stuck). Szczegóły i nowe gotchas: `reports/f0_env/f0_env.md`.
- `.venv` (uv, Py 3.12), `data/manifest.csv` (5 plików, sumy SHA-256 zweryfikowane).

## 2026-10-16 — F1 zaliczona
- `scenarios/smoke/` (10 agentów, EPSG:2180): 20 nóg car, 0 stuck, współrzędne bez zamiany osi. Dowód: `reports/f1_smoke/f1_smoke.md`, `reports/f1_smoke/f1_smoke_events.json`.
- Scenariusz zostaje testem regresyjnym.

## 2026-10-16 — F2: topologia zaliczona, prędkości do decyzji
- Sieć powiat + 3 km: 4 453 węzły, 10 296 linków, SCC 100%, 90/90 tras testowych. Dowód: `reports/f2_network/f2_network.md`, `.json`, `.png`.
- Otwarte: domyślne prędkości Supersonic (15 km/h na ~3 000 km dróg lokalnych), decyzja użytkownika.
- Wizualizacje wsteczne: `reports/f0_env/f0_equil.png`, `reports/f1_smoke/f1_smoke.png` (`pipeline/plot_run.py`). Regresja smoke po przebudowie jara: ok.
- F2 zamknięta po D13 (limity ustawowe × 0,8): centrum → skraje powiatu 22–35 min, 90/90 tras, regresja ok.

## 2026-10-16 — F3 zaliczona
- Mieszkańcy pracujący w Kutnie 17 546 (bazowy) / 16 167 (niski) + 8 186 przyjeżdżających = 25 732 / 24 353 agentów przy 100%. Dowód: `reports/f3_demand/f3_demand.md`, `.json`, `.png`.
- Złączenie obwodów 232/232 (reguła rejon × 10 + nr). Otwarte do F4: kierunek wjazdu dla 1 157 osób spoza łódzkiego.
- Poprawka F2 (zgłoszenie użytkownika): A1 ucinana przez NetworkCleaner na granicy. Zawrotki na granicy → motorway 87,8 km (było 18). `reports/f2_network/f2_network.md`.

## 2026-10-16 — F4 zaliczona (test automatyczny), czeka na QGIS
- `plans.xml.gz` 10% bazowy: 2 573 osoby (1 762 mieszkańców, 605 z powiatu, 206 na wjazdach), łańcuch h-car-w-car-h 100%, sha256 powtarzalny. Dowód: `reports/f4_plans/f4_plans.md`, `.json`, `.png`.
- Kierunek wjazdu spoza łódzkiego rozwiązany krajowymi rejonami BREC 2021 (nowe pobranie 124 MB, manifest).
- Godziny nadal ZAŁOŻENIE (07:00 / 8 h), decyzja D10 otwarta.

## 2026-10-16 — F5 zaliczona (run 10%)
- D14: godziny wyjazdu z GBR Gdańsk 2022 Rys. 46 (punkty wektorowe PDF), plans F4 przegenerowane (sha256 `525ed292…`, test F4 ok).
- Run 10%, 20 iteracji, 2,5 min: 5 146 nóg car = 2N, 0 stuck. Czas podróży mediana: mieszkańcy 17,3 min, przyjeżdżający 25,6 min. Kongestia 624 poj.-h, wąskie gardło: ciąg primary SE od centrum. Dowód: `reports/f5_run_10pct/f5_run.md`, `reports/f5_run_10pct/f5_events.json`, `reports/f5_run_10pct/f5_run.png`, `reports/f5_run_10pct/f5_delay.png`.

## 2026-10-16 — F5: sprawdzenie wąskiego gardła
- Główne wąskie gardło F5 to ul. Sklęczkowska (DK92), zwężenie z 2 do 1 pasa w kierunku NE. Rano popyt wynosi około 1 700 poj./h przy przepustowości 1 500. Atrybuty sieci zgadzają się z OSM, więc przyczyną jest popyt (D6/D7), a nie błąd sieci. `reports/f5_run_10pct/f5_run.md`.

## 2026-10-16 — F6 zaliczona (100%)
- 25 732 osoby, 51 464 nogi car = 2N, 0 stuck, 4 min 9 s na 20 iteracji, RAM maks. około 1 GB. Rozkłady czasu podróży zgodne z F5 (mediana 16,8 vs 17,3 min dla mieszkańców). Kongestia 6 830 poj.-h: DK92 i ulice lokalne do wschodniej strefy pracy. Dowód: `reports/f6_run_100pct/f6_run.md`, `reports/f6_run_100pct/f6_events.json`, `reports/f6_run_100pct/f6_compare.png`, `reports/f6_run_100pct/f6_delay.png`.
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
- MATSim 2026 odrzuca storage ≠ flow, więc E3 z R3 wycofane (`reports/r3_ocena/testy/r3_storage_factor_rejected.log`).
- **Policzony tylko 25%, seed 4711, 100 iteracji:**
  - 12 866 nóg car = 2N, 0 stuck, 13 min;
  - czas podróży: mediana 15,5 / 24,1 min (mieszkańcy / przyjeżdżający), p90 35,0 / 36,8;
  - opóźnienie 1 130 poj.-h;
  - wąskie gardło DK92 Sklęczkowska (zwężenie do 1 pasa) z kolejką cofającą się na odcinek 6 000 poj./h;
  - select-link: 38% agentów jedzie tym odcinkiem.
  - `reports/r3_25pct_*`, `reports/r3_ocena/wyniki_25pct/r3_compare.*`.
- **Uzupełnione 2026-10-17:** seedy 1 i 2, zbieżność i porównanie seedów, raport `reports/r3_ocena/wyniki_25pct/r3_25pct.md`.
- Lekcje z błędów tej sesji: `ERRORS.md` i reguły 7–11 w Workflow `CLAUDE.md`.

## 2026-10-17: R3, wyniki z 25% (3 seedy, 100 iteracji)

- Seedy 1 i 2 liczone równolegle (po 4 wątki, 13 min). Liczba wątków QSim nie skraca runu. Wyniki przy 4 i 8 wątkach są identyczne, przy 1 wątku się różnią.
- Wszystkie 3 seedy: 12 866 nóg car, 0 stuck (`reports/r3_25pct_s*_events.json`).
- GEH < 5 w szczycie 7–8 (natężenia przeskalowane do 100%): 98,9–99,5% linków. Mediany czasów różnią się o ≤ 0,4 min, suma opóźnień o 11%.
- Raport: `reports/r3_ocena/wyniki_25pct/r3_25pct.md`. Mapy są teraz w ciemnym motywie (prośba użytkownika).

## 2026-10-17: D16, przyjeżdżający spoza powiatu

- A: start z wjazdu = godzina z profilu GBR (bez doliczania dojazdu). B: gminy dalej niż 100 km od wjazdu pominięte (12 gmin, 47 osób w 100%).
- Plany 10/25/100%: walidacja ok, sha256 powtarzalny (`reports/d16_przyjezdzajacy/plans_*.json`).
- Run 25%, 3 seedy równolegle (14 min): 12 842 nóg car, 0 stuck. Wskaźniki zbiorcze bez zmian poza rozrzutem seedów. Raport: `reports/d16_przyjezdzajacy/d16_przyjezdzajacy.md`.
- Porządki: `reports/` w folderach faz, spis w `reports/README.md`. 3 seedy 10% vs 25%: `reports/r3_ocena/r3_10_vs_25pct.md`.

## 2026-10-17: G2 / D17, liczba miejsc pracy i wyjeżdżający

- D17 w `DECISIONS.md`: B (rejestr P4507) jako baza, C (skalowanie do P4508 = 17 486) jako wariant wrażliwości, wyjeżdżający O1 z odcięciem > 100 km, rok 2024.
- `demand.py`: kolumna `work_in_kutno_reg` (14 586 w 100%), `outbound_by_gmina.csv` (83 gminy, 2 669 os.). `plans.py`: rodzaj `outbound` (dom w budynku w Kutnie, praca w budynku gminy powiatu albo na linku wyjazdowym; 31 linków wyjazdowych), `jobs_total` do wariantu C (nadpisanie z linii poleceń `jobs_total=17486`).
- Odcięte > 100 km: 30 gmin, 235 os. w 100% (47 przyjeżdżających, 188 wyjeżdżających). Warszawa (457) zostaje, wyjazd na A1.
- Plany 10%: B 2 521 os. (1 465 mieszk., 808 przyjeżdż., 248 wyjeżdż.), C 1 997 os. (1 133 / 616 / 248). Walidacja ok, sha256 powtarzalny (`reports/g2_miejsca_pracy/{B,C}/plans_10pct_plans.json`). Pierwsza wersja nie przeszła walidacji (ERRORS 14).
- Runy 10% × 3 seedy dla B i C (6 równolegle, po 2 wątki, 11 min): nogi car zgodne z planami (5 042 / 3 994), 0 stuck. Opóźnienia [poj.-h próbki]: B 370–405, C 146–166, wobec 540–567 w starych runach 10% (A). GEH < 5 w szczycie między seedami: B 93–95%, C 96%. Raport: `reports/g2_miejsca_pracy/g2_miejsca_pracy.md`.
- B na 25% × 3 seedy (nowe wyniki referencyjne, domyślne `plans_25pct.xml.gz` z D17/B): 6 302 osoby, 12 604 nóg car, 0 stuck. Opóźnienia 754–777 poj.-h próbki (D16: 1 076–1 091, −30%), GEH < 5 w szczycie między seedami 99,4–99,9%. `reports/g2_miejsca_pracy/B_25pct/`.

## 2026-10-17: kolejki z G6, poprawka D18

- `pipeline/queues.py`: diagnoza na eventach (przejazdy linków, przyczyna: capacity / spillback / węzeł, przepełnienie). Run B 25%: 26% czasu pojazdów w opóźnieniu (zgodne z 26% klatek w G6). 51% opóźnień na ulicach tertiary z 600 poj./h/pas, 44% to kolejka spod zwężenia Sklęczkowskiej (2 → 1 pas).
- Artefakt: `stuckTime` 10 s → 82 pojazdy na linku o pojemności 1,2. Test na tych samych trasach (stuckTime 10/30/60/300, kinematicWaves 30/300): przy queue suma opóźnień ±7%, przy kinematicWaves +56%, a z 300 s gridlock.
- D18: stuckTime 30 (Berlin v6.3, Kelheim v3.1). Run 25% × 3 seedy: 12 604 nóg car, 0 stuck, opóźnienia 735–854 poj.-h próbki, przepełnione linki 4–7 zamiast 13, GEH < 5 w szczycie 98,8–100%. Raport: `reports/g6_kolejki/g6_kolejki.md`. Nowe wyniki referencyjne: `reports/g6_kolejki/d18_25pct/`.

## 2026-10-17: G5, punkt startowy i plan kalibracji

- `pipeline/g5_baseline.py`: model D18 (25%, 3 seedy) vs GPR 2025 (lekkie, SDRDR, na kierunek). A1 7%, DK w Kutnie 56% (Sklęczkowska 71%, Objazdowa 65%, Bitwy pod Kutnem 28%), pozostałe DK 16%, DW 7%. `reports/g5_kalibracja/g5_0_baseline.*`.
- Plan z wariantami (K1 dojazdy autem, K2 tło, K3 profil, K4 walidacja z 3 odcinkami miejskimi poza próbą, K5 wrażliwość sieci): `docs/research/G5_plan_kalibracji.md`. Czeka na decyzje użytkownika, runów nie ma.

## 2026-10-17: G5 / D19, kroki bez MATSim i run R1

- D19: K1-1 (popyt car × 0,593), K2-2 (tło lekkie z O-D estymowanego z GPR), K3-2 (profil Lisica), K4 (3 odcinki miejskie poza próbą).
- `digitize_lisica.py`: profil godzinowy dnia roboczego (lekkie i ciężkie, sumy 100%).
- R1 (D18 + K1-1, 25% × 3 seedy): 7 478 nóg car, 0 stuck, opóźnienia 106–113 poj.-h próbki (D18: 735–854). Model / GPR: A1 3%, DK w mieście 30%.
- `background_od.py`: odcinki dopasowania ok, ale walidacja w mieście daje 140–173% GPR na Sklęczkowskiej i 155–168% na Objazdowej. Luka A1 nie rozróżnia tranzytu od relacji z Kutnem. Opcje W1–W3 w `docs/research/G5_plan_kalibracji.md` §4. Czeka na decyzję. Agentów tła jeszcze nie ma w planach.
