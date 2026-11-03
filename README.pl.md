# MATSim Kutno: instrukcja modelu

[English](README.md) | **Polski**

Stan: 2026-11-03, baza **R9.5** (D36). Opis zakłada decyzje D1–D37 z `docs/projekt/DECISIONS.md` i wyniki z `docs/projekt/PROGRESS.md`.
Każde założenie jest oznaczone **ZAŁOŻENIE** albo ma źródło (plik, wiersz, URL w `data/manifest.csv` i `docs/ZRODLA.md`).
Brakujące elementy są w rozdziale 14 („Luki”), z odsyłaczem do dokumentu, który je opisuje. Mapa projektu (fazy, stan, plany): [docs/projekt/ROADMAP.md](docs/projekt/ROADMAP.md).

> **Ważne:** to model ruchu samochodowego w gminie Kutno, nie prognoza ruchu. Na drogach z GPR jest skalibrowany do pomiarów. Na ulicach miejskich poza GPR natężenia są zaniżone mniej więcej o połowę (D37), więc wyników dla tych ulic nie należy czytać wprost.

---

## 1. Cel, zakres i to, czego model nie robi

**Cel:** agentowa symulacja MATSim dla gminy miejskiej Kutno (TERC 1002011, 42 255 mieszkańców wg NSP 2021). Kutno jest poligonem metodologii, którą później przeniesiemy na Łódź, ale dopiero po zakończeniu prac nad samym Kutnem.

**Co jest w bazie R9.5 (wszyscy agenci jadą samochodem):**
- dojazdy do pracy `home → work → home`: mieszkańcy Kutna pracujący w Kutnie, przyjeżdżający i wyjeżdżający (D17), z udziałem auta i obecności w pracy (K1-1, D19);
- osobne wyjścia mieszkańców `home → cel → home`: zakupy i usługi (D32, D34), odwiedziny, rekreacja, zdrowie, podwożenie (D36);
- ruch tła jako subpopulacje `tlo` (lekkie i dostawcze) i `ciezkie`, z macierzy O-D estymowanych z liczników GPR (D19–D21). To estymacja kalibrowana do pomiarów, nie obserwacja;
- sieć z prędkościami per grupa dróg (D23) i zakazami skrętu z OSM (D26), domy z BDOT10k (D28), kierunek linku przypięcia wg trasy (D29), atrybuty osób (D30).

**Czego model NIE robi:**
- nie modeluje transportu publicznego, pieszych ani rowerzystów. Rozkład GTFS jest zaimportowany tylko technicznie (`scenarios/kutno_pt/`), bez agentów PT;
- nie ma wyboru trybu ani kalibracji ASC (krok 6 w ROADMAP). Parametry scoringu są domyślne, a score służy tylko do diagnostyki;
- nie modeluje szkoły jako celu podróży (krok 4B, plan bez wdrożenia), łańcuchów dnia (D35, wariant `chains`, domyślnie `off`), podróży nie z domu, przyjazdów spoza miasta w innych celach niż praca ani ruchu służbowego w mieście;
- nie modeluje sygnalizacji ani pierwszeństwa. Zakazy skrętu działają w routerze, QSim ich nie wymusza;
- nie łączy agentów w gospodarstwa: agent wyprawy jest osobną osobą, niepowiązaną z pracującym (D32).

---

## 2. Jak odtworzyć wyniki

Dane surowe (`data/raw/`) nie są w gicie, ale każdy plik ma URL i sumę SHA-256 w `data/manifest.csv`. Plany i sieć w `scenarios/kutno/*.xml.gz` też są poza gitem, bo powstają z tych danych. Odtworzenie całości od zera na czystym klonie nie zostało jeszcze sprawdzone (krok 8 w ROADMAP).

**Runy MATSim i estymację O-D uruchamiamy na GitHub Actions**, nie lokalnie (ERRORS 34). Wejścia runów leżą w gicie, w `scenarios/kutno_r91/` i `scenarios/kutno_od/`, więc te kroki nie wymagają `data/raw/`.

```bash
# 0. Python (uv, Py 3.12) and dependencies
uv sync

# 1. Raw data: download the files from data/manifest.csv to data/raw/ (check SHA-256)

# 2. Boundaries (EPSG:2180, axes E,N)
uv run python -W ignore pipeline/make_area.py

# 3. Buildings and landuse from OSM (same PBF as the network), shops as shopping destinations (D34)
uv run python -W ignore pipeline/osm_features.py
uv run python -W ignore pipeline/osm_poi.py

# 4. MATSim network: build the uber-jar and convert OSM (Java 25, set JAVA_HOME in the command)
cd matsim && mvnw.cmd -B package -DskipTests && cd ..
java -cp matsim/matsim-example-project-0.0.1-SNAPSHOT.jar org.matsim.kutno.CreateKutnoNetwork \
  data/raw/osm/lodzkie-261015.osm.pbf scenarios/kutno/area/network_area.wkt scenarios/kutno/area/towns.wkt \
  config/network.properties scenarios/kutno/network.xml.gz
uv run python -W ignore pipeline/validate_network.py

# 5. Demand from GUS and registers, full population and person attributes (D30)
uv run python -W ignore pipeline/demand.py
uv run python -W ignore pipeline/attributes.py

# 6. R9.5 baseline plans (25%, parameters from config/kutno.toml; override with key=value)
uv run python -W ignore pipeline/plans.py scenarios/kutno/plans_g3r95_25pct.xml.gz 0.25
uv run python -W ignore pipeline/validate_plans.py scenarios/kutno/plans_g3r95_25pct.xml.gz 0.25 <report_dir>
```

Plan 25% ma sha256 `f3ca89f…`, taki sam jak `scenarios/kutno_r91/plans_r94e_p0.xml.gz` testowany na GitHub Actions. Warto to sprawdzić, bo ten sam config musi dawać ten sam plik.

**Workflowy** (wszystkie tylko ręcznie, `workflow_dispatch`):

| Workflow | Do czego | Wejścia |
|---|---|---|
| `matsim-od` | runy bez tła, estymacja O-D (`background_od.py`), kontrola `od_warnings.py`; wynik to macierze w artefakcie | `scenarios/kutno_od/` |
| `matsim-r93` | porównanie dwóch wariantów planów, po 5 runów (3 seedy MATSim, 2 seedy planów), 25%, 50 iteracji, analiza z pomiarami miejskimi | `scenarios/kutno_r91/` |
| `matsim-r91`, `matsim-r92`, `matsim-attr`, `matsim-g1b` | testy D29, D31, D30 i D27 (historyczne) | jak wyżej, `scenarios/kutno_g1b/` |
| `matsim-run`, `matsim-run-100pct` | runy bazy R7b (historyczne) | `scenarios/kutno_r7b_*` |

Test bazy R9.5 wobec R9.4:

```bash
gh workflow run matsim-r93.yml -f variant=r94e -f control=r93o
```

**Zmiana popytu oznacza nową estymację tła**, w tej kolejności: plany bez tła do `scenarios/kutno_od/` (`plans.py … background_od= heavy_od=`), workflow `matsim-od` z nowym tagiem, potem `od_warnings.py` (w workflow) i plany z nowymi macierzami. Przepis na R9.5 krok po kroku: `reports/etap3/g_inne_cele/inne_cele.md`, sekcja „Odtworzenie”. Macierze z GitHub Actions różnią się od lokalnych szumem losowania punktów, sumy do 0,12% (`reports/etap3/krok0_od_gha/krok0.md`). Różnice wariantów porównuj z rozrzutem seedów planów, nie seedów MATSim.

**Run lokalny** tylko do testu technicznego (z katalogu projektu, nie z katalogu configu; `output/` jest względny do katalogu roboczego):

```bash
java -Xmx10g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run \
  --config scenarios/kutno/config_25pct.xml --output output/test_25pct --iterations 2
uv run python pipeline/check_events.py output/test_25pct/output_events.xml.zst --expect-car-legs 27233
```

27 233 nogi car to plan 25% bazy R9.5: 2 × 3 739 pracujących, 2 × 1 477 wyjść mieszkańców i po jednej nodze dla 16 801 agentów tła.

**Test regresyjny** (po każdej zmianie w `matsim/`): `scenarios/smoke/config.xml` (10 agentów, sieć syntetyczna), potem `check_events.py --expect-car-legs 20`. Przed testem usuń stary output.

---

## 3. Przepływ danych (pipeline)

