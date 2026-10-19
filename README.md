# MATSim Kutno: instrukcja modelu

Stan: 2026-10-18. Opis zakłada decyzje D1–D19 z `DECISIONS.md` i wyniki z `PROGRESS.md`.
Każde założenie jest oznaczone **ZAŁOŻENIE** albo ma źródło (plik, wiersz, URL w `data/manifest.csv` i `docs/ZRODLA.md`).
Brakujące elementy są w rozdziale 13 („Luki”), z przypisaniem do sesji, która je uzupełnia.

> **Ważne:** to model ruchu dojazdów do pracy autem w gminie Kutno, nie prognoza ruchu. Wyniki służą do sprawdzenia poprawności pipeline'u i sensowności geografii (D2). Porównania z pomiarami są na etapie kalibracji (G5, D19).

---

## 1. Cel, zakres i to, czego model nie robi

**Cel:** agentowa symulacja MATSim dla gminy miejskiej Kutno (TERC 1002011, 42 255 mieszkańców wg NSP 2021). Kutno jest poligonem metodologii, którą później przeniesiemy na Łódź (G7).

**Zakres MVP (D3, D6):**
- agent jedzie **samochodem** w łańcuchu `dom → praca → dom`;
- popyt obejmuje: mieszkańców Kutna pracujących w Kutnie (D17, rejestr), przyjeżdżających do pracy w Kutnie z macierzy GUS, a od D17 także **wyjeżdżających** z Kutna do pracy poza miastem;
- od D19 do popytu dodany jest współczynnik udziału auta i obecności w pracy (K1-1).

**Czego model NIE robi (świadomie, zakres zamrożony):**
- nie modeluje transportu publicznego, pieszych, rowerzystów (tryby: rozdział G4, nieaktywne);
- nie modeluje innych celów podróży (zakupy, szkoła, sprawy), ruchu dostawczego ani ciężarowego;
- nie modeluje sygnalizacji, skrzyżowań, pierwszeństwa ani zakazów skrętu (G1 odłożony przez użytkownika);
- nie ma wyboru trybu (mode choice) ani kalibracji scoringu;
- nie modeluje ruchu tranzytowego i tła (ruch z zewnątrz sieci) w działającym runie. Tło jest w planach G5 (rozdział 13).

---

## 2. Jak odtworzyć wyniki

Wszystkie kroki są w projekcie. Dane surowe (`data/raw/`) nie są w gicie, ale każdy plik ma URL i sumę SHA-256 w `data/manifest.csv`.

```bash
# 0. Python (uv, Py 3.12) i zależności
uv sync

# 1. Dane surowe: pobrać pliki z data/manifest.csv do data/raw/ (sprawdzić SHA-256)

# 2. Granice (EPSG:2180, osie E,N)
uv run python -W ignore pipeline/make_area.py

# 3. Budynki i landuse z OSM (ten sam PBF co sieć)
uv run python -W ignore pipeline/osm_features.py

# 4. Sieć MATSim: build uber-jara i konwersja OSM (Java 25, JAVA_HOME ustawiane w poleceniu)
cd matsim && mvnw.cmd -B package -DskipTests && cd ..
# konwerter (usage z Javadoc CreateKutnoNetwork; nie ma jeszcze skryptu w repo, patrz rozdział 13)
java -cp matsim/matsim-example-project-0.0.1-SNAPSHOT.jar org.matsim.kutno.CreateKutnoNetwork \
  data/raw/osm/lodzkie-261015.osm.pbf scenarios/kutno/area/network_area.wkt scenarios/kutno/area/towns.wkt \
  config/network.properties scenarios/kutno/network.xml.gz
uv run python -W ignore pipeline/validate_network.py

# 5. Popyt z GUS i rejestrów
uv run python -W ignore pipeline/demand.py

# 6. Plany (25%, seed z config/kutno.toml, z K1-1). Parametry można nadpisać: klucz=wartość
uv run python -W ignore pipeline/plans.py scenarios/kutno/plans_25pct_k1.xml.gz 0.25
# plany referencyjne bez K1-1 (wejście config_25pct.xml; sha256 1be78c27…027)
uv run python -W ignore pipeline/plans.py scenarios/kutno/plans_25pct_bez_k1.xml.gz 0.25 car_share=1.0 work_from_home=0.0
uv run python -W ignore pipeline/validate_plans.py scenarios/kutno/plans_25pct_bez_k1.xml.gz 0.25

# 7. Run MATSim (z katalogu projektu, nie z katalogu configu)
java -Xmx10g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run \
  --config scenarios/kutno/config_25pct.xml --output output/r3_25pct --iterations 100

# 8. Walidacja eventów i wyniki
uv run python pipeline/check_events.py output/r3_25pct/output_events.xml.zst --expect-car-legs 12604   # 12 604 = wyniki D18 (bez K1-1, patrz R-1)
uv run python pipeline/queues.py ...   # przepełnione linki (D18), argumenty: patrz nagłówek skryptu
```

