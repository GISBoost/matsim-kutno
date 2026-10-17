# TASKS — fazy MVP

Każda faza: wejścia → działania → wyjścia → test → kryterium zaliczenia → **wizualizacja** → stop.

**Wizualizacja po każdej fazie (prośba użytkownika, 2026-10-16):** faza kończy się obrazem `reports/fN_*.png`, który pokazuje to, co faza testowała (mapa, przejazdy, rozkłady). Obraz trafia do użytkownika razem z listą wykresów, które MATSim sam generuje w `output/<run>/` (`modestats.png`, `scorestats.png`, `traveldistancestats*.png`, `stopwatch.png`). Dla runów MATSim: `uv run python pipeline/plot_run.py <output_dir> reports/fN_run.png "tytuł"`. Bez zaliczenia nie przechodzimy dalej. Blocker = wpis w `ERRORS.md` i pytanie do użytkownika.

## F0 — Środowisko MATSim
- **Wejścia:** `matsim-example-project` (branch master, parent `matsim 2026.0`), Java 25.
- **Działania:** skopiować projekt do `matsim/` (bez historii gita upstream), `mvnw.cmd package -DskipTests`, uruchomić przykładowy scenariusz `equil` z 1 iteracją. Utworzyć `.venv` (uv) i `data/manifest.csv` (przenieść wpisy z FACT_CHECK).
- **Wyjścia:** `matsim/`, `reports/f0_env/f0_env.md` (wersje Java/MATSim/uv, czas buildu).
- **Test:** BUILD SUCCESS; przykład kończy się bez wyjątków, a `output_events.xml.gz` istnieje i ma > 0 eventów `departure`.
- **Stop:** build nie przechodzi po 2 próbach naprawy → ERRORS + pytanie.

## F1 — Smoke test (10 agentów, sieć syntetyczna)
- **Wejścia:** ręczny fixture w `scenarios/smoke/` (sieć kilku węzłów w EPSG:2180 z koordynatami w rejonie Kutna, 10 osób, `home 07:00 → work 8 h → home`).
- **Działania:** run 1 iteracji; skrypt `pipeline/check_events.py` liczy eventy per osoba.
- **Test:** 20 `departure` = 20 `arrival`, 0 `stuck`, każda osoba ma `vehicle enters/leaves traffic`, a koordynaty w outpucie są w kolejności E,N.
- **Zaliczenie:** wszystkie warunki spełnione. Ten test zostaje testem regresyjnym na później.

## F2 — Sieć OSM (powiat kutnowski + bufor)
- **Wejścia:** Geofabrik `lodzkie-latest.osm.pbf` (~132 MB), granica powiatu 1002 złożona z geometrii BREC.
- **Działania:** jeden konwerter: `SupersonicOsmNetworkReader` (contrib osm 2026.0) z transformacją do EPSG:2180, filtr obszaru = powiat + bufor (szerokość dobrana tak, żeby objąć drogi wjazdowe; uzasadnić w raporcie), `NetworkCleaner`, tylko `car`.
- **Wyjścia:** `scenarios/kutno/network.xml.gz`, `reports/f2_network/f2_network.json` (węzły, linki, rozkład `freespeed`/`capacity`/`lanes`, linki z wartościami domyślnymi, udział największej SCC, bbox).
- **Test:** bbox mieści się w powiat + bufor; 0 linków z capacity/freespeed ≤ 0; trasy car istnieją między 10 parami punktów (centrum, strefy przemysłowe, 4 kierunki wjazdów).
- **Stop człowieka:** podgląd sieci w QGIS.

## F3 — Popyt: dane GUS
- **Wejścia:** tabela ludności BREC, macierz dojazdów, tablice rynku pracy (łódzkie TABL. 5), geometria BREC 2021.
- **Działania:** filtr po TERC `1002011`; złączenie 232/233 obwodów (wyjaśnić różnicę); pracujący per obwód = wskaźniki × ekonomiczne grupy wieku (warianty niski/bazowy/wysoki w `config/`); pracujący w Kutnie = pracujący mieszkańcy − wyjeżdżający (z jawną notą: macierz obejmuje tylko pracowników najemnych); przyjeżdżający per gmina źródłowa (w powiecie / poza powiatem).
- **Wyjścia:** `reports/f3_demand/f3_demand.json` + CSV pośrednie.
- **Test:** suma ludności = 42 255; suma przyjeżdżających = 8 186; każdy obwód ma geometrię albo jest opisany w raporcie.

## F4 — Lokalizacje i plans (10%)
- **Wejścia:** F2, F3, budynki i landuse z OSM (ten sam PBF).
- **Działania:** domy (D11), domy przyjeżdżających (D9), praca (D7), godziny (D10: stałe albo rozkład ze źródła), `plans.xml.gz` z seeda.
- **Test:** `pipeline/validate_plans.py`: każda osoba ma dokładnie `home-car-work-car-home`; współrzędne mieszczą się w obszarze sieci; liczba osób = 10% × (pracujący w Kutnie + przyjeżdżający) ± zaokrąglenie; identyczny sha256 przy powtórnym uruchomieniu.
- **Stop człowieka:** próbka domów i miejsc pracy w QGIS.

## F5 — Run integracyjny (10%)
- **Działania:** `config.xml` (EPSG:2180, factors 0,1, 10–20 iteracji, strategie: ChangeExpBeta + ReRoute + TimeAllocationMutator do decyzji w tej fazie, seed).
- **Test:** `departure = arrival = 2N`, 0 stuck, rozkład czasu podróży w raporcie, score jest tylko diagnostyką.
- **Wyjście:** `reports/f5_run_10pct/f5_run.md`.