```
GUS NSP 2021: population per district, commuting matrix, labour market ─┐
GUS BREC 2021: census area boundaries ──────────────────────────────────┤
                                                                        ├─► make_area.py ─► area/ (municipality, county, network area)
OSM Geofabrik lodzkie (PBF) ─► CreateKutnoNetwork (Java) ───────────────┴─► network.xml.gz (car network, turn restrictions, EPSG:2180)
                              ├─► osm_features.py ─► osm/features.gpkg (work buildings, landuse)
                              └─► osm_poi.py ──────► osm/shops.csv (shopping destinations, D34)
BDOT10k ─► homes (D28), destinations of services and other trips (D32, D36)
BDL P4507/P4508 (register 2024) ─► demand.py ─► workers_by_obwod, inbound_by_gmina, outbound_by_gmina
CEPiK, GUS Mobilność ─► attributes.py ─► population_kutno.csv, person attributes (D30)

GBR Gdańsk 2022 (hourly profiles), GUS Mobilność, BCL 2023 ─► errands.py (resident trips, D32, D36)
network + features + demand + errands ─► plans.py ─► plans_*.xml.gz + _meta.csv + _strata.csv
GPR 2025 + runs without background ─► background_od.py (GHA: matsim-od) ─► background_od_*_gpr.csv ─► plans.py (background)

config_*.xml (MATSim 2026.0, seed, factors, QSim) + plans
        │
        ▼
MATSim run (GHA: matsim-r93) ─► output/ ─► check_events.py, queues.py, convergence.py, g5_baseline.py, pomiary_miejskie.py ─► reports/
```

**Podział odpowiedzialności:** Python liczy dane i plany, Java konwertuje sieć i uruchamia symulację. Każdy plik powstaje w jednym miejscu.

---

## 4. Źródła danych

Pełna lista z ograniczeniami: `docs/ZRODLA.md`. Poniżej to, co wpływa na model.

| Źródło | Co dostajemy | Gdzie w modelu | Ograniczenia |
|---|---|---|---|
| **GUS NSP 2021, ludność w rejonach i obwodach spisowych** (`gus/ludnosc_rejony_obwody_nsp2021.xlsx`) | 232 obwody Kutna: ludność ogółem, grupy wieku (przed/produkcyjny/poprodukcyjny). Suma 42 255. | Rozkład mieszkańców pracujących na obwody (D5, D17) | Brak krzyżowania płci z wiekiem i brak statusu zatrudnienia. |
| **GUS NSP 2021, rynek pracy, TABL. 5** (`gus/rynek_pracy_nsp2021_tablice.xlsx`) | Wskaźniki zatrudnienia dla miast woj. łódzkiego: produkcyjny 0,739 (wariant niski: pracujący / ogółem) lub 0,784 (bazowy: bez nieustalonego statusu, metoda GUS); poprodukcyjny ok. 0,12 | Szacunek pracujących per obwód (D5), wariant „base” | Tylko województwo, nie gmina. Estymacja, nie obserwacja. Wartości: `scenarios/kutno/validation/f3_demand.json`. |
| **GUS NSP 2021, macierz przepływów do pracy** (`gus/macierz_przeplywow_nsp2021.xlsx`) | Przyjeżdżający do Kutna: 8 186 osób w 134 gminach. Wyjeżdżający: 2 669 w 83 gminach. | Przyjeżdżający i wyjeżdżający (D3, D9, D17) | Tylko pracownicy najemni. Pomija przepływy < 3 osób i ruch wewnątrz gminy. Miejsce pracy to adres pracodawcy (np. siedziba firmy w Warszawie). |
| **BDL P4507 i P4508, 2024** (`g2/bdl_kutno.json`, API BDL) | P4507: pracujący mieszkańcy gminy (17 255). P4508: miejsca pracy wg siedziby płatnika (17 486). | Kotwica liczby mieszkańców pracujących w Kutnie (D17/B) i wariant C | Rejestry ZUS/KRUS, liczą według siedziby płatnika. Między P4507 + NSP a P4508 jest luka 30%, której nie da się wyjaśnić (G2). |
| **GUS BREC 2021, geometria** (`brec/AreaStatisticalUnit_10_2021.zip`, `brec/SU_BREC_2021_REJ.zip`) | Granice gminy, powiatu, rejonów i obwodów w EPSG:2180 | Obszar, obwody, gminy źródłowe (D9, D11) | Miasta na prawach powiatu mają w BREC kody dzielnic (łączymy po kodzie powiatu). |
| **OSM Geofabrik, `lodzkie-261015.osm.pbf`** (dane do 2026-10-15) | Sieć drogowa, budynki (tag `building`), landuse (`residential`, `industrial`, `commercial`, `retail`), tagi `amenity`/`shop`/`office` | Sieć (rozdział 5), budynki domów i pracy (rozdział 7) | Jakość tagów zależy od wolontariuszy. W gm. Kutno 72% budynków ma `building=yes` (bez typu), a `building:levels` jest w tej grupie tylko w 2% (bloki: 84%). |
| **GBR Gdańsk 2022, Raport 3a, Rys. 46** (`gbr/GBR2022_raport3a.pdf`) | Godzinowe rozkłady wyjazdów „dom–praca” i „dom–inne” (`config/departure_home_work_gbr2022.csv`, `config/departure_home_inne_gbr2022.csv`) | Godziny wyjazdu (D14, D32) | Metropolia Gdańsk, nie Kutno. Dane odczytane z wykresu wektorowego PDF. |
| **GDDKiA GPR 2025** (`g5/gpr2025/`) | Średni dobowy ruch na 19 odcinkach w sieci (A1, DK, DW), SDRR/SDRDR, udział lekkich i ciężkich | Walidacja (G5), cel kalibracji | Jedna wartość na cały odcinek, bez godzin. Brak ulic miejskich poza DK. |
| **GDDKiA SCPR 2025, stacja 14005 Lisica** (`g5/scpr2025/st_14005.pdf`) | Krzywe godzinowe dnia roboczego (zdigitalizowane) | Profil godzinowy ruchu tła (K3-2) | Stacja 13 km od Kutna, na DK60. Digitalizacja z wykresu. |
| **GUS Mobilność 2024** (`gus_transport/mobilnosc_*`) | Praca z domu łódzkie 7,3%; tabl. 10: stawki podróży dom–X; prawo jazdy i auta | Obecność w pracy (K1-1), liczba wyjść mieszkańców (D32, D36), atrybuty (D30) | Tylko województwo. Stawki dotyczą wszystkich środków transportu. |
| **Bochnia 2016, Radom 2022** (`g4/`) | Udział auta w dojazdach dom–praca: 61–67%; Radom: podróże fakultatywne 53,2% | Udział auta (K1-1), udział kierowcy wypraw 0,424 (D32) | Inne miasta, wartości z wykresów. |
| **CEPiK 2019** | Prawa jazdy wg płci i wieku | Atrybut `license` (D30) | Rejestr zawyża najstarsze grupy. |
| **GUS Budżet czasu 2023** | Czasy zakupów, życia towarzyskiego, rekreacji; udział osób robiących zakupy wg wieku | Czasy postoju i uczestnicy wyjść (D32, D36) | Suma z dnia, nie jedna wizyta. |
| **WIOŚ 2013, punkty K1–K5** | Natężenia na pięciu ulicach Kutna | Kontrola ulic miejskich (`pipeline/pomiary_miejskie.py`), cel przeskalowany do 2025 przez GPR | Stare, pomiar jednodobowy. Kontrola rzędu wielkości, nie kalibracja. |
| **TomTom (D22, wariant A)** | Czasy przejazdu tras | Dopasowanie prędkości (D23) | W repo tylko agregaty. Nowe zapytania wymagają zgody. |
| **BDOT10k powiat 1002, 2025-12-09** (`g3/bdot10k/1002_GPKG.zip`) | Budynki z funkcją i liczbą kondygnacji (99,9% wypełnione) | Domy (D28), cele usług i pozostałych wyjść (D32, D36) | 39% geometrii z ortofotomapy. 1 450 budynków OSM w Kutnie nie ma odpowiednika w BDOT10k. |
| **GUS statystyczne punkty adresowe, NSP** (`g2/adr_kutno_2026_0.csv`) | 4 807 punktów adresowych budynków mieszkalnych w Kutnie | Tylko kontrola (G2, G3) | Nic o podmiotach i pracy. |
| **GUS macierz dostępności** (`gus_transport/macierz_dostepnosci_20210331.xlsx`) | Czas przejazdu autem między gminami | Kontrola czasów (G5), próg D16 w minutach (nieużyte) | Model drogowy GUS, bez kongestii. |
| **GTFS zbiorkom.live Kutno, GTFS kolej (Kuranowski)** | Rozkłady autobusów i kolei | Tylko import techniczny `scenarios/kutno_pt/` (krok 5), bez agentów PT | Licencję GTFS Kutno potwierdził użytkownik 2026-10-21. Feed kolei ważny 30 dni. |
| **Literatura VSP i MATSim MUM 2026** (`g5/lit/`, `mum2026/`) | Konfiguracje referencyjne (matsim-berlin v6.3, matsim-kelheim v3.1), praktyka kalibracji | Uzasadnienie `stuckTime` (D18) i dynamiki `queue` | Inne skale. Nie są kopiowane wprost. |