**Test regresyjny** (po każdej zmianie w `matsim/`): `scenarios/smoke/config.xml` (10 agentów, sieć syntetyczna), potem `check_events.py --expect-car-legs 20`. Przed testem usuń stary output.

**Uwaga:** przed ponownym generowaniem planów przeczytaj rozdział 13, punkt R-1 (`car_share` w `config/kutno.toml`). Bez tego plany 25% nie będą zgodne z wynikami referencyjnymi.

---

## 3. Przepływ danych (pipeline)

```
GUS NSP 2021: ludność per obwód, macierz dojazdów, rynek pracy ─┐
GUS BREC 2021: granice rejonów i obwodów ──────────────────────┤
                                                                ├─► make_area.py ─► area/ (gmina, powiat, obszar sieci)
OSM Geofabrik lodzkie (PBF) ─► CreateKutnoNetwork (Java) ──────┴─► network.xml.gz (sieć car, EPSG:2180)
                              └─► osm_features.py ─────────────► osm/features.gpkg (budynki, landuse)
BDL P4507/P4508 (rejestr 2024) ┐
                               ├─► demand.py ─► workers_by_obwod, inbound_by_gmina, outbound_by_gmina
                                                                  │
GBR Gdańsk 2022 (profil godzin) ─┐                                 │
network + features + demand ─────┴─► plans.py ─► plans_*.xml.gz + _meta.csv + _strata.csv
                                                                  │
config_*.xml (MATSim 2026.0, seed, factors, QSim) ◄──────────────┘
        │
        ▼
MATSim run ─► output/ (events, linkstats, modestats) ─► check_events.py, queues.py, convergence.py, g5_baseline.py ─► reports/
```

**Podział odpowiedzialności (CLAUDE.md):** Python liczy dane i plany, Java konwertuje sieć i uruchamia symulację. Każdy plik powstaje w jednym miejscu.

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
| **GBR Gdańsk 2022, Raport 3a, Rys. 46** (`gbr/GBR2022_raport3a.pdf`) | Godzinowy rozkład wyjazdów „dom–praca” (`config/departure_home_work_gbr2022.csv`) | Godziny wyjazdu (D14) | Metropolia Gdańsk, nie Kutno. Dane odczytane z wykresu wektorowego PDF. |
| **GDDKiA GPR 2025** (`g5/gpr2025/`) | Średni dobowy ruch na 19 odcinkach w sieci (A1, DK, DW), SDRR/SDRDR, udział lekkich i ciężkich | Walidacja (G5), cel kalibracji | Jedna wartość na cały odcinek, bez godzin. Brak ulic miejskich poza DK. |
| **GDDKiA SCPR 2025, stacja 14005 Lisica** (`g5/scpr2025/st_14005.pdf`) | Krzywe godzinowe dnia roboczego (zdigitalizowane) | Profil godzinowy ruchu tła (K3-2) | Stacja 13 km od Kutna, na DK60. Digitalizacja z wykresu. |
| **GUS Mobilność 2024** (`gus_transport/mobilnosc_*`) | Praca z domu łódzkie 7,3%, udział samochodu w podróżach wszystkich celów 60,1% | Obecność w pracy (K1-1) | Dla wszystkich celów, nie dla dojazdów do pracy. Tylko województwo. |
| **Bochnia 2016, Radom 2022** (`g4/`) | Udział auta w dojazdach dom–praca: 61–67% | Udział auta (K1-1) | Inne miasta, wartości z wykresów. |
| **BDOT10k powiat 1002, 2025-12-09** (`g3/bdot10k/1002_GPKG.zip`) | Budynki mieszkalne z liczbą kondygnacji (99,9% wypełnione) | **Nie używane w modelu** (rekomendacja G3, decyzja otwarta) | 39% geometrii z ortofotomapy. |
| **GUS statystyczne punkty adresowe, NSP** (`g2/adr_kutno_2026_0.csv`) | 4 807 punktów adresowych budynków mieszkalnych w Kutnie | Tylko kontrola (G2, G3) | Nic o podmiotach i pracy. |
| **GUS macierz dostępności** (`gus_transport/macierz_dostepnosci_20210331.xlsx`) | Czas przejazdu autem między gminami | Kontrola czasów (G5), próg D16 w minutach (nieużyte) | Model drogowy GUS, bez kongestii. |
| **GTFS zbiorkom.live Kutno, GTFS kolej (Kuranowski)** | Rozkłady autobusów i kolei | Poza MVP (G4) | Brak licencji w feedzie zbiorkom.live. Feed kolei ważny 30 dni. |
| **Literatura VSP i MATSim MUM 2026** (`g5/lit/`, `mum2026/`) | Konfiguracje referencyjne (matsim-berlin v6.3, matsim-kelheim v3.1), praktyka kalibracji | Uzasadnienie `stuckTime` (D18) i dynamiki `queue` | Inne skale. Nie są kopiowane wprost. |

**Co nie jest źródłem prawdy:** `archiwum/` (raporty innych modeli AI z błędami, wypisanymi w `FACT_CHECK.md`). Nie kopiujemy z nich liczb.

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

