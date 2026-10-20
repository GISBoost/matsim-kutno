# FACT_CHECK — weryfikacja twierdzeń z raportów AI

Weryfikacja: 2026-10-16. Źródła pierwotne + pliki pobrane lokalnie (manifest na dole).
Statusy: **POTW** potwierdzone · **CZĘŚĆ** częściowo · **NIEPOTW** brak dowodów · **SPRZECZNE** sprzeczne z dowodami · **TEST** wymaga testu lokalnego.

Skróty źródeł twierdzeń: **G** = `raport google.txt` / `prompt_google.txt`, **A** = `AUDYT_PROMPTU_KUTNO_MATSIM.md`, **S** = `matsim_lodz_kutno_podsumowanie.md` (Grok), **Ł** = `archiwum/lowicz_2026-07/*`, **R** = `docs/research/MATSim_Lodz_research_v2.md`.

## Środowisko i MATSim

| # | Twierdzenie | Źr. | Status | Dowód |
|---|---|---|---|---|
| 1 | MATSim 2024–2026 wymaga Java 21 | G | **SPRZECZNE** | `maven.compiler.release` w pom.xml matsim-libs: 2024.0 → 17, 2025.0 → 21, **2026.0 → 25**. Najnowszy release: 2026.0 (2026-04-10). |
| 2 | Potrzebny zainstalowany Maven | G, Ł | **SPRZECZNE** | `matsim-example-project` ma `mvnw`/`mvnw.cmd` (Maven Wrapper). Maven nie jest zainstalowany lokalnie, a wrapper go nie wymaga. |
| 3 | Lokalnie: Java | — | **POTW** | Temurin OpenJDK 25.0.1 (`C:\Program Files\java25`), `JAVA_HOME` nieustawione. |
| 4 | Sprzęt: 32 GB RAM, RTX 4070 | R | **CZĘŚĆ** | RTX 4070 12 GB tak, ale **RAM = 16 GB**; CPU Ryzen 5 5600X, 6C/12T. Wolne miejsce: C: 48 GB, D: 114 GB. |
| 5 | `SupersonicOsmNetworkReader` w `contribs/osm` | G | **POTW** | Plik istnieje w tagu 2026.0 (`contribs/osm/.../networkReader/`). Stary `core.utils.io.OsmNetworkReader` też nadal istnieje. |
| 6 | Lokalny Python z geostackiem | — | **CZĘŚĆ** | Py 3.11: pandas, geopandas, shapely, pyproj, networkx; **brak** openpyxl, osmium. Dostępny `uv` (na razie użyty z `--with openpyxl`, bez instalacji globalnej). |

## GUS / TERYT

| # | Twierdzenie | Źr. | Status | Dowód |
|---|---|---|---|---|
| 7 | TERC gm. miejskiej Kutno = `1002011`, gm. wiejskiej = `1002062` | G | **POTW** | Oba kody występują w XLSX GUS (tabela ludności i macierz przepływów). |
| 8 | Kutno ma ~43 tys. mieszkańców (NSP 2021) | G | **CZĘŚĆ** | Dokładnie **42 255** (M 19 686, K 22 569). „~45 tys.” z S jest zawyżone. |
| 9 | Tabela ludności daje rejony i obwody | S, A | **POTW** | Kutno: **41 rejonów, 232 obwody**; obie sumy = 42 255; zero wartości ukrytych/nienumerycznych. |
| 10 | Kolumny: płeć, ekonomiczne i 10-letnie grupy wieku | A | **POTW** | Ogółem, M, K, przedprodukcyjny, produkcyjny (razem/mobilny/niemobilny), poprodukcyjny, 0-9 … 80+. **Brak statusu zatrudnienia i brak krzyżowania płeć × wiek.** |
| 11 | Udział pracujących 60–70% / 0,65 | S, G | **NIEPOTW** | Wartość założona bez źródła. Tablice „Ludność na rynku pracy NSP 2021” (XLSX) schodzą najniżej do **województwa × miasto/wieś × wiek × płeć**, nie do gmin. Łódzkie: pracujący / ludność w wieku produkcyjnym = 1 031 493 / 1 395 218 = **73,9%** (wskaźnik 78,4% liczony bez osób o nieustalonym statusie); w wieku poprodukcyjnym 12,0%. Dane NSP o pracujących na poziomie gminy w BDL: **NIEPOTW** (do sprawdzenia). |
| 12 | Tablice XLSX nie mają geometrii, a geometrii BREC trzeba szukać w OSM | G | **SPRZECZNE** (druga część) | XLSX faktycznie nie ma geometrii, ale **geometria BREC 2021 jest otwarta**: ATOM `geo.stat.gov.pl/atom-web/atom/SU`. SHP EPSG:2180 (OBW 205 MB, REJ 124 MB, cała PL) lub GML EPSG:4258 per województwo (łódzkie 23 MB). |
| 13 | Geometria łączy się z tabelą po identyfikatorach | A | **CZĘŚĆ / TEST** | Rejony: ID 6-cyfrowe (np. 650901), **41/41 zgodne**. Obwody: ID 7-cyfrowe (rejon + nr), **233 w geometrii vs 232 w tabeli**. **Wyjaśnione w F3:** `obwod_id = rejon × 10 + nr`, 232/232; obwód 6509213 jest tylko w geometrii. |
| 14 | Macierz dojazdów jest międzygminna i „nieprzydatna” dla Kutna | S | **CZĘŚĆ / ISTOTNE** | Jest międzygminna (brak przepływów wewnątrz gminy, pomija przepływy < 3 os., dotyczy pracowników najemnych). Dla Kutna jest jednak kluczowa: **przyjeżdża 8 186, wyjeżdża 2 669** (134 / 83 relacje). Największe źródła: gm. wiejska Kutno 1 831, Krzyżanów 662, Strzelce 533. Kutno jest wyraźnym importerem pracy. |
| 15 | ~15 000 pracujących w Kutnie → `flowCapacityFactor = 0,02` dla 300 agentów | G | **NIEPOTW** | Liczba wymyślona. Współczynnik zależy od nieustalonej populacji bazowej. |
| 16 | Korekta tablicy gospodarstw z 9.12.2025 | A | **NIEPOTW** | Nie sprawdzano, bo tablice gospodarstw nie są potrzebne w MVP (tylko pracujący). |