**Zasada:** liczby i parametry bierzemy tylko ze źródeł z `docs/ZRODLA.md` i z `data/manifest.csv`. Twierdzenia z raportów pomocniczych są sprawdzone w `docs/projekt/FACT_CHECK.md`.

---

## 5. Sieć drogowa

### 5.1 Obszar

- **Gmina Kutno** (gm. miejska 1002011): suma 41 rejonów BREC, 33,55 km².
- **Powiat kutnowski** (1002): 117 rejonów, 885,6 km².
- **Obszar sieci** = powiat + **bufor 3 km** (`network_buffer_m = 3000` w `config/kutno.toml`).
  **ZAŁOŻENIE:** bufor zatrzymuje drogi wjazdowe za granicą powiatu, żeby przyjeżdżający z dalszych gmin miały gdzie wjechać. Szerokość bufora poza powiatem jest otwarta (D-otwarte).
- Współrzędne: EPSG:2180, kolejność osi **E, N** (x ≈ 525 000, y ≈ 485 000). Transformacja z WGS84 odbywa się raz, w konwerterze Java.

### 5.2 Konwersja z OSM

- Konwerter: `SupersonicOsmNetworkReader` (contrib `osm`, MATSim 2026.0), tylko tryb `car`.
- Filtr obszaru: linki, których węzły leżą wewnątrz obszaru sieci.
- `NetworkCleaner` usuwa węzły i linki nieosiągalne (F2: usunięto 116 węzłów i 127 linków).
- **Zawrotki na granicy** (poprawka F2, A1): przy przycięciu autostrada A1 zostaje z jednokierunkowymi jezdniami, które kończą się ślepo na granicy, i `NetworkCleaner` usunąłby je aż do najbliższego węzła. Dlatego każdy węzeł-ujście (tylko wjazdy) łączymy z najbliższym węzłem-źródłem (tylko wyjazdy) w promieniu **300 m**. Linki dostają typ `boundary_turnaround`, prędkość 30 km/h i capacity 5 000 poj./h (wartości ZAŁOŻENIE). Działają tylko w pasie **1 km** od granicy (`boundary_zone_m`).

**Zakazy skrętu (D26):** Supersonic nie czyta relacji OSM `restriction`, więc robi to parser w `CreateKutnoNetwork`: 55 relacji, 62 zakazane pary linków jako `DisallowedNextLinks`. Routery je respektują, QSim nie. Efekt jest poniżej rozrzutu seedów (`reports/etap3/g1_skrzyzowania/g1.md`).

**Wynik sieci (baza R8, bez zmian do R9.5):** 4 534 węzły, 10 383 linki. Stan po F2 (przed D23 i D26): 4 453 węzły, 10 296 linków, 4 426 km. Największa silnie spójna składowa obejmuje **100%** węzłów. 90/90 par tras testowych jest osiągalnych. Żaden link nie ma capacity, freespeed, length ani lanes ≤ 0.

### 5.3 Prędkości (D13, D23, D25)

Domyślne prędkości Supersonic (wartości VSP dla miast niemieckich) dawały **15 km/h** na ok. 3 000 km dróg lokalnych, głównie wiejskich. Dlatego prędkości są ustawiane jawnie w `config/network.properties`, w kolejności:

1. tag OSM `maxspeed` (także `PL:urban`, `PL:rural` itd.) przeliczony na km/h;
2. brak tagu → limit ustawowy wg typu drogi (Prawo o ruchu drogowym, art. 20): miasto 50, poza miastem 90, residential 50, living_street 20, motorway 140, trunk 100 (**ZAŁOŻENIE**: trunk 100, bo w PL to zwykle GP lub droga ekspresowa);
3. **freespeed = prędkość dozwolona × współczynnik grupy dróg** (D23, baza od D25):

| Grupa | Drogi | `f` |
|---|---|---:|
| A | autostrada | 0,95 |
| B | DK i DW poza miastem | 1,00 |
| C | tertiary i unclassified poza miastem | 0,60 |
| D | osiedlowe poza miastem | 0,70 |
| E | główne w mieście | 0,85 |
| F | lokalne w mieście | 0,55 |

Wartości są dopasowane do agregatów czasów TomTom (D22, wariant A) i zaokrąglone. To stan „na dziś”, obserwacje do dalszych prac: `reports/etap2/g5_predkosci_d23/obserwacje_f.md`. `f_E` i `f_F` nadal zawierają opóźnienia węzłów, bo zakazy skrętu (G1) ich nie rozdzieliły. Wynik D23: MAPE czasu trasy 20,5 → 18,2% (walidacja), prędkość swobodna segmentów model/TomTom 0,86 → 0,99 (`reports/etap2/g5_predkosci_d23/d23_podsumowanie.md`).

„Miasto” = gmina miejska i miasta w gminach miejsko-wiejskich z BREC (`towns.wkt`). **ZAŁOŻENIE:** wsie z zabudową traktujemy jak drogi zamiejskie (OSM nie ma granic obszaru zabudowanego).

### 5.4 Przepustowość i dynamika (nie skalibrowane)

- **Capacity** i liczba pasów: domyślne wartości Supersonic (np. tertiary 600 poj./h/pas, primary 1 500 poj./h/pas). **Nie są skalibrowane** i nie mają lokalnego źródła. Połowa opóźnień siedzi na ulicach tertiary (`reports/etap2/g6_kolejki/g6_kolejki.md`).
- **Skrzyżowania:** brak sygnalizacji i pierwszeństwa. Przepustowość to tylko właściwość linku. Eksperyment G1b (D27) z mnożnikiem przepustowości wlotów k = 0,8 / 0,6 / 0,4 nie zmienił natężeń na GPR, a przy k ≤ 0,6 podniósł opóźnienia ponad rozrzut bez niezależnej walidacji. Bazą nie został (`reports/etap3/g1_skrzyzowania/g1b.md`).
- **Dynamika kolejek:** `trafficDynamics = queue`. kinematicWaves (jak Berlin, Kelheim) dał +56% opóźnień, a przy 300 s stuck time gridlock (D18, G5 K5).
- **`qsim.stuckTime = 30 s`** (D18). Przy 10 s i `removeStuckVehicles=false` QSim wpychał pojazdy na pełne krótkie linki (82 pojazdy na linku o pojemności 1,2). Po zmianie: przepełnione linki 13 → 4–7.

### 5.5 Przypięcie aktywności do sieci

- Kandydatami są **najbliższy link** wg odległości do jego odcinka i jego link odwrotny. Wybór minimalizuje czas swobodny trasy (`snap_mode = route`, D29; `nearest` odtwarza R9). Zawrotki na początku i końcu trasy spadły z 35% do 12% podróży. Po dodaniu wypraw w R9.5 jest ich 14,3%.
- Dom na starcie i na końcu dnia to osobne linki (`home_link`, `home_link_end`). Praca ma jeden link, więc jedna zawrotka na podróż tam i z powrotem zostaje. Wariant `work_split = on` (D31) ją usuwa, ale nie jest w bazie.
- Pomijane są typy: `motorway`, `motorway_link`, `trunk`, `trunk_link`, `boundary_turnaround` (`snap_exclude_types`). Bez tego MATSim przypinałby dom do jezdni A1 (R3/E5).
- Wyjątek: wjazdy i wyjazdy na granicy zachowują swój link.

---

## 6. Popyt: kto jedzie, skąd i dokąd

### 6.1 Bilans w skali 100% (bazowy wariant B, D17)

| Składnik | Liczba | Skąd | Uwagi |
|---|---|---|---|
| Mieszkańcy pracujący w Kutnie | **14 586** | P4507 2024 (17 255) minus wyjeżdżający NSP (2 669) | Baza (B). Rozkład na obwody jak w estymacji D5. |
| Przyjeżdżający do pracy w Kutnie | **8 139** | macierz NSP (8 186) po odcięciu gmin > 100 km (D16) | Od gmin spoza powiatu odcięto 47 osób. |
| **Miejsca pracy w Kutnie łącznie** | **22 725** | suma dwóch powyższych | **Wariant C** (wrażliwość): 17 486 (BDL P4508), przeskalowane jednym współczynnikiem. |
| Wyjeżdżający z Kutna w modelu | **2 481** | macierz NSP minus 188 osób z gmin > 100 km | Wariant O1 (D17). |

Dla porównania, estymacja D5 (wskaźniki NSP × struktura wieku obwodów) dawała 20 215 pracujących mieszkańców, czyli o 17% więcej niż P4507. D5 została zastąpiona przez B w D17. **Zostaje jako rozkład na obwody** (`employed_base`).

**Co wiemy, a czego nie:** tożsamość „miejsca pracy = mieszkańcy zostający + przyjeżdżający” nie domyka się. Rejestry dają 22 725, a P4508 17 486. Różnica 30% nie ma wyjaśnienia w danych (G2, `docs/research/G2_warianty.md`). Dlatego C jest wariantem wrażliwości, a nie błędem.