**Wynik sieci (F2):** 4 453 węzły, 10 296 linków, 4 426 km. Największa silnie spójna składowa obejmuje **100%** węzłów. 90/90 par tras testowych jest osiągalnych. Żaden link nie ma capacity, freespeed, length ani lanes ≤ 0.

### 5.3 Prędkości (D13)

Domyślne prędkości Supersonic (wartości VSP dla miast niemieckich) dawały **15 km/h** na ok. 3 000 km dróg lokalnych, głównie wiejskich. Dlatego prędkości są ustawiane jawnie w `config/network.properties`, w kolejności:

1. tag OSM `maxspeed` (także `PL:urban`, `PL:rural` itd.) przeliczony na km/h;
2. brak tagu → limit ustawowy wg typu drogi (Prawo o ruchu drogowym, art. 20): miasto 50, poza miastem 90, residential 50, living_street 20, motorway 140, trunk 100 (**ZAŁOŻENIE**: trunk 100, bo w PL to zwykle GP lub droga ekspresowa);
3. **freespeed = prędkość dozwolona × 0,8** (**ZAŁOŻENIE**: 0,8 to wartość praktyki VSP, nie wyliczona dla Kutna).

„Miasto” = gmina miejska i miasta w gminach miejsko-wiejskich z BREC (`towns.wkt`). **ZAŁOŻENIE:** wsie z zabudową traktujemy jak drogi zamiejskie (OSM nie ma granic obszaru zabudowanego).

**Kontrola:** czas swobodny w sieci to mediana **0,76 × czas GUS** (29 gmin, `scenarios/kutno/validation/gus_vs_siec.csv`). Sieć jest szybsza niż ORS/GUS, więc nie ma sygnału, że prędkości są zaniżone. Sam ORS to też model.

### 5.4 Przepustowość i dynamika (nie skalibrowane)

- **Capacity** i liczba pasów: domyślne wartości Supersonic (np. tertiary 600 poj./h/pas, primary 1 500 poj./h/pas). **Nie są skalibrowane** i nie mają lokalnego źródła. Połowa opóźnień siedzi na ulicach tertiary (`reports/etap2/g6_kolejki/g6_kolejki.md`).
- **Skrzyżowania:** brak sygnalizacji i pierwszeństwa. Przepustowość to tylko właściwość linku (G1, odłożony).
- **Dynamika kolejek:** `trafficDynamics = queue`. kinematicWaves (jak Berlin, Kelheim) dał +56% opóźnień, a przy 300 s stuck time gridlock (D18, G5 K5).
- **`qsim.stuckTime = 30 s`** (D18). Przy 10 s i `removeStuckVehicles=false` QSim wpychał pojazdy na pełne krótkie linki (82 pojazdy na linku o pojemności 1,2). Po zmianie: przepełnione linki 13 → 4–7.

### 5.5 Przypięcie aktywności do sieci

- Aktywności są przypinane do **najbliższego linku** wg odległości do jego odcinka. Pomijane są typy: `motorway`, `motorway_link`, `trunk`, `trunk_link`, `boundary_turnaround` (`snap_exclude_types`). Bez tego MATSim przypinałby dom do jezdni A1 (R3/E5).
- Wyjątek: wjazdy i wyjazdy na granicy zachowują swój link.

---

## 6. Popyt: kto jedzie do pracy i skąd

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
- **Gminy w powiecie kutnowskim (D9):** dom to losowy budynek mieszkalny OSM w gminie źródłowej (ważony powierzchnią obrysu). Start na wjeździe do Kutna o godzinie z profilu (rozdział 9).
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
- **Status:** to zmiana zakresu MVP („wszyscy jadą autem”, D6) i wymaga potwierdzenia decyzji. Wartości pochodzą z innych miast (**ZAŁOŻENIE**).

### 6.6 Próbka i skala

- **Skala:** 10%, 25%, 100%. Wyniki raportujemy z **25%, 3 seedy** (D15, decyzja użytkownika). 100% tylko na wyraźną prośbę.
- **Seedy:** 4711 (domyślny w configu), 1, 2.
- **Przepustowość skalowana do próbki:** `flowCapacityFactor = storageCapacityFactor = sampleSize` (MATSim 2026 wymaga ich równości, D8, D15/5).
- Wyniki w skali 100% odtwarzamy przez `× 1/sampleSize` (dotyczy natężeń i GEH; `convergence.py` robi to sam).

---

## 7. Lokalizacje: skąd są domy i miejsca pracy

Wszystkie lokalizacje są **budynkami z OSM** (ten sam PBF co sieć), wybieranymi losowo z wagą **powierzchni obrysu budynku** (D7, D11). Losowanie jest z powtórzeniami, a seed jest w configu (`seed = 4711`).

### 7.1 Filtry budynków