## F6 — Skala 100%
- **Działania:** factors 1,0; pomiar czasu iteracji i RAM; porównanie rozkładów z F5.
- **Test:** jak w F5; RAM < 10 GB.

## Research równoległy (nie blokuje F0–F3)
- R1: źródło rozkładu godzin wyjazdu do pracy i czasu pracy w PL (D10).
- R2: czy BDL ma dane NSP 2021 o pracujących na poziomie gminy (lepsza kotwica dla D5).

---

# Etap 2: od prototypu do modelu (od 2026-10-17)

MVP (F0–F6) jest zamknięty. Każda faza G zmienia zakres lub dane, więc przed startem wymaga wpisu w `DECISIONS.md`. Obowiązują te same zasady co w F0–F6:
- kontrakt fazy: wejścia → działania → test → zaliczenie → wizualizacja;
- runy: 25%, 3 seedy, maks. 100 iteracji;
- źródła w `docs/ZRODLA.md`, pobrania w `data/manifest.csv`;
- wyniki w `reports/gN_*/`.

**Etap 2a (bieżący): zbieranie danych.** Każde źródło trafia do `docs/ZRODLA.md` ze statusem, ograniczeniami i liczbami, które z niego wiemy. Model nie zmienia się, dopóki dane do fazy nie są zebrane i ocenione.

## G1 — Skrzyżowania (odłożone przez użytkownika 2026-10-17, „implementacja później”)
- **Stan:** węzeł QSim bez sygnalizacji, pierwszeństwa, konfliktów i zakazów skrętu. Przepustowość daje tylko link (domyślne wartości Supersonic na pas). 36 węzłów `traffic_signals` w OSM w gm. Kutno.
- **Działania (kolejno):** test wrażliwości przepustowości (DK92, wloty do sygnalizacji); redukcja przepustowości wlotów do węzłów z sygnalizacją (ZAŁOŻENIE z wariantami); zakazy skrętu z relacji OSM jako `DisallowedNextLinks`; ewentualnie contrib `signals` i `lanes` dla kluczowych skrzyżowań.
- **Test:** różnica opóźnień i natężeń względem bazy, większa niż rozrzut seedów.

## G2 — Miejsca pracy (D7)
- **Dane:** suma kontrolna z BDL lub NSP dla gm. Kutno (uwaga na próg > 9 osób); rozkład wewnątrz gminy z REGON (adres, PKD, ewentualnie klasa zatrudnienia) albo z typu budynku. Statystyczne punkty adresowe GUS do sprawdzenia.
- **Działania:** nowe wagi budynków pracy; porównanie z wagami według powierzchni (top-20 celów, rozkład na mapie).
- **Test:** suma pracy zgodna z kotwicą; top-10 celów to realne zakłady; mapa zmian.
- **Stan (2026-10-17):** suma zrobiona (D17: B = 22 725 baza, C = 17 486 wrażliwość, wyjeżdżający O1). Runy 10% × 3 seedy w `reports/g2_miejsca_pracy/`. Otwarte: rozkład wewnątrz gminy (wagi budynków pracy, REGON).

## G3 — Domy (D11)
- **Dane:** kod R5 (`dasymetric_pop.py`, ta sama metoda); BDOT10k (funkcja budynku, ewentualnie kondygnacje); siatki ludności GUS jako kontrola.
- **Działania:** ujednolicić dobór budynków mieszkalnych z R5 (lista wykluczeń zamiast listy typów; 9 817 budynków `yes` poza `landuse=residential`); decyzja o kondygnacjach (w R5 świadomie pominięte).
- **Test:** suma per obwód bez zmian; mniej domów w losowych punktach; porównanie z siatką GUS.

## G4 — Tryby (car / pt / bike / walk) — zmiana zakresu, wymaga decyzji
- **Dane:** GUS Mobilność 2024, tabl. 13 (łódzkie, wszystkie cele), tabl. 1 (praca z domu 7,3%); GTFS Kutno (licencja do wyjaśnienia); sieć rowerowa i piesza z OSM.
- **Działania:** `SubtourModeChoice` i atrybut `carAvail` (wzór: Medina Godoy, MUM 2026); PT z GTFS (pt2matsim albo gtfs2matsim); kalibracja ASC na podział modalny.
- **Otwarte:** podział modalny ze źródła dotyczy wszystkich celów i całego województwa, a nie dojazdów do pracy w Kutnie. Trzeba zdecydować, czy to wystarczy jako cel kalibracji, czy szukamy lepszego źródła.
- **Test:** podział modalny w granicach błędu szacunku GUS (tabl. 32).

## G5 — Ruch tła i walidacja
- **Dane:** GPR (GDDKiA) na DK92 i DK60; ewentualne pomiary miejskie; macierz dostępności GUS do walidacji czasów przejazdu między gminami.
- **Działania:** tranzyt i ciężarówki na drogach krajowych i A1; porównanie z pomiarami (GEH względem pomiarów, a nie między seedami).

## G6 — Wizualizacja w Blenderze
- **Wzór:** Bell (MUM 2026). Eventy → pozycje pojazdów na klatkę (`.npz`) → handler klatki w Blenderze → Geometry Nodes → render.
- **Działania:** skrypt bake w Pythonie (sieć EPSG:2180 → współrzędne sceny; eventy 25% → `.npz`); skrypt ładujący dla Blendera 4.3/4.4; scena bazowa (sieć, budynki OSM, ciemny motyw).
- **Test:** pojazd z eventów jedzie w Blenderze po swojej trasie (porównanie 3 losowych pojazdów); render 1 min doby porannego szczytu.

## G7 — Przeniesienie na Łódź
- Po G2–G5. Wymaga decyzji o skali (Łódź ponad 600 tys. mieszkańców) i zasobach (16 GB RAM).