### 6.2 Mieszkańcy pracujący w Kutnie (`kind = resident`)

1. Liczba pracujących: P4507 (17 255) × udział gminy. Odejmowani są wyjeżdżający (2 669).
2. Rozkład na **232 obwody spisowe** proporcjonalnie do `employed_base` (estymacja wg wieku, D5).
3. Przy skali 25% liczba agentów w obwodzie = wynik × udział auta × obecność (K1-1) × próbka, zaokrąglony metodą największych reszt, tak żeby suma była równa `round(sample × całość)`.

**ZAŁOŻENIE (D5):** wskaźniki zatrudnienia z tablic dla miast woj. łódzkiego (produkcyjny i poprodukcyjny, metoda GUS) stosujemy do grup wieku w obwodzie. Tabela ludności nie krzyżuje płci z wiekiem, więc nie wiemy, czy struktura płci zmienia wynik.

### 6.3 Przyjeżdżający do pracy w Kutnie (`kind = commuter`)

- Liczba i gminy źródłowe: macierz NSP 2021 (134 gminy, 8 186 osób).
- **Gminy w powiecie kutnowskim (D9):** dom to losowy budynek mieszkalny BDOT10k w gminie źródłowej (D28, ta sama pula i waga co mieszkańcy). Start na wjeździe do Kutna o godzinie z profilu (rozdział 9).
- **Gminy spoza powiatu (D16/A):** agent pojawia się na **wjeździe granicznym** najbliższym centroidowi gminy, o godzinie z profilu. Czasu dojazdu poza siecią nie doliczamy (**ZAŁOŻENIE**: jak D16/A; wcześniej doliczano 72 km/h × 1,3, co dawało starty po północy).
- **Odcięcie > 100 km (D16/B, ZAŁOŻENIE):** gminy, których centroid leży dalej niż **100 km** od najbliższego wjazdu, są pomijane. Obejmuje to 12 gmin (47 osób w 100%), m.in. Szczecin, Gdańsk, Kraków, Wrocław, Poznań. Warszawa (ok. 89 km od wjazdu) zostaje: 27 przyjeżdżających, a w wyjeżdżających 457 osób w macierzy NSP. Próg `max_border_km` jest w `config/kutno.toml`.
- Wjazdy: 31 linków typów `motorway`, `trunk`, `primary`, `secondary` w strefie 1 km od granicy, skierowanych do Kutna (ZAŁOŻENIE, `entry_road_types`, `entry_zone_m`).

### 6.4 Wyjeżdżający z Kutna (`kind = outbound`, D17/O1)

- Liczba i gminy docelowe: macierz NSP (83 gminy, 2 669 osób).
- **Dom:** losowy budynek mieszkalny w obwodzie Kutna, losowany wagą pracujących (jak mieszkańcy).
- **Praca:** w gminach powiatu, losowy budynek pracy w gminie docelowej. Gminy spoza powiatu: **wyjazd** (link wyjazdowy najbliższy centroidowi gminy, lustro wjazdów).
- Godzina wyjazdu z profilu, praca 8 h. Po pracy wraca po tym samym czasie, bez czasu dojazdu poza siecią (ZAŁOŻENIE).

**Dlaczego O1:** ruch istnieje i obciąża te same wloty co przyjeżdżający, w przeciwnym kierunku. Bez niego natężenia wylotowe były by zaniżone (G2).

### 6.5 Udział auta i obecność w pracy (K1-1, D19)

- Wszystkie kategorie (mieszkańcy, przyjeżdżający, wyjeżdżający) mnożone są przez:
  - **udział auta 0,64** (środek przedziału 61–67% z Bochni i Radomu; `car_share`);
  - **1 − 0,073** (praca wyłącznie z domu, łódzkie wg GUS Mobilność 2024; `work_from_home`).
  - Wynik: **× 0,593**.
- **Skutek:** plany 25% spadają z 6 302 do 3 739 osób.
- **Uwaga metodyczna:** redukcja działa na liczebności w każdej grupie (obwód, gmina), a nie przez losowe pominięcie konkretnych osób. Mieszkańcy w obwodzie z niskim udziałem auta nie są wyróżnieni.
- **Status:** przyjęte w D19. Wartości pochodzą z innych miast (**ZAŁOŻENIE**).

### 6.6 Próbka i skala

- **Skala:** 10%, 25%, 100%. Wyniki raportujemy z **25%, 5 runów** (3 seedy MATSim i 2 seedy planów), 50 iteracji (decyzja użytkownika 2026-10-23). 100% tylko na wyraźną prośbę.
- **Seedy:** 4711 (domyślny w configu), 1, 2.
- **Przepustowość skalowana do próbki:** `flowCapacityFactor = storageCapacityFactor = sampleSize` (MATSim 2026 wymaga ich równości, D8, D15/5).
- Wyniki w skali 100% odtwarzamy przez `× 1/sampleSize` (dotyczy natężeń i GEH; `convergence.py` robi to sam).

### 6.7 Wyjścia mieszkańców (`errands.py`, D32, D34, D36)

Osobne wyjścia `home → cel → home`, tylko kierowca auta. Agent wyprawy jest osobną osobą, niepowiązaną z pracującym (**ZAŁOŻENIE**).

- **Liczba wyjść** = stawka GUS Mobilność 2024 (tabl. 10, łódzkie, na 2 146 153 osób 6+) × populacja Kutna 6+ × `errand_car_share` × próbka.
- **`errand_car_share` = 0,424** (**ZAŁOŻENIE**): Radom GOFR 2022, podróże fakultatywne 53,2%, × 0,797 (kierowcy wśród jazd autem, GUS łódzkie). Warianty 0,304 i 0,479.
- **Uczestnicy:** wiek ≥ 18, `license = yes`, `carAvail ≠ never`, waga wg wieku z GUS Budżet czasu 2023.
- **Godzina:** GBR Gdańsk 2022 „dom–inne”, przedziały 5–20 h.

| Typ | Cel | Postój | Stawka GUS (podróże dom–X) | Wyjścia w planie 25% |
|---|---|---:|---:|---:|
| `shop`, `service` | sklepy OSM (D34): `supermarket`, `mall`, `department_store` i pozostałe `shop=*`, waga = liczba sklepów; usługi z BDOT10k, waga = obrys | 57 min | 102 892 + 229 380 + 25 702 | 711 |
| `visit` | budynki mieszkalne | 1 h 28 min | 70 062 | 139 |
| `leisure` | kultura, sport, gastronomia (BDOT10k) | 1 h 36 min | 90 163 | 179 |
| `health` | ochrona zdrowia, szpital, apteka (BDOT10k) | 57 min | 78 397 | 156 |
| `escort` | najbliższa szkoła podstawowa, przedszkole, żłobek | 5 min | 146 725 | 292 |

Razem 1 477 wyjść w planie 25%. Wybór celu nie zależy od odległości (poza `escort`). Pomiar wariantów z odległością pokazał w Kutnie prawie brak efektu (`reports/etap3/g_zakupy/odleglosc/pomiar_beta.md`). Czas dla `health` jest **ZAŁOŻENIEM** (jak zakupy, brak kategorii w GUS).

### 6.8 Ruch tła (`background_od.py`, D19–D21)

Subpopulacje `tlo` (lekkie i dostawcze, pce 1,0) i `ciezkie` (pce 2,5, 80 km/h). Macierze `scenarios/kutno/demand/background_od_r94e_{lcv,heavy}_gpr.csv` są estymowane z GPR 2025 względem runów pracujących i wyjść bez tła. W planie 25%: 11 961 agentów `tlo` i 4 840 `ciezkie`, profil godzin ze stacji Lisica. Strefy graniczne per droga z wagą GPR, końce ciężkich w budynkach pracy (`pipeline/border_zones.py`). Znane ograniczenia: strefy DK91 płn.-zach. i płd.-zach. oraz DK92 wsch. bez ograniczenia przez GPR (D25).

---

## 7. Lokalizacje: skąd są domy i miejsca pracy

Domy mieszkańców są **budynkami BDOT10k** z wagą **obrys × kondygnacje** (D28). Miejsca pracy są **budynkami OSM** z wagą **powierzchni obrysu** (D7). Końce ruchu tła to budynki OSM. Losowanie jest z powtórzeniami, a seed jest w configu (`seed = 4711`). Cele wyjść mieszkańców: rozdział 6.7.

### 7.1 Filtry budynków

**Mieszkalne, BDOT10k** (`home_source = "bdot"`, ZAŁOŻENIE D28): `OT_BUBD_A` powiatu 1002, `KATEGORIAISTNIENIA = eksploatowany`, funkcja przeważająca „budynek jednorodzinny” albo „budynek wielorodzinny” (19 520 z 19 644 budynków mieszkalnych w powiecie). Odrzucone m.in. domy letniskowe, parafialne, opieki społecznej, internaty, klasztory. Wariant `home_source = "osm"` odtwarza stan R7b/R8.