**Mieszkalne** (`residential_buildings`, ZAŁOŻENIE D11): `house`, `detached`, `apartments`, `residential`, `semidetached_house`, `terrace`, `bungalow`, `farm`, `dormitory`, a także `building=yes` wewnątrz landuse `residential`, bez tagów `amenity`/`shop`/`office`.

**Pracy** (`work_buildings`, ZAŁOŻENIE D7): `retail`, `industrial`, `warehouse`, `office`, `commercial`, `school`, `hospital`, `public`, `civic`, `government`, `kindergarten`, `university`, `college`, `supermarket`, `service`, `fire_station`, `train_station`, `transportation`, `manufacture`, `factory`, `hotel`, a także każdy budynek z tagiem `amenity`/`shop`/`office` i `building=yes` w landuse `industrial`, `commercial`, `retail`. Tylko w granicach gminy Kutno (dla agentów z Kutna).

**Wykluczenia z danych OSM:**
- `building=no` traktujemy jak brak budynku (plac komisu z `shop=car`, 3,6 ha, był największym „miejscem pracy”, R3/błąd 1).
- Budynek mieszkalny nie może być budynkiem pracy (`loc[work, residential] = False`).

### 7.2 Domy

- **Mieszkańcy:** budynek mieszkalny w obwodzie spisowym, losowany wagą powierzchni. Obwód bez budynku mieszkalnego → **losowy punkt** w obwodzie (D11). W 100% jest jeden taki obwód, `6509902`, z 6 osobami (w 10%). Nie wiemy, czy to brak zabudowy, czy brak danych w OSM (do sprawdzenia w QGIS).
- **Przyjeżdżający z powiatu:** losowy budynek mieszkalny w gminie źródłowej (geometria z rejonów BREC).
- **Przyjeżdżający spoza powiatu i wyjeżdżający spoza powiatu:** nie mają domu w Kutnie. Start/koniec na linku granicznym.
- Tylko 26 611 budynków mieszkalnych w obszarze sieci.

**Alternatywa (nieprzyjęta):** budynki z BDOT10k z liczbą kondygnacji (wagi „obrys × kondygnacje”). Analiza G3 pokazała lepsze dopasowanie do siatki GUS 250 m (błąd 8,5 pp wobec 9,4–10,3 pp obecnie, zależnie od wariantu porównania; `docs/research/G3_domy.md`). Decyzja jest otwarta (rozdział 13).

### 7.3 Miejsca pracy

- Losowanie z **wagą powierzchni obrysu** z listy budynków pracy w gminie Kutno. Kandydatów: 1 103, wylosowano 473 budynki w 10% (F4).
- Top 5 budynków dostaje 13% agentów (duże hale w strefie wschodniej). Są to realne obiekty (`industrial` i `warehouse`, 1,6–3,1 ha), sprawdzone w kontroli przed runem (D16).
- **ZAŁOŻENIE:** rozkład zatrudnienia wewnątrz gminy odwzorowany przez powierzchnię budynków. Nie ma REGON ani adresów zakładów w modelu (D7, G2 otwarte).

### 7.4 Przypisanie linku sieci

Każdy dom i miejsce pracy dostaje **najbliższy link** sieci (z pominięciem typów z `snap_exclude_types`, rozdział 5.5). Przyjeżdżający i wyjeżdżający spoza powiatu mają link graniczny od razu.

---

## 8. Cechy agentów: co wiemy o osobie

Agenty tworzy się z **agregatów**, nie z mikrodanych. Nie odtwarzamy gospodarstw ani osób (CLAUDE.md).

| Atrybut | Wartość | Skąd |
|---|---|---|
| `subpopulation` | `person` (wymagane przez SimWrapper, CLAUDE.md) | stała |
| `kind` | `resident` / `commuter` / `outbound` | rodzaj popytu (6.2–6.4) |
| `id` | `r<obwód>_<n>`, `c<gmina>_<n>`, `o<gmina>_<n>` | unikalne (test w `plans.py`) |
| dom | budynek OSM i link | rozdział 7.2 |
| praca | budynek OSM i link | rozdział 7.3 |
| godzina wyjazdu | z profilu GBR (rozdział 9) | losowana z przedziału |

**Czego agenci NIE mają:** wieku, płci, wykształcenia, zawodu, dochodu, posiadania samochodu, liczby osób w gospodarstwie. Wskaźniki zatrudnienia wg wieku wpływają tylko na **rozkład po obwodach** (waga obwodu), a nie na atrybuty osób. Nie ma też kontroli spójności (np. osoba ze wskaźnikiem niskim zatrudnieniem w obwodzie pracuje tak samo jak inna).

---

## 9. Plany dnia: łańcuch i godziny

**Łańcuch (każda osoba):** `home (end_time = wyjazd) → car → work (max_dur = 8:00:00) → car → home`. Test: trzy aktywności i dwie nogi car, `end_time` XOR `max_dur` (CLAUDE.md, gotchas).