## OSM, CRS, sieć

| # | Twierdzenie | Źr. | Status | Dowód |
|---|---|---|---|---|
| 17 | Kryterium Kutna w EPSG:2180: X ∈ [470k, 510k], Y ∈ [480k, 520k] | G | **SPRZECZNE** | Centrum Kutna (19,3633 E; 52,2307 N) → **E = 524 805, N = 485 023** (pyproj). Test X odrzuciłby całe miasto. |
| 18 | EPSG:2180 „x/y” są jednoznaczne | — | **TEST** | Wg EPSG oś 1 = **północ (x)**, oś 2 = wschód (y). MATSim/GeoTools zwykle pracuje w kolejności E,N. Trzeba sprawdzić w smoke teście, żeby nie zamienić osi. |
| 19 | Ekstrakt OSM łódzkie z Geofabrik | Ł | **POTW** | `lodzkie-latest.osm.pbf` = 132 MB, dane do 2026-10-15. |
| 20 | Bufor 2 km wystarczy dla DK92/A1 | G | **NIEPOTW / TEST** | Węzeł A1 leży ok. 6 km od centrum. Bufor wynika z decyzji o zakresie popytu. |

## GTFS (poza MVP — tylko kontrola)

| # | Twierdzenie | Źr. | Status | Dowód |
|---|---|---|---|---|
| 21 | Kutno ma aktywny GTFS na zbiorkom.live | S | **POTW** | HTTP 200, 160 558 B, ważny 2026-10-01 → 2026-12-31, 8 plików (z `shapes.txt`). Wydawca: **zbiorkom.live (agregator, nie MZK)**, licencja nieustalona. |
| 22 | ~13 linii | S | **CZĘŚĆ** | `routes.txt` = **12** linii. |
| 23 | Aktywny GTFS-RT | S | **CZĘŚĆ** | HTTP 200, ale `last-modified` = 2026-10-01, czyli feed RT nieaktualizowany od 15 dni. |

## Spójność materiałów (sprzeczności między raportami)

- **Łowicz (07.2026) vs Kutno (10.2026)**: dwa różne PRD. Łowicz zakłada gminę miejską + wiejską bez bufora, PopulationSim/IPF na BREC, pracę z REGON + distance decay, budynki BDOT10k, próbkę 1% i scoring z kelheim. Kutno zakłada samo miasto, pracę z POI OSM, bufor sieci i próbkę 300 agentów / 5–10%. Prompty Łowicza odwołują się do zasady projektu, którego nie ma w folderze.
- **Próbka**: 1% (Ł) vs 2% / 300 agentów (G) vs 5–10% (S).
- **Konwerter OSM**: „nie pisz własnego parsera” (Ł) vs dopuszczony własny skrypt Python (G).
- **Rozkłady czasu** N(7:15, 30 min), praca 8 h ± 20 min (G): podane bez żadnego źródła.

## Manifest pobranych plików (`data/raw/`, poza Git)

| Plik | URL | Pobrano (UTC) | Bajty | SHA-256 |
|---|---|---|---|---|
| `gus/ludnosc_rejony_obwody_nsp2021.xlsx` | stat.gov.pl/…/6536/12/1/1/ludnosc_w_rejonach_statystycznych_i_obwodach_spisowych_nsp_2021.xlsx (publ. 2024-03-04) | 2026-10-16T16:55Z | 27 012 607 | 72bcef42…c4ce8 |
| `gus/macierz_przeplywow_nsp2021.xlsx` | stat.gov.pl/…/6536/9/2/1/macierz_przeplywow_ludnosci_zwiazanych_z_zatrudnieniem.xlsx (publ. 2024-01-31) | 2026-10-16T16:55Z | 2 916 382 | 55b6c4ea…96983 |
| `brec/AreaStatisticalUnit_10_2021.zip` | geo.stat.gov.pl/atom-web/download/?fileId=4a9e5752…&name=AreaStatisticalUnit_10.zip | 2026-10-16 | 22 792 730 | 2a351d25…9cd28 |
| `gus/rynek_pracy_nsp2021_tablice.xlsx` | stat.gov.pl/…/6536/11/2/1/ludnosc_na_rynku_pracy_…_tablice_w_formacie_xlsx.xlsx | 2026-10-16 | — | 168f35d3…f083b |
| `gtfs/kutno.zip` | cdn.zbiorkom.live/gtfs/kutno.zip | 2026-10-16 | 160 558 | 3df08df9…524ac60 |

Pełne sumy SHA-256 są w historii sesji. Do przeniesienia do `data/manifest.csv` przy pierwszym skrypcie pobierającym.