**Pracy, OSM** (`work_buildings`, ZAŁOŻENIE D7): `retail`, `industrial`, `warehouse`, `office`, `commercial`, `school`, `hospital`, `public`, `civic`, `government`, `kindergarten`, `university`, `college`, `supermarket`, `service`, `fire_station`, `train_station`, `transportation`, `manufacture`, `factory`, `hotel`, a także każdy budynek z tagiem `amenity`/`shop`/`office` i `building=yes` w landuse `industrial`, `commercial`, `retail`. Tylko w granicach gminy Kutno (dla agentów z Kutna).

**Wykluczenia z danych OSM:**
- `building=no` traktujemy jak brak budynku (plac komisu z `shop=car`, 3,6 ha, był największym „miejscem pracy”, R3/błąd 1).
- Budynek mieszkalny OSM nie może być budynkiem pracy (`loc[work, residential] = False`).

### 7.2 Domy

- **Mieszkańcy:** budynek BDOT10k w obwodzie spisowym, waga obrys × `LICZBAKONDYGNACJI` (brak = 1). Obwód bez kandydata bierze najbliższy dom do 100 m (`home_nearest_max_m`, ZAŁOŻENIE), inaczej losowy punkt w obwodzie (obwód 6509214).
- **Przyjeżdżający z powiatu:** ta sama pula domów, losowy budynek w gminie źródłowej.
- **Przyjeżdżający spoza powiatu i wyjeżdżający spoza powiatu:** nie mają domu w Kutnie. Start/koniec na linku granicznym.

**Zgodność z siatką GUS 250 m:** odchylenie masy 10,3 pp (OSM) → 8,1 pp (BDOT10k). Ruch bez zmian ponad rozrzut planów (`reports/etap3/g3_domy/g3.md`).

### 7.3 Miejsca pracy

- Losowanie z **wagą powierzchni obrysu** z listy budynków pracy w gminie Kutno. Kandydatów: 1 103, wylosowano 473 budynki w 10% (F4).
- Top 5 budynków dostaje 13% agentów (duże hale w strefie wschodniej). Są to realne obiekty (`industrial` i `warehouse`, 1,6–3,1 ha), sprawdzone w kontroli przed runem (D16).
- **ZAŁOŻENIE:** rozkład zatrudnienia wewnątrz gminy odwzorowany przez powierzchnię budynków. Nie ma REGON ani adresów zakładów w modelu (D7, G2 otwarte).

### 7.4 Przypisanie linku sieci

Każdy dom i miejsce pracy dostaje link sieci według zasad z rozdziału 5.5 (`snap_mode = route`, D29). Przyjeżdżający i wyjeżdżający spoza powiatu mają link graniczny od razu.

---

## 8. Cechy agentów: co wiemy o osobie

Agenty tworzy się z **agregatów**, nie z mikrodanych. Nie odtwarzamy gospodarstw (zasady projektu). Atrybuty z D30 nie wpływają na QSim: strategie to tylko `ChangeExpBeta` i `ReRoute`. Test na GitHub Actions dał identyczne trasy, nogi, natężenia i score (run 40189940976).

| Atrybut | Wartość | Skąd |
|---|---|---|
| `subpopulation` | `person`, `tlo`, `ciezkie` | stała (wymagana przez SimWrapper i strategie) |
| `kind` | `resident` / `commuter` / `outbound` | rodzaj popytu (6.2–6.4) |
| `id` | `r<obwód>_<n>`, `c<gmina>_<n>`, `o<gmina>_<n>`, `h…` dla ciężkich | unikalne (test w `plans.py`) |
| dom | budynek BDOT10k i link | rozdział 7.2 |
| praca lub cel wyjścia | budynek i link | rozdziały 6.7, 7.3 |
| godzina wyjazdu | z profilu GBR (rozdział 9) | losowana z przedziału |
| `age`, `sex` | populacja × zatrudnienie (miasta Polski) × P(licencja) | BDL P4181, NSP 2021 (D30) |
| `license` | yes/no | CEPiK 2019 / NSP 2021, przesunięcie do 60,6% w Łódzkiem (GUS Mobilność 2024); mężczyźni 65+ jak 55–64 (**ZAŁOŻENIE**) |
| `carAvail` | always / sometimes / never | auta / posiadacze prawa jazdy w Łódzkiem = 0,73 (**ZAŁOŻENIE**: jedno auto = jeden posiadacz) |

Pełna populacja Kutna (42 255 osób z atrybutami) jest w `scenarios/kutno/demand/population_kutno.csv`. Raport: `reports/etap3/g_atrybuty/atrybuty.md`.

**Czego agenci NIE mają:** wykształcenia, zawodu, dochodu, gospodarstwa domowego. Wiek przyjeżdżających pochodzi z rozkładu Kutna, nie z ich gmin.

---

## 9. Plany dnia: łańcuch i godziny

**Łańcuch pracującego:** `home (end_time = wyjazd) → car → work (max_dur = 8:00:00) → car → home`. **Wyjście mieszkańca:** `home → car → cel (max_dur wg typu, rozdział 6.7) → car → home`. Test: trzy aktywności i dwie nogi car, `end_time` XOR `max_dur` (zasady projektu). Łańcuchy dnia pracujących (podwiezienie przed pracą, zakupy po pracy) są wariantem `chains = on` (D35), nie bazą.

**Godzina wyjazdu pracujących (D14):**
1. Losowanie przedziału godzinowego z rozkładu „dom–praca” GBR Gdańsk 2022, Rys. 46 (`config/departure_home_work_gbr2022.csv`, 18 przedziałów, po normalizacji do 100%). Przedział 20–24 h jest jednym przedziałem 4-godzinnym.
2. Godzina jednostajnie losowana w przedziale (**ZAŁOŻENIE**).
3. Wyjazd z domu = ta godzina. Przyjeżdżający z granicy: godzina wejścia na granicę.

**Ograniczenia godzin:**
- Rozkład jest z metropolii Gdańsk (**ZAŁOŻENIE**, że pasuje do Kutna).
- Brak godzinowego rozkładu lokalnego (decyzja D10 otwarta, R1: `docs/research/R1_godziny.md`). Przegląd polskich badań ruchu pod ten i inne parametry: `docs/research/badania_ruchu_PL.md`.
- Start najpóźniej o 23:52.

**Czas pracy 8 h** (`work_max_dur`): **ZAŁOŻENIE** zaokrąglone z GUS BCL 2013 (8 h 11 min średnio dla najemnych). Nie jest to rozkład per agent. `TimeAllocationMutator` **wyłączony** (godziny z danych nie mają dryfować).

**Koniec symulacji:** `qsim.endTime = 48:00:00` (zapas; 36:00 przerywało agenta z Krakowa, `stuckAndAbort`, R3).

---

## 10. Symulacja MATSim (konfiguracja)

Pliki: `scenarios/kutno/config_{10,25,100}pct.xml`. Ścieżki są względne do configu. `controller.outputDirectory` jest względny do katalogu roboczego, więc uruchamiaj z katalogu projektu.

| Parametr | Wartość | Uzasadnienie |
|---|---|---|
| MATSim | 2026.0, Java 25 | `matsim/` (matsim-example-project @ 74d23af) |
| `lastIteration` | 100 w configu; runy GitHub Actions 50 (`--iterations`) | decyzja użytkownika 2026-10-23: nowe runy maks. 50 iteracji |
| `flowCapacityFactor` = `storageCapacityFactor` | = sampleSize (0,25 dla 25%) | D8, MATSim 2026 wymaga równości |
| `stuckTime` | 30 s | D18 |
| `trafficDynamics` | `queue` | D18, G5 K5 |
| `endTime` | 48:00:00 | rozdział 9 |
| `randomSeed` | 4711 (1, 2 dla wariancji) | config |
| `coordinateSystem` | EPSG:2180 | zasady projektu (D-spec) |
| `numberOfThreads` | 8 w configu; runy 4 lub 2 wątki | liczba wątków nie skraca runu, 4 i 8 dają identyczne wyniki |
| `linkDynamics` | `PassingQ` | D20: osobowe wyprzedzają ciężkie (80 km/h) |
| Strategie | `ChangeExpBeta` 0,8, `ReRoute` 0,2 | osobno dla `person`, `tlo`, `ciezkie` |
| `fractionOfIterationsToDisableInnovation` | 0,8 | po 80 iteracjach tylko wybór planu (score spłaszcza się z definicji) |
| Scoring | domyślny MATSim; typical: `home` 16 h, `work` 8 h, `shop` i `service` 57 min, `visit` 1 h 28 min, `leisure` 1 h 36 min, `health` 57 min, `escort` 5 min | **ZAŁOŻENIE**, score tylko diagnostyczny |
| Plany | `plans_g3r95_{10,25,100}pct` | baza R9.5 (D36) |
| SimWrapper, linkStats | włączone; linkStats co 10 it. (średnia z 5) | R3/E2, diagnostyka zbieżności |