**Godzina wyjazdu (D14):**
1. Losowanie przedziału godzinowego z rozkładu „dom–praca” GBR Gdańsk 2022, Rys. 46 (`config/departure_home_work_gbr2022.csv`, 18 przedziałów, po normalizacji do 100%). Przedział 20–24 h jest jednym przedziałem 4-godzinnym.
2. Godzina jednostajnie losowana w przedziale (**ZAŁOŻENIE**).
3. Wyjazd z domu = ta godzina. Przyjeżdżający z granicy: godzina wejścia na granicę.

**Ograniczenia godzin:**
- Rozkład jest z metropolii Gdańsk (**ZAŁOŻENIE**, że pasuje do Kutna).
- Brak godzinowego rozkładu lokalnego (decyzja D10 otwarta, R1 w sesji `r1-r-d-o-rozk-adu-godzin`).
- Start najpóźniej o 23:52.

**Czas pracy 8 h** (`work_max_dur`): **ZAŁOŻENIE** zaokrąglone z GUS BCL 2013 (8 h 11 min średnio dla najemnych). Nie jest to rozkład per agent. `TimeAllocationMutator` **wyłączony** (godziny z danych nie mają dryfować).

**Koniec symulacji:** `qsim.endTime = 48:00:00` (zapas; 36:00 przerywało agenta z Krakowa, `stuckAndAbort`, R3).

---

## 10. Symulacja MATSim (konfiguracja)

Pliki: `scenarios/kutno/config_{10,25,100}pct.xml`. Ścieżki są względne do configu. `controller.outputDirectory` jest względny do katalogu roboczego, więc uruchamiaj z katalogu projektu.

| Parametr | Wartość | Uzasadnienie |
|---|---|---|
| MATSim | 2026.0, Java 25 | `matsim/` (matsim-example-project @ 74d23af) |
| `lastIteration` | 100 | D15/3 (maks. 100 iteracji) |
| `flowCapacityFactor` = `storageCapacityFactor` | = sampleSize (0,25 dla 25%) | D8, MATSim 2026 wymaga równości |
| `stuckTime` | 30 s | D18 |
| `trafficDynamics` | `queue` | D18, G5 K5 |
| `endTime` | 48:00:00 | rozdział 9 |
| `randomSeed` | 4711 (1, 2 dla wariancji) | config |
| `coordinateSystem` | EPSG:2180 | CLAUDE.md |
| `numberOfThreads` | 8 w configu; runy 4 lub 2 wątki | liczba wątków nie skraca runu, 4 i 8 dają identyczne wyniki |
| Strategie | `ChangeExpBeta` 0,8, `ReRoute` 0,2 | `subpopulation = person` |
| `fractionOfIterationsToDisableInnovation` | 0,8 | po 80 iteracjach tylko wybór planu (score spłaszcza się z definicji) |
| Scoring | domyślny MATSim; `home` typical 16 h, `work` typical 8 h | **ZAŁOŻENIE**, score tylko diagnostyczny, kalibracja poza MVP |
| SimWrapper, linkStats | włączone; linkStats co 10 it. (średnia z 5) | R3/E2, diagnostyka zbieżności |

**Co jest w wyjściu:** `output_events.xml.zst` (eventy, format `.zst`, CLAUDE.md), `output_links.csv.zst`, `modestats`, `scorestats`, `traveldistancestats` (MATSim). Wykresy: `pipeline/plot_run.py`.

**Co MATSim robi z nogami:** przy trybie `car` MATSim sam dokleja teleportowane nogi `walk` (dojście i odejście). Nie są częścią modelu ruchu (CLAUDE.md, gotchas), tylko trzeba je odfiltrować przy liczeniu nóg.

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

**Zasada z CLAUDE.md:** run bez błędu nie jest dowodem. Fazę zalicza test semantyczny.

### 11.2 Wyniki referencyjne (D18, 25%, 3 seedy)

Źródło: `reports/etap2/g6_kolejki/d18_25pct/`, `reports/etap2/g6_kolejki/g6_kolejki.md`.

| Wskaźnik | Wartość |
|---|---|
| nogi car | 12 604 (zgodne z planami), 0 stuck |
| opóźnienie łącznie, 3 seedy [poj.-h próbki] | 735–854 |
| przepełnione linki 06–09 | 4–7 |
| GEH < 5 w szczycie 7–8 (między seedami) | 98,8–100% |
| mediana czasu podróży s4711: mieszkańcy / przyjeżdżający / wyjeżdżający | 15,0 / 23,5 / 24,1 min |
| największe wąskie gardło | DK92 Sklęczkowska (zwężenie 2 → 1 pas). W diagnozie wariantu B (ten sam popyt) 44% opóźnień to kolejka spod tego zwężenia, a 51% to ulice tertiary z capacity 600 poj./h/pas |

**To jest punkt startowy do kalibracji, nie wynik kalibrowany.** Dla odniesienia: R1 (z K1-1, 25%, 3 seedy) daje 7 478 nóg car i opóźnienia 106–113 poj.-h. Oznacza to silną nieliniowość kongestii względem popytu.

### 11.3 Walidacja względem GPR 2025 (G5, R1)

| Grupa odcinków | Model (D18) / GPR | Model (R1, K1-1) / GPR |
|---|---|---|
| A1 (3 odcinki) | 7% | 3% |
| DK w Kutnie (Objazdowa, Bitwy pod Kutnem, Sklęczkowska) | 56% | 30% |
| pozostałe DK | 16% | 8% |
| DW | 7% | 4% |

**Luka jest oczekiwana:** model nie ma tranzytu, ruchu lokalnego innego niż dojazdy, ruchu dostawczego i ciężarowego. Dlatego po K1-1 natężenie w mieście spada, a nie rośnie. Tło (rozdział 13, G5) ma wypełnić tę lukę.

---

## 12. Założenia (zbiorcza tabela)

Każde ZAŁOŻENIE ma wartość, miejsce w kodzie lub configu, uzasadnienie i status.

| ID | Założenie | Wartość | Gdzie | Uzasadnienie / status |
|---|---|---|---|---|
| A-1 | Zasięg sieci = powiat + bufor | 3 000 m | `config/kutno.toml` `network_buffer_m` | D9, do weryfikacji w F2 (otwarte: szerokość poza powiatem) |
| A-2 | Zawrotki na granicy | 300 m, 30 km/h, cap 5 000, strefa 1 km | `config/network.properties` | F2 (A1), D9 |
| A-3 | Prędkość = limit × 0,8 | factor 0,8 | `config/network.properties` | praktyka VSP, nie wyliczone dla Kutna |
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
| A-16 | Budynki mieszkalne i pracy (listy typów) | rozdział 7.1 | `config/kutno.toml` | D7, D11 |
| A-17 | Wagi budynków = powierzchnia obrysu | m² | `plans.py` | D7, D11; alternatywa BDOT × kondygnacje nieprzyjęta (G3) |
| A-18 | Obwód bez budynków → losowy punkt | — | `plans.py` | D11, dotyczy obwodu 6509902 |
| A-19 | Udział auta dom–praca | 0,64 (61–67%) | `config/kutno.toml` `car_share` | D19/K1-1, Bochnia 2016, Radom 2022 |
| A-20 | Praca z domu | 7,3% | `config/kutno.toml` `work_from_home` | GUS Mobilność 2024, tabl. 1 |
| A-21 | Profil godzin wyjazdu | GBR Gdańsk 2022 | `config/departure_home_work_gbr2022.csv` | D14, metropolia, nie Kutno |
| A-22 | Godzina jednostajnie w przedziale | — | `plans.py` | ZAŁOŻENIE D14 |
| A-23 | Czas pracy 8 h | 08:00:00 | `config/kutno.toml` `work_max_dur` | GUS BCL 2013, zaokrąglone |
| A-24 | Brak TimeAllocationMutator | — | config | godziny z danych |
| A-25 | Scoring: typical duration home 16 h, work 8 h | — | `config_*.xml` | domyślne MATSim, score diagnostyczny |
| A-26 | Próbka i zaokrąglanie | 25% (wyniki), metoda największych reszt | `plans.py` | D15/3, D8 |
| A-27 | Seedy | 4711, 1, 2 | config, `output/r3_runs.sh` | D15 |
| A-28 | `stuckTime` | 30 s | config | D18, Berlin/Kelheim |
| A-29 | Dynamika `queue` | — | config | D18, G5 K5 |
| A-30 | Brak ruchu tła w runach | — | — | **otwarte**: G5 K2-2, plany z tłem jeszcze nie są wygenerowane |
| A-31 | Brak pieszych, rowerzystów, PT i ciężarowych | — | — | D6 (wszyscy car), G4 |
| A-32 | Opóźnienia na linku, nie na skrzyżowaniu | — | — | G1 odłożony |
| A-33 | Dzień roboczy | — | — | typowy dzień roboczy (GUS, GBR) |

---

## 13. Ograniczenia, znane problemy i luki

### 13.1 Zgodność konfiguracji (wymaga decyzji lub poprawki przed następnym runem)

- **R-1: `car_share` i `work_from_home` są domyślnie włączone** w `config/kutno.toml` (D19/K1-1, decyzja: zostaje). Wyniki referencyjne D16, D17/B i D18 (`reports/etap2/g6_kolejki/d18_25pct/`) używają planów **bez K1-1**: `scenarios/kutno/plans_25pct.xml.gz` (6 302 osoby), który `config_25pct.xml` czyta jako wejście. Domyślne `plans.py ... 0.25` daje dziś 3 739 osób (K1-1), więc bez parametrów nie odtworzy referencji. Plany bez K1-1 mają osobną nazwę `scenarios/kutno/plans_25pct_bez_k1.xml.gz`. Wygenerowano je poleceniem z parametrami poniżej, sha256 identyczny z `plans_25pct.xml.gz` (`1be78c27…027`), 6 302 osoby (3 647 / 2 041 / 614). Plany K1-1 dla R1 są w `plans_g5r1_25pct.xml.gz`.
- **R-2: domyślne pliki `scenarios/kutno/plans.xml.gz`, `config_10pct.xml` i `config_100pct.xml`** pochodzą z etapu F5/F6 (`inputPlansFile = plans.xml.gz`). Nie wiadomo z pewnością, z jakiego stanu `kutno.toml` powstały. Nie są opisane w `PROGRESS.md`. **Propozycja:** usunąć z konfiguracji wzorcowej albo opisać w `reports/README.md`.
- **R-3: `output/r3_runs.sh`** (skrypt uruchamiający seedy równolegle) jest w `output/`, czyli w `.gitignore`. Nie jest wersjonowany. Build `CreateKutnoNetwork` także nie ma skryptu w repo (rozdział 2 podaje polecenie z Javadoc).
- **R-4:** komentarz w `config_25pct.xml` mówi o 8 wątkach, a runy referencyjne używały 4 (bez wpływu na wyniki, ale do poprawy).