**Co jest w wyjściu:** `output_events.xml.zst` (eventy, format `.zst`), `output_links.csv.zst`, `modestats`, `scorestats`, `traveldistancestats` (MATSim). Wykresy: `pipeline/plot_run.py`.

**Co MATSim robi z nogami:** przy trybie `car` MATSim sam dokleja teleportowane nogi `walk` (dojście i odejście). Nie są częścią modelu ruchu, tylko trzeba je odfiltrować przy liczeniu nóg.

---

## 11. Walidacja i wyniki

### 11.1 Testy

| Test | Skrypt | Co sprawdza |
|---|---|---|
| Eventy | `pipeline/check_events.py` | `departure = arrival`, 0 `stuck` (także `stuckAndAbort`), liczba nóg car = liczba w planach |
| Plany | `pipeline/validate_plans.py` | łańcuch, obszar, praca w gminie Kutno, liczba osób, powtarzalność sha256 |
| Sieć | `pipeline/validate_network.py` | obszar, SCC, atrybuty, trasy testowe |
| Popyt | `pipeline/demand.py` (asercje) | suma ludności 42 255, 8 186 przyjeżdżających, złączenie 232/232 |
| Przepełnienie linków | `pipeline/queues.py` | `overfilled_links_gt2x` (D18) |
| Zbieżność | `pipeline/convergence.py` | zmiana natężeń top-50 linków, GEH między seedami (skala 100%) |
| Model vs GPR | `pipeline/g5_baseline.py` | model / GPR na 19 odcinkach (A1, DK, DW) |
| Model vs ulice miejskie | `pipeline/pomiary_miejskie.py` | model / WIOŚ 2013 K1–K5 przeskalowane do 2025 (kontrola, nie kalibracja) |
| Macierze O-D | `pipeline/od_warnings.py` | ostrzeżenia po każdej estymacji |

**Zasada projektu:** run bez błędu nie jest dowodem. Fazę zalicza test semantyczny.

### 11.2 Baza R9.5 (test GitHub Actions, 2026-10-31)

Źródło: `reports/etap3/g_inne_cele/inne_cele.md`, `inne_cele_porownanie.json`, run 41200518829. 25%, 50 iteracji, mediana z 5 runów (3 seedy MATSim i 2 seedy planów), kontrola R9.4 na tej samej platformie.

| Miara | R9.5 | R9.4 | Rozrzut planów R9.4 |
|---|---:|---:|---:|
| stuck | 0 | 0 | – |
| nogi car = plany | tak (27 233) | tak (25 701) | – |
| opóźnienie, poj.-h próbki | 243,8 | 236,5 | 17,8 |
| GPR lekkie w ±15% | 15/15 | 15/15 | – |
| GPR ciężkie w ±15% | 14/15 (poza: 91878, −15,1%) | 13/15 | – |
| podróże pracujących: czas / dystans | 17,15 min / 11,11 km | 17,13 min / 11,11 km | 0,26 min |
| zawrotki na starcie lub końcu trasy, % podróży | 14,3 | 13,5 | – |
| ulice miejskie K1–K5, suma, % celu 2025 | 43,6 | 40,9 | – |

**Ulice miejskie (D37), znane ograniczenie:**

| Punkt | Cel 2025 [poj./dobę] | R9.5 | % celu |
|---|---:|---:|---:|
| K1 Toruńska | 12 910 | 2 876 | 22,3 |
| K2 Łąkoszyńska | 8 367 | 3 884 | 46,4 |
| K3 Grunwaldzka | 3 805 | 3 280 | 86,2 |
| K4 Kościuszki | 4 208 | 2 500 | 59,4 |
| K5 Łęczycka | 9 850 | 4 536 | 46,0 |

Cel to pomiar jednodobowy z 2013 przeskalowany przez GPR, więc to kontrola rzędu wielkości. Po D36 nie dokładamy popytu ani nie stroimy parametrów pod K1–K5. Brakuje m.in. przyjazdów spoza miasta w celach innych niż praca, podróży nie z domu, ruchu służbowego i dostawczego w mieście oraz szkoły (`reports/etap3/g_pomiary_miejskie/popyt_brak.md`, `k1_zachod.md`).

**Rozrzut:** losowanie planów i punktów estymacji O-D daje 20–100 razy większy rozrzut niż seedy MATSim (mediana 9–12% na odcinek wobec 0,1–0,4%, baza R6). Różnice wariantów oceniaj względem rozrzutu seedów planów.

**Czasy:** walidacja względem TomTom (D22, D25) dotyczy R7b: 58% tras w 15% lub 1 min wobec wymaganych > 85% wg TAG. Model jest skalibrowany w popycie, nie zwalidowany co do czasów. Późniejszych baz nie sprawdzaliśmy nowymi zapytaniami.

### 11.3 Jak zmieniała się baza

Każdy krok zmienia jedną rzecz, a zmiany ruchu oceniamy względem rozrzutu seedów planów.

| Baza | Decyzja | Co doszło | Efekt | Raport |
|---|---|---|---|---|
| R6 | D19–D21 | tło, dostawcze i ciężkie, poprawki po audycie G5 | GPR lekkie 12/15, ciężkie 12/15 | `reports/etap2/g5_kalibracja/g5_r6_ref.md` |
| R7b | D23, D25 | prędkości per grupa dróg | GPR lekkie 14/15, MAPE czasu 20,5 → 18,2% | `reports/etap2/g5_predkosci_d23/d23_podsumowanie.md` |
| R8 | D26 | zakazy skrętu | poniżej rozrzutu seedów | `reports/etap3/g1_skrzyzowania/g1.md` |
| R9 | D28 | domy z BDOT10k | GUS 250 m: 10,3 → 8,1 pp; ruch w rozrzucie | `reports/etap3/g3_domy/g3.md` |
| R9.1 | D29 | kierunek linku wg trasy | zawrotki 35,1 → 12,4% podróży | `reports/etap3/g_zawrotki/zawrotki.md` |
| R9.2 | D30 | atrybuty osób | symulacja bez zmian | `reports/etap3/g_atrybuty/atrybuty.md` |
| R9.3 | D32 | zakupy i usługi | opóźnienie +5,8% (rozrzut 13,9%), GPR lekkie 15/15 | `reports/etap3/g_zakupy/zakupy.md` |
| R9.4 | D34 | cele zakupów wg sklepów OSM | wyprawy krótsze o 16% km, reszta w rozrzucie | `reports/etap3/g_zakupy/cel_osm/cel_osm.md` |
| R9.5 | D36 | odwiedziny, rekreacja, zdrowie, podwożenie | K1–K5 40,9 → 43,6% celu, GPR w rozrzucie | `reports/etap3/g_inne_cele/inne_cele.md` |

Warianty sprawdzone, ale poza bazą: G1b (D27, przepustowość wlotów), `work_split` (D31, zawrotki 12,4 → 1,1%), `chains` (D35, łańcuchy dnia, ruch w rozrzucie). Wyniki sprzed tła (D18, R1) są historyczne: `reports/etap2/g6_kolejki/g6_kolejki.md`, `reports/etap2/g5_kalibracja/`.

---

## 12. Założenia (zbiorcza tabela)

Każde ZAŁOŻENIE ma wartość, miejsce w kodzie lub configu, uzasadnienie i status.