### 13.2 Ograniczenia danych i metody

- Macierz NSP: tylko pracownicy najemni, bez przepływów < 3 osób i bez ruchu wewnątrz gminy. Dolna granica odpływu i napływu (zaniża ruch).
- Miejsce pracy w macierzy = adres pracodawcy (siedziba). Dalekie relacje (Warszawa 457) mogą być efektem siedziby firmy, nie realnego dojazdu.
- Wskaźniki zatrudnienia tylko na poziomie województwa. Estymacja D5 jest o 17% wyższa od rejestru.
- Pracujący per obwód (232) to estymacja, nie obserwacja (D5, CLAUDE.md).
- Dane OSM: 72% budynków gminy ma `building=yes` bez typu, a `building:levels` jest w nich tylko w 2%. Wagi (powierzchnia obrysu) są więc przybliżone.
- 1 450 budynków OSM w Kutnie nie ma odpowiednika w BDOT10k (G3).
- Liczba mieszkańców pracujących jest nieprzyporządkowana do wieku ani płci.

### 13.3 Ograniczenia modelu

- Brak sygnalizacji, skrzyżowań, zakazów skrętu. Kolejki są wynikiem capacity linku i `stuckTime`, nie konfliktów na skrzyżowaniu.
- Brak czasu w czasie dojazdu poza siecią: przyjeżdżający i wyjeżdżający „teleportują się” na granicę (ZAŁOŻENIE, D16/A).
- Jeden typowy dzień roboczy, bez weekendu i świąt.
- Brak losowej zmienności czasu pracy per agent (stałe 8 h).
- Scoring domyślny: wybór trasy jest prawdziwy, ale score nie jest kalibrowany i nie służy do wniosków.
- Wyniki wrażliwe nieliniowo na popyt (C vs B: opóźnienia −71% przy −22% popytu). Liczba miejsc pracy jest najczulszym parametrem.

---

## 14. Luki: czego jeszcze nie ma

Każda luka ma przypisaną sesję, która ją uzupełnia. Sesje wysłały komunikaty z prośbą o wpis w swoim dokumencie (rozdział 15).

| # | Luka | Stan | Kto uzupełnia |
|---|---|---|---|
| L-1 | **Ruch tła i tranzyt** (K2-2): 59 879 podróży/dobę w 100%, estymacja O-D z GPR. Brak w planach. Plan kroków 1–5 w `G5_plan_kalibracji.md` §5. | czeka na wdrożenie | sesja `g5-walidacja` |
| L-2 | **Decyzja K1-1** (zawężenie MVP „wszyscy car”) i źródło udziału auta dla Kutna. Przedział z innych miast, brak danych lokalnych. | decyzja użytkownika | sesja `g4-tryby` |
| L-3 | **Podział modalny** (G4): PT, pieszo, rower nieobecne. Brak źródła dla dojazdów do pracy w Kutnie. | otwarte | sesja `g4-tryby` |
| L-4 | **Rozkład wewnątrz gminy miejsc pracy**: wagi według powierzchni budynków. REGON, PKD i adresy zakładów nieużyte (G2). | otwarte | sesja `g2-praca` |
| L-5 | **Wagi domów** (BDOT × kondygnacje vs obrys): rekomendacja G3 bez decyzji. | decyzja użytkownika | sesja `g3-domy` |
| L-6 | **Godziny wyjazdu z lokalnego źródła** (D10): dziś GBR Gdańsk. Brak lokalnego rozkładu. | research | sesja `r1-r-d-o-rozk-adu-godzin` |
| L-7 | **Czas pracy 8 h**: stałe ZAŁOŻENIE, bez rozkładu per agent. | research | sesja `r1-r-d-o-rozk-adu-godzin` (ten sam temat) |
| L-8 | **Capacity ulic miejskich i skrzyżowań** (A-6, G1): brak danych. Pomiary miejskie (UM, ZDP, GDDKiA Rejon Kutno) do wysłania przez użytkownika. | czeka na dane | użytkownik (wnioski) |
| L-9 | **Ciężarowe i PCE**: 24–37% ciężkich na DK w GPR, brak źródła PCE. | otwarte | sesja `g5-walidacja` |
| L-10 | **Rekonstrukcja konfiguracji** (R-1, R-2, R-3): jeden skrypt odtwarzający wszystkie runy i pliki. | do zrobienia | ta sesja (po zgodzie) |
| L-11 | **Wizualizacja Blender** (G6): opis, co pokazuje i co nie. Nie wpływa na model. | opis w `docs/research/G6_blender.md` | sesja `g6-blender` |

Pytania otwarte z `DECISIONS.md`, bez decyzji: szerokość bufora poza powiatem, parametry scoringu, car share (D6), REGON (D7).

---

## 15. Struktura projektu

| Ścieżka | Zawartość | W gicie |
|---|---|---|
| `CLAUDE.md` | zasady pracy agenta | tak |
| `DECISIONS.md` | decyzje D1–D19 (zmiana = nowy wpis) | tak |
| `FACT_CHECK.md` | zweryfikowane fakty z raportów AI | tak |
| `TASKS.md` | fazy F0–F6 i etap 2 (G1–G7) | tak |
| `PROGRESS.md` | co zaliczono, z dowodem | tak |
| `ERRORS.md` | błędy i reguły | tak |
| `config/` | `kutno.toml`, `network.properties`, profile godzin | tak |
| `data/manifest.csv` | URL, data, bajty i SHA-256 każdego pobrania | tak |
| `data/raw/` | pobrane źródła (tylko do odczytu) | nie |
| `pipeline/` | skrypty Python (dane, plany, analiza, walidacja) | tak |
| `matsim/` | projekt Java (`CreateKutnoNetwork`, `mvnw`) | tak |
| `scenarios/smoke/` | test regresyjny, 10 agentów | tak |
| `scenarios/kutno/` | sieć, plany, configi, popyt CSV (`plans_*.xml.gz` wyłączone z gita) | częściowo |
| `reports/` | raporty i dowody per faza (`reports/README.md`) | tak |
| `docs/research/` | analizy G2–G6 i tło metodyczne | tak |
| `docs/ZRODLA.md` | katalog źródeł | tak |
| `output/` | runy MATSim | nie |
| `blender/` | wizualizacja G6 | tak |
| `archiwum/` | materiały innych AI (nie jest źródłem prawdy) | tak |

**Wyniki referencyjne (aktualne):** `reports/etap2/g6_kolejki/d18_25pct/` (25%, 3 seedy, D18).

---

## 16. Słownik

| Skrót | Znaczenie |
|---|---|
| BDL | Bank Danych Lokalnych GUS. P4507 = pracujący mieszkańcy, P4508 = pracujący wg siedziby płatnika |
| BDOT10k | Baza Danych Obiektów Topograficznych (budynki, kondygnacje) |
| BREC | Baza Rejestrów Ewidencyjnych Charakterystyk (rejony i obwody spisowe NSP 2021) |
| CRS EPSG:2180 | układ PUWG 1992, osie E, N |
| D1–D19 | decyzje projektowe (`DECISIONS.md`) |
| GEH | miara zgodności natężeń (< 5 = dobra zgodność) |
| GPR | Generalny Pomiar Ruchu GDDKiA (SDRR, SDRDR, SDRL) |
| GBR | Gdański Biuro Rozwoju, Raport 3a (badanie mobilności, profil godzin) |
| GTFS | rozkład jazdy transportu publicznego (format) |
| K1–K5, G1–G7 | kroki kalibracji (`G5_plan_kalibracji.md`) i etapy projektu (`TASKS.md`) |
| MVP | zakres: samochód, dom–praca–dom |
| NSP 2021 | Narodowy Spis Powszechny 2021 |
| O-D | macierz podróży (origin–destination) |
| PCE | współczynnik ekwiwalentu samochodu osobowego (ciężarówki) |
| QSim | silnik symulacji kolejkowej MATSim |
| SCPR | Stacje Ciągłych Pomiarów Ruchu (GDDKiA) |
| SDRDR | średni dobowy ruch w dni robocze (GPR) |
| TERC | identyfikator jednostki terytorialnej (1002011 = gm. miejska Kutno) |
| TABL. 5 | tablica GUS „Ludność na rynku pracy” (wskaźniki zatrudnienia) |

## 17. Licencja

- **Kod** (`pipeline/`, `matsim/src/`, `blender/`, skrypty w `reports/` i `docs/`): GPL-3.0-or-later, plik [LICENSE](LICENSE).
- **Dane i wyniki z GUS**: CC BY 4.0 (wymagane podanie źródła: Główny Urząd Statystyczny).
- **Dane z OpenStreetMap**: ODbL 1.0 (© OpenStreetMap contributors). Wyprowadzone bazy z danymi OSM publikujemy na ODbL.
- **Przykładowy projekt MATSim** w `matsim/`: GPL-2.0-or-later, plik `matsim/LICENSE`.
- Pełny podział i zastrzeżenia: [LICENSE-DATA.md](LICENSE-DATA.md).