| ID | Założenie | Wartość | Gdzie | Uzasadnienie / status |
|---|---|---|---|---|
| A-1 | Zasięg sieci = powiat + bufor | 3 000 m | `config/kutno.toml` `network_buffer_m` | D9, do weryfikacji w F2 (otwarte: szerokość poza powiatem) |
| A-2 | Zawrotki na granicy | 300 m, 30 km/h, cap 5 000, strefa 1 km | `config/network.properties` | F2 (A1), D9 |
| A-3 | Prędkość = limit × `f` grupy dróg | A 0,95, B 1,00, C 0,60, D 0,70, E 0,85, F 0,55 | `config/network.properties` | D23, D25; dopasowane do agregatów TomTom, „na dziś” |
| A-4 | Wsie jak drogi zamiejskie | rural 90 | `config/network.properties` | brak granic obszaru zabudowanego w OSM |
| A-5 | Trunk = 100 km/h | trunk 100 | `config/network.properties` | GP lub ekspresówka, do potwierdzenia |
| A-6 | Capacity domyślne Supersonic | tertiary 600, primary 1 500 poj./h/pas | MATSim | **nieskalibrowane**, brak źródła lokalnego (G1, G5 K5) |
| A-7 | Pracujący mieszkańcy | P4507 2024 = 17 255 | `config/kutno.toml` `employed_residents_reg` | D17/B, rejestr |
| A-8 | Wariant liczby miejsc pracy | B (baza), C = 17 486 | `config/kutno.toml` `jobs_total` | D17, luka 30% nieobjaśniona |
| A-9 | Wyjeżdżający w modelu | O1, rok kotwicy 2024 | `plans.py`, `demand.py` | D17, G2 |
| A-10 | Wskaźniki zatrudnienia | produkcyjny 0,784 (bazowy), poprodukcyjny wg TABL. 5 | `demand.py` (rozkład obwodów) | D5, tylko województwo |
| A-11 | Przedział 0–17 dla grupy przedprodukcyjnej | wskaźnik województwa | `demand.py` | D5 |
| A-12 | Odcięcie gmin > 100 km od wjazdu | 100 km | `config/kutno.toml` `max_border_km` | D16/B, decyzja użytkownika |
| A-13 | Start przyjeżdżającego z granicy | godzina z profilu, bez dojazdu | `plans.py` | D16/A |
| A-14 | Wjazd: typ linku | motorway, trunk, primary, secondary; strefa 1 km | `config/kutno.toml` `entry_road_types`, `entry_zone_m` | D9 |
| A-15 | Dom przyjeżdżającego z powiatu | losowy budynek w gminie źródłowej | `plans.py` | D9 |
| A-16 | Budynki mieszkalne (BDOT10k) i pracy (OSM) | rozdział 7.1 | `config/kutno.toml` | D28, D7 |
| A-17 | Wagi: domy obrys × kondygnacje, praca obrys | m² | `plans.py` | D28, D7 |
| A-18 | Obwód bez budynku → najbliższy dom do 100 m, inaczej losowy punkt | 100 m | `config/kutno.toml` `home_nearest_max_m` | D28, dotyczy obwodów 6509902 i 6509214 |
| A-19 | Udział auta dom–praca | 0,64 (61–67%) | `config/kutno.toml` `car_share` | D19/K1-1, Bochnia 2016, Radom 2022 |
| A-20 | Praca z domu | 7,3% | `config/kutno.toml` `work_from_home` | GUS Mobilność 2024, tabl. 1 |
| A-21 | Profil godzin wyjazdu | GBR Gdańsk 2022 | `config/departure_home_work_gbr2022.csv` | D14, metropolia, nie Kutno |
| A-22 | Godzina jednostajnie w przedziale | — | `plans.py` | ZAŁOŻENIE D14 |
| A-23 | Czas pracy 8 h | 08:00:00 | `config/kutno.toml` `work_max_dur` | GUS BCL 2013, zaokrąglone |
| A-24 | Brak TimeAllocationMutator | — | config | godziny z danych |
| A-25 | Scoring: typical duration wg typu aktywności | rozdział 10 | `config_*.xml` | domyślne MATSim, score diagnostyczny |
| A-26 | Próbka i zaokrąglanie | 25% (wyniki), metoda największych reszt | `plans.py` | D15/3, D8 |
| A-27 | Seedy | 4711, 1, 2 | config, `output/r3_runs.sh` | D15 |
| A-28 | `stuckTime` | 30 s | config | D18, Berlin/Kelheim |
| A-29 | Dynamika `queue` | — | config | D18, G5 K5 |
| A-30 | Ruch tła z estymacji O-D (lekkie + dostawcze, ciężkie) | 20 punktów na gminę, τ = 30 min, waga wjazdu = capacity | `pipeline/background_od.py` | D19–D21; estymacja kalibrowana do GPR, rozrzut zależy od seedu punktów |
| A-31 | Brak pieszych, rowerzystów i PT; ciężkie tylko jako tło (pce 2,5, 80 km/h) | — | — | D6, D20; kroki 5–6 w ROADMAP |
| A-32 | Opóźnienia na linku, nie na skrzyżowaniu; zakazy skrętu tylko w routerze | — | — | D26; sygnalizacja później |
| A-33 | Dzień roboczy | — | — | typowy dzień roboczy (GUS, GBR) |
| A-34 | Kierunek linku wg trasy swobodnej, bez zakazów skrętu | `snap_mode = route` | `config/kutno.toml` | D29 |
| A-35 | Atrybuty: mężczyźni 65+ jak 55–64; jedno auto = jeden posiadacz prawa jazdy | 0,73 | `config/kutno.toml`, `pipeline/attributes.py` | D30 |
| A-36 | Udział kierowcy w wyjściach mieszkańców | 0,424 (warianty 0,304, 0,479) | `config/kutno.toml` `errand_car_share` | D32, Radom GOFR 2022 × GUS łódzkie |
| A-37 | Wyjście = osobny agent, bez powiązania z pracującym | — | `pipeline/errands.py` | D32 |
| A-38 | Godziny wyjść = GBR Gdańsk „dom–inne” | przedziały 5–20 h | `config/departure_home_inne_gbr2022.csv` | D32, metropolia, nie Kutno |
| A-39 | Czasy postoju | rozdział 6.7 | `config/kutno.toml` | D32, D36, GUS Budżet czasu 2023; `health` jak zakupy |
| A-40 | Cele: bez zależności od odległości (poza `escort`) | waga wg rozdziału 6.7 | `pipeline/errands.py` | D32, D34, D36 |
| A-41 | Sklepy: wszystkie `shop=*` poza `vacant`, Eurocash w typie c, OSM niekompletny | do 15 m od budynku | `config/kutno.toml` `errand_poi_m` | D34 |

---

## 13. Ograniczenia, znane problemy i luki

### 13.1 Zgodność konfiguracji

- **R-1: `scenarios/kutno/plans.xml.gz` i `plans_25pct_bez_k1`** to pliki z etapów F5–D18, nieużywane przez obecne configi. `config_{10,25,100}pct.xml` wskazują plany `plans_g3r95_*pct`.
- **R-2: brak jednego skryptu odtwarzającego całość.** Kolejność jest w rozdziale 2, a przepisy przy poszczególnych bazach są w raportach. `output/r3_runs.sh` jest poza gitem, a nowe runy i tak idą przez GitHub Actions.
- **R-3:** `config_25pct.xml` ma 8 wątków, a runy na GitHub Actions używają 2 (`threads`). Wątki nie skracają runu, a 1 wątek daje inne wyniki niż 4 i 8.

### 13.2 Ograniczenia danych i metody

- Macierz NSP: tylko pracownicy najemni, bez przepływów < 3 osób i bez ruchu wewnątrz gminy. Dolna granica odpływu i napływu (zaniża ruch).
- Miejsce pracy w macierzy = adres pracodawcy (siedziba). Dalekie relacje (Warszawa 457) mogą być efektem siedziby firmy, nie realnego dojazdu.
- Wskaźniki zatrudnienia tylko na poziomie województwa. Estymacja D5 jest o 17% wyższa od rejestru.
- Pracujący per obwód (232) to estymacja, nie obserwacja (D5).
- Dane OSM: 72% budynków gminy ma `building=yes` bez typu, a `building:levels` jest w nich tylko w 2%. Wagi miejsc pracy (powierzchnia obrysu) są więc przybliżone.
- Stawki wyjść mieszkańców pochodzą z całego województwa i dotyczą wszystkich środków transportu. Udział kierowcy jest z Radomia i Łódzkiego.
- Dane godzinowe wyjść i dojazdów są z Gdańska. Lepsze wzorce dla miast średnich: `docs/research/badania_ruchu_PL.md`.
- 1 450 budynków OSM w Kutnie nie ma odpowiednika w BDOT10k (G3).
- Atrybuty osób nie krzyżują się z obwodem spisowym: wiek i płeć agenta nie wynikają ze struktury jego obwodu.

### 13.3 Ograniczenia modelu

- **Ulice miejskie poza GPR są zaniżone mniej więcej o połowę (D37):** K1–K5 43,6% celu, Toruńska 22%. Na drogach z GPR model mieści się w ±15%, ale przekroje GPR są głównie tranzytowe, więc ruchu w mieście nie sprawdzają.
- Brak sygnalizacji i pierwszeństwa. Zakazy skrętu tylko w routerze. Kolejki są wynikiem capacity linku i `stuckTime`, nie konfliktów na skrzyżowaniu.
- Czasy przejazdu nie są zwalidowane wg TAG (D25), a po R7b nie sprawdzano ich nowymi zapytaniami.
- Brak czasu w czasie dojazdu poza siecią: przyjeżdżający i wyjeżdżający „teleportują się” na granicę (ZAŁOŻENIE, D16/A).
- Jeden typowy dzień roboczy, bez weekendu i świąt.
- Brak losowej zmienności czasu pracy per agent (stałe 8 h).
- Scoring domyślny: wybór trasy jest prawdziwy, ale score nie jest kalibrowany i nie służy do wniosków. Strategie to tylko wybór planu i trasy, bez zmiany godzin i trybu.
- Wszyscy agenci jadą autem, więc atrybuty osób i rozkład GTFS jeszcze niczego nie zmieniają w symulacji.
- Wyniki wrażliwe nieliniowo na popyt (C vs B: opóźnienia −71% przy −22% popytu). Liczba miejsc pracy jest najczulszym parametrem.

---

## 14. Luki: czego jeszcze nie ma

Stan na 2026-11-03. Pełna lista otwartych spraw i kolejność: `docs/projekt/ROADMAP.md`.

| # | Luka | Stan | Gdzie opisane |
|---|---|---|---|
| L-1 | **Ruch na ulicach miejskich** poza GPR zaniżony ok. o połowę. | znane ograniczenie (D37), do kroku 6 lub nowych danych | `reports/etap3/g_pomiary_miejskie/popyt_brak.md` |
| L-2 | **Szkoła** jako cel podróży. | plan bez wdrożenia, czeka na decyzję (D33) | `docs/research/G_szkola_4B_plan.md` |
| L-3 | **Transport publiczny, rower, pieszo, wybór trybu**. GTFS zaimportowany technicznie (22 linie, 446 kursów), bez agentów PT i bez kalibracji ASC. | kroki 5–6 | `reports/etap3/g_pt_import/pt_import.md`, `docs/research/G4_tryby.md` |
| L-4 | **Łańcuchy dnia** pracujących. | wariant gotowy (`chains = on`), czeka na decyzję (D35) | `reports/etap3/g_lancuchy/lancuchy.md` |
| L-5 | **Odległość w wyborze celu** wyjść. | pomiar bez wdrożenia, w Kutnie prawie bez efektu | `reports/etap3/g_zakupy/odleglosc/pomiar_beta.md` |
| L-6 | **Rozkład miejsc pracy w gminie**: wagi według powierzchni budynków, bez REGON i adresów zakładów. | znane ograniczenie G2 | `docs/research/G2_miejsca_pracy.md` |
| L-7 | **Udział auta K1-1**: źródło z innych miast, brak danych lokalnych. | decyzja podjęta, dane słabe | `docs/research/G5_plan_kalibracji.md` |
| L-8 | **Godziny wyjazdu z lokalnego źródła** (D10): dziś GBR Gdańsk, w tle profil Lisica. | research | `docs/research/R1_godziny.md`, `docs/research/badania_ruchu_PL.md` |
| L-9 | **Czas pracy 8 h**: stałe ZAŁOŻENIE, bez rozkładu per agent. | research | `docs/research/R1_godziny.md` |
| L-10 | **Capacity ulic miejskich i sygnalizacja**: brak danych lokalnych, G1b bez walidacji. | ewentualnie po G1 | `reports/etap3/g1_skrzyzowania/g1b.md` |
| L-11 | **Prędkości `f`**: wartości „na dziś”, ponowna walidacja czasów wymaga zgody na nowe zapytania (D22). | otwarte | `reports/etap2/g5_predkosci_d23/obserwacje_f.md` |
| L-12 | **Odtworzenie od zera** na czystym klonie i jeden skrypt. | krok 8 | `docs/projekt/ROADMAP.md` |

Pytania otwarte z `docs/projekt/DECISIONS.md`, bez decyzji: szerokość bufora poza powiatem, parametry scoringu, rozkład czasu pracy.

---

## 15. Struktura projektu

| Ścieżka | Zawartość | W gicie |
|---|---|---|
| `docs/projekt/ROADMAP.md` | fazy, stan, dalsze plany | tak |
| `docs/projekt/DECISIONS.md` | decyzje D1–D37 (zmiana = nowy wpis) | tak |
| `docs/projekt/FACT_CHECK.md` | zweryfikowane fakty z raportów AI | tak |
| `docs/projekt/TASKS.md` | kontrakty faz F0–F6 i etapu 2 | tak |
| `docs/projekt/PROGRESS.md` | co zaliczono, z dowodem | tak |
| `docs/projekt/ERRORS.md` | błędy i reguły | tak |
| `config/` | `kutno.toml`, `network.properties`, profile godzin, uczestnictwo w wyjściach | tak |
| `data/manifest.csv` | URL, data, bajty i SHA-256 każdego pobrania | tak |
| `data/raw/` | pobrane źródła (tylko do odczytu) | nie |
| `pipeline/` | skrypty Python (dane, plany, analiza, walidacja) | tak |
| `matsim/` | projekt Java (`CreateKutnoNetwork`, `mvnw`) | tak |
| `.github/workflows/` | runy MATSim i estymacja O-D (rozdział 2) | tak |
| `scenarios/smoke/` | test regresyjny, 10 agentów | tak |
| `scenarios/kutno/` | sieć, plany, configi, popyt CSV (`*.xml.gz` wyłączone z gita) | częściowo |
| `scenarios/kutno_r91/` | wejścia testów GHA: plany, pojazdy, meta wariantów `p0`–`p2`, także R9.5 (`r94e`) | tak |
| `scenarios/kutno_od/` | wejścia estymacji O-D: plany bez tła, config | tak |
| `scenarios/kutno_pt/` | import GTFS: rozkład, pojazdy, sieć z linkami PT (`pipeline/build_kutno_pt.sh`) | tak |
| `scenarios/kutno_g1b/`, `scenarios/kutno_r7b_*` | wejścia testów historycznych | tak |
| `reports/` | raporty i dowody per faza (`reports/README.md`) | tak |
| `docs/research/` | analizy i tło metodyczne | tak |
| `docs/ZRODLA.md` | katalog źródeł | tak |
| `output/` | runy MATSim | nie |

Odtwarzacz runów (wizualizer) jest w osobnym repozytorium, [easy-matplayer](https://github.com/GISBoost/easy-matplayer).

**Wyniki referencyjne (aktualne):** baza R9.5, `reports/etap3/g_inne_cele/inne_cele.md` (25%, 3 seedy MATSim + 2 seedy planów, 50 iteracji). Wcześniejsze bazy: rozdział 11.3.

---

## 16. Słownik

| Skrót | Znaczenie |
|---|---|
| BDL | Bank Danych Lokalnych GUS. P4507 = pracujący mieszkańcy, P4508 = pracujący wg siedziby płatnika |
| BDOT10k | Baza Danych Obiektów Topograficznych (budynki, kondygnacje) |
| BREC | Baza Rejestrów Ewidencyjnych Charakterystyk (rejony i obwody spisowe NSP 2021) |
| CRS EPSG:2180 | układ PUWG 1992, osie E, N |
| D1–D37 | decyzje projektowe (`docs/projekt/DECISIONS.md`) |
| GEH | miara zgodności natężeń (< 5 = dobra zgodność) |
| GPR | Generalny Pomiar Ruchu GDDKiA (SDRR, SDRDR, SDRL) |
| GBR | Gdański Biuro Rozwoju, Raport 3a (badanie mobilności, profil godzin) |
| GTFS | rozkład jazdy transportu publicznego (format) |
| K1–K5, G1–G7 | kroki kalibracji (`G5_plan_kalibracji.md`) i etapy projektu (`docs/projekt/TASKS.md`). W rozdziale 11 K1–K5 to punkty pomiarowe WIOŚ 2013 |
| GHA | GitHub Actions |
| R6…R9.5 | kolejne bazy modelu (rozdział 11.3) |
| WIOŚ | Wojewódzki Inspektorat Ochrony Środowiska |
| MVP | pierwszy zakres modelu, zamknięty: samochód, dom–praca–dom |
| NSP 2021 | Narodowy Spis Powszechny 2021 |
| O-D | macierz podróży (origin–destination) |
| PCE | współczynnik ekwiwalentu samochodu osobowego (ciężarówki) |
| QSim | silnik symulacji kolejkowej MATSim |
| SCPR | Stacje Ciągłych Pomiarów Ruchu (GDDKiA) |
| SDRDR | średni dobowy ruch w dni robocze (GPR) |
| TERC | identyfikator jednostki terytorialnej (1002011 = gm. miejska Kutno) |
| TABL. 5 | tablica GUS „Ludność na rynku pracy” (wskaźniki zatrudnienia) |

## 17. Licencja

- **Kod** (`pipeline/`, `matsim/src/`, skrypty w `reports/` i `docs/`): GPL-3.0-or-later, plik [LICENSE](LICENSE).
- **Dane i wyniki z GUS**: CC BY 4.0 (wymagane podanie źródła: Główny Urząd Statystyczny).
- **Dane z OpenStreetMap**: ODbL 1.0 (© OpenStreetMap contributors). Wyprowadzone bazy z danymi OSM publikujemy na ODbL.
- **Przykładowy projekt MATSim** w `matsim/`: GPL-2.0-or-later, plik `matsim/LICENSE`.
- Pełny podział i zastrzeżenia: [LICENSE-DATA.md](LICENSE-DATA.md).
