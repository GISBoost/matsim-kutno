# MATSim Kutno: model guide

**English** | [Polski](README.pl.md)

Status: 2026-11-03, baseline **R9.5** (D36). The description assumes decisions D1–D37 from `docs/projekt/DECISIONS.md` and results from `docs/projekt/PROGRESS.md`.
Each assumption is marked as **ASSUMPTION** or has a source (file, line, URL in `data/manifest.csv` and `docs/ZRODLA.md`).
Missing elements are in chapter 14 ("Gaps"), with a reference to the document that describes them. Project map (stages, status, plans): [docs/projekt/ROADMAP.md](docs/projekt/ROADMAP.md).

> **Important:** this is a car traffic model of the Kutno municipality, not a traffic forecast. On roads covered by GPR counts it is calibrated to measurements. On city streets outside GPR, volumes are underestimated by roughly half (D37), so results for those streets should not be read directly.

---

## 1. Purpose, scope and what the model does not do

**Purpose:** agent-based MATSim simulation of the urban municipality of Kutno (TERC 1002011, 42,255 inhabitants according to NSP 2021). Kutno is a testing ground for a methodology that we will later transfer to Łódź, but only after the work on Kutno itself is finished.

**What baseline R9.5 contains (all agents travel by car):**
- commuting `home → work → home`: residents working in Kutno, inbound and outbound commuters (D17), with car share and presence at work (K1-1, D19);
- separate resident trips `home → cel → home`: shopping and services (D32, D34), visits, leisure, health, escorting (D36);
- background traffic as the subpopulations `tlo` (light and delivery vehicles) and `ciezkie` (heavy), from O-D matrices estimated from GPR counts (D19–D21). This is an estimate calibrated to measurements, not an observation;
- a network with speeds per road group (D23) and OSM turn restrictions (D26), homes from BDOT10k (D28), activity link direction chosen by route (D29), person attributes (D30).

**What the model does NOT do:**
- it does not model public transport, pedestrians or cyclists. The GTFS timetable is imported only technically (`scenarios/kutno_pt/`), without PT agents;
- it has no mode choice and no ASC calibration (step 6 in ROADMAP). Scoring parameters are default and the score is diagnostic only;
- it does not model school as a trip purpose (step 4B, plan without implementation), daily chains (D35, variant `chains`, `off` by default), trips not based at home, non-work trips from outside the city or business traffic in the city;
- it does not model traffic signals or right of way. Turn restrictions work in the router, QSim does not enforce them;
- it does not group agents into households: a trip agent is a separate person, not linked to a worker (D32).

---

## 2. How to replay the results

Raw data (`data/raw/`) is not in git, but each file has a URL and SHA-256 in `data/manifest.csv`. Plans and the network in `scenarios/kutno/*.xml.gz` are also outside git, because they are built from this data. Rebuilding everything from scratch on a clean clone has not been verified yet (step 8 in ROADMAP).

**MATSim runs and O-D estimation run on GitHub Actions**, not locally (ERRORS 34). Run inputs are in git, in `scenarios/kutno_r91/` and `scenarios/kutno_od/`, so these steps do not need `data/raw/`.

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

The 25% plan has sha256 `f3ca89f…`, the same as `scenarios/kutno_r91/plans_r94e_p0.xml.gz` tested on GitHub Actions. It is worth checking, because the same config must produce the same file.

**Workflows** (all manual only, `workflow_dispatch`):

| Workflow | Purpose | Inputs |
|---|---|---|
| `matsim-od` | runs without background, O-D estimation (`background_od.py`), `od_warnings.py` check; the result is matrices in an artifact | `scenarios/kutno_od/` |
| `matsim-r93` | comparison of two plan variants, 5 runs each (3 MATSim seeds, 2 plan seeds), 25%, 50 iterations, analysis with city counts | `scenarios/kutno_r91/` |
| `matsim-r91`, `matsim-r92`, `matsim-attr`, `matsim-g1b` | tests of D29, D31, D30 and D27 (historical) | as above, `scenarios/kutno_g1b/` |
| `matsim-run`, `matsim-run-100pct` | runs of baseline R7b (historical) | `scenarios/kutno_r7b_*` |

Test of baseline R9.5 against R9.4:

```bash
gh workflow run matsim-r93.yml -f variant=r94e -f control=r93o
```

**A change in demand means a new background estimation**, in this order: plans without background into `scenarios/kutno_od/` (`plans.py … background_od= heavy_od=`), workflow `matsim-od` with a new tag, then `od_warnings.py` (in the workflow) and plans with the new matrices. The R9.5 recipe step by step: `reports/etap3/g_inne_cele/inne_cele.md`, section „Odtworzenie”. Matrices from GitHub Actions differ from local ones by point-sampling noise, totals up to 0.12% (`reports/etap3/krok0_od_gha/krok0.md`). Compare variant differences with the spread of plan seeds, not MATSim seeds.

**A local run** is for a technical test only (from the project directory, not the config directory; `output/` is relative to the working directory):

```bash
java -Xmx10g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run \
  --config scenarios/kutno/config_25pct.xml --output output/test_25pct --iterations 2
uv run python pipeline/check_events.py output/test_25pct/output_events.xml.zst --expect-car-legs 27233
```

27,233 car legs is the 25% plan of baseline R9.5: 2 × 3,739 workers, 2 × 1,477 resident trips and one leg for each of the 16,801 background agents.

**Regression test** (after every change in `matsim/`): `scenarios/smoke/config.xml` (10 agents, synthetic network), then `check_events.py --expect-car-legs 20`. Remove the old output before the test.

---

## 3. Data flow (pipeline)

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

**Division of responsibility:** Python computes data and plans, Java converts the network and runs the simulation. Each file is created in one place.

---

## 4. Data sources

Full list of limitations: `docs/ZRODLA.md`. Below is what influences the model.

| Source | What we get | Where in the model | limitations |
|---|---|---|---|
| **GUS NSP 2021, population in regions and statistical districts** (`gus/ludnosc_rejony_obwody_nsp2021.xlsx`) | 232 districts of Kutno: total population, age groups (pre/productive/post-productive). Total 42,255. | Distribution of employed persons on districts (D5, D17) | Lack of gender cross-section with age and lack of employment status. |
| **GUS NSP 2021, labor market, TABLE 5** (`gus/rynek_pracy_nsp2021_tablice.xlsx`) | Employment indicators for cities in the Łódź voivodeship: production 0.739 (low variant: employed person / total) or 0.784 (baseline: without undetermined status, GUS method); post-production approx. 0.12 | Employed person estimate per district (D5), "baseline" variant | Only the voivodeship, not the commune. Estimation, not observation. Values: `scenarios/kutno/validation/f3_demand.json`. |
| **GUS NSP 2021, employment flow matrix** (`gus/macierz_przeplywow_nsp2021.xlsx`) | Inbound commuter to Kutno: 8,186 persons in 134 municipalities. Outbound: 2,669 in 83 municipalities. | Inbound and outbound commuters (D3, D9, D17) | Employees only. Ignores flows < 3 people and traffic within the municipality. The workplace is the employer's address (e.g., company headquarters in Warsaw). |
| **BDL P4507 and P4508, 2024** (`g2/bdl_kutno.json`, BDL API) | P4507: employed residents of the municipality (17 255). P4508: workplaces by payer headquarters (17 486). | Anchor of the number of employed persons in Kutno (D17/B) and variant C | ZUS/KRUS registers, counted by payer's headquarters. There is a 30% gap between P4507 + NSP and P4508 that cannot be explained (G2). |
| **GUS BREC 2021, geometry** (`brec/AreaStatisticalUnit_10_2021.zip`, `brec/SU_BREC_2021_REJ.zip`) | Municipal boundaries, county, region and district boundaries in EPSG:2180 | Area, districts, source municipalities (D9, D11) | Cities with county rights have district codes in BREC (we combine by county code). |
| **OSM Geofabrik, `lodzkie-261015.osm.pbf`** (data up to 2026-10-15) | Road network, buildings (tag `building`), landuse (`residential`, `industrial`, `commercial`, `retail`), tags `amenity`/`shop`/`office` | Network (chapter 5), buildings of homes and work (chapter 7) | Tag quality depends on volunteers. In the Kutno municipality, 72% of buildings have `building=yes` (without type), and `building:levels` is in this group only at 2% (blocks: 84%). |
| **GBR Gdańsk 2022, Report 3a, Fig. 46** (`gbr/GBR2022_raport3a.pdf`) | Hourly schedules for "home-work" and "home-other" commutes (`config/departure_home_work_gbr2022.csv`, `config/departure_home_inne_gbr2022.csv`) | Departure hours (D14, D32) | Gdańsk Metropolis, not Kutno. Data read from the vector PDF chart. |
| **GDDKiA GPR 2025** (`g5/gpr2025/`) | Average daily traffic on 19 segments in the network (A1, DK, DW), SDRR/SDRDR, share of light and heavy | Validation (G5), calibration goal | One value for the entire segment, without hours. No urban streets except DK. |
| **GDDKiA SCPR 2025, station 14005 Lisica** (`g5/scpr2025/st_14005.pdf`) | Weekday hourly curves (digitized) | Background traffic hourly profile (K3-2) | Station 13 km from Kutno, on DK60. Digitization from the graph. |
| **GUS Mobilność 2024** (`gus_transport/mobilnosc_*`) | Work from home Łódź 7.3%; Table 10: travel rates home–X; driver's license and cars | Presence at work (K1-1), number of resident trips (D32, D36), attributes (D30) | Only the voivodeship. Rates apply to all modes of transport. |
| **Bochnia 2016, Radom 2022** (`g4/`) | Share of car in commuting home-work: 61–67%; Radom: discretionary trips 53.2% | Vehicle share (K1-1), driver trip share 0,424 (D32) | Other cities, values from the charts. |
| **CEPiK 2019** | Driver's licenses by gender and age | Attribute `license` (D30) | The registry overestimates the oldest groups. |
| **GUS Time Use Survey 2023** | Shopping, social life, and recreation times; share of people shopping by age | Stopping times and participants of trips (D32, D36) | Sum for the day, not one visit. |
| **WIOŚ 2013, points K1–K5** | Flows on five streets of Kutno | Urban street control (`pipeline/pomiary_miejskie.py`), goal scaled to 2025 by GPR | Old, one-day measurement. Order of magnitude check, not calibration. |
| **TomTom (D22, variant A)** | Travel times of routes | Speed matching (D23) | Only aggregates in the repository. New queries require approval. |
| **BDOT10k county 1002, 2025-12-09** (`g3/bdot10k/1002_GPKG.zip`) | Buildings with function and number of storeys (99.9% filled) | Homes (D28), destinations of services and other trips (D32, D36) | 39% of the geometry comes from orthophotos. 1,450 OSM buildings in Kutno have no counterpart in BDOT10k. |
| **GUS statistical address points, NSP** (`g2/adr_kutno_2026_0.csv`) | 4 807 address points of residential buildings in Kutno | Only control (G2, G3) | Nothing about entities and work. |
| **GUS accessibility matrix** (`gus_transport/macierz_dostepnosci_20210331.xlsx`) | Travel time by car between municipalities | Time control (G5), threshold D16 in minutes (unused) | GUS road model, without congestion. |
| **GTFS zbiorkom.live Kutno, GTFS rail (Kuranowski)** | Bus and train schedules | Only technical import `scenarios/kutno_pt/` (step 5), without PT agents | The GTFS license for Kutno was confirmed by the user on 2026-10-21. The railway feed is valid for 30 days. |
| **VSP and MATSim MUM 2026 Literature** (`g5/lit/`, `mum2026/`) | Reference configurations (matsim-berlin v6.3, matsim-kelheim v3.1), calibration practice | Justification `stuckTime` (D18) and dynamics `queue` | Other scales. They are not copied directly. |

**Rule:** numbers and parameters come only from sources in `docs/ZRODLA.md` and `data/manifest.csv`. Claims from auxiliary reports are checked in `docs/projekt/FACT_CHECK.md`.

---

## 5. Road network

### 5.1 Area

- **Kutno Municipality** (gm. miejska 1002011): total of 41 BREC districts, 33.55 km².
- **Kutno county commuters** (1002): 117 districts, 885.6 km².
- **Network area** = county + **3 km buffer** (`network_buffer_m = 3000` in `config/kutno.toml`).
  **ASSUMPTION:** the buffer retains the entry roads outside the county so that inbound commuters from further municipalities have somewhere to enter. The width of the buffer outside the county is open (D-open).
- Coordinates: EPSG:2180, axis order **E, N** (x ≈ 525 000, y ≈ 485 000). Transformation from WGS84 is performed once in the Java converter.

### 5.2 Conversion from OSM

- Converter: `SupersonicOsmNetworkReader` (contrib `osm`, MATSim 2026.0), only `car` mode.
- Area filter: links whose nodes lie within the network area.
- `NetworkCleaner` removes unreachable nodes and links (F2: 116 nodes and 127 links removed).
- **Border U-turns** (fix F2, A1): when the A1 motorway is truncated, it remains with unidirectional lanes that end blindly at the border, and `NetworkCleaner` would remove them until the nearest node. Therefore, every node-exit (only entrances) we connect with the nearest node-source (only exits) within a radius of **300 m**. Links receive type `boundary_turnaround`, speed 30 km/h and capacity 5 000 veh/h (ASSUMPTION values). They operate only in the band of **1 km** from the border (`boundary_zone_m`).

**Turn restrictions (D26):** Supersonic does not read OSM `restriction` relations, so a parser in `CreateKutnoNetwork` does it: 55 relations, 62 forbidden link pairs as `DisallowedNextLinks`. Routers respect them, QSim does not. The effect is below the seed spread (`reports/etap3/g1_skrzyzowania/g1.md`).

**Network result (baseline R8, unchanged up to R9.5):** 4,534 nodes, 10,383 links. State after F2 (before D23 and D26): 4,453 nodes, 10,296 links, 4,426 km. The largest strongly connected component covers **100%** of nodes. 90/90 test route pairs are reachable. No link has capacity, freespeed, length or lanes ≤ 0.

### 5.3 Speeds (D13, D23, D25)

Supersonic default speeds (VSP values for German cities) gave **15 km/h** on about 3,000 km of local, mostly rural roads. That is why speeds are set explicitly in `config/network.properties`, in this order:

1. the OSM `maxspeed` tag (also `PL:urban`, `PL:rural`, etc.) converted to km/h;
2. no tag → statutory limit by road type (Road Traffic Act, art. 20): city 50, outside city 90, residential 50, living_street 20, motorway 140, trunk 100 (**ASSUMPTION**: trunk 100, because in Poland it is usually a GP road or an expressway);
3. **freespeed = allowed speed × road-group factor** (D23, baseline since D25):

| Group | Roads | `f` |
|---|---|---:|
| A | motorway | 0.95 |
| B | national and voivodeship roads outside the city | 1.00 |
| C | tertiary and unclassified outside the city | 0.60 |
| D | residential outside the city | 0.70 |
| E | main roads in the city | 0.85 |
| F | local roads in the city | 0.55 |

Values are fitted to TomTom travel-time aggregates (D22, variant A) and rounded. This is the „as of today” state, observations for further work: `reports/etap2/g5_predkosci_d23/obserwacje_f.md`. `f_E` and `f_F` still contain intersection delays, because turn restrictions (G1) did not separate them. D23 result: route-time MAPE 20.5 → 18.2% (validation), free-flow segment speed model/TomTom 0.86 → 0.99 (`reports/etap2/g5_predkosci_d23/d23_podsumowanie.md`).

„City” = the urban municipality and towns in urban-rural municipalities from BREC (`towns.wkt`). **ASSUMPTION:** built-up villages are treated like rural roads (OSM has no built-up area boundaries).

### 5.4 Throughput and dynamics (uncalibrated)

- **Capacity** and number of lanes: default Supersonic values (e.g., tertiary 600 veh./h/lane, primary 1 500 veh./h/lane). **They are not calibrated** and do not have a local source. Half of the delays are on tertiary streets `reports/etap2/g6_kolejki/g6_kolejki.md`.
- **Intersections:** no signals or right of way. Capacity is only a link property. The G1b experiment (D27) with an inflow capacity multiplier k = 0.8 / 0.6 / 0.4 did not change GPR volumes, and at k ≤ 0.6 raised delays above the spread without independent validation. It did not become the baseline (`reports/etap3/g1_skrzyzowania/g1b.md`).
- **Queue dynamics:** `trafficDynamics = queue`. kinematicWaves (like Berlin, Kelheim) gave +56% delays, and with 300 s stuckTime gridlock (D18, G5 K5).
- **At `qsim.stuckTime = 30 s`** (D18). At 10 s and `removeStuckVehicles=false` QSim pushed vehicles onto full short links (82 vehicles on a capacity of 1.2). After the change: overloaded links 13 → 4–7.

### 5.5 Attaching activities to the network

- Candidates are the **nearest link** by distance to its segment and its reverse link. The choice minimises the free-flow route time (`snap_mode = route`, D29; `nearest` reproduces R9). U-turns at the start and end of a route fell from 35% to 12% of trips. With resident trips added in R9.5 the value is 14.3%.
- Home at the start and at the end of the day are separate links (`home_link`, `home_link_end`). Work has one link, so one U-turn per round trip remains. The variant `work_split = on` (D31) removes it, but is not in the baseline.
- Excluded types: `motorway`, `motorway_link`, `trunk`, `trunk_link`, `boundary_turnaround` (`snap_exclude_types`). Without this MATSim would attach a home to the A1 carriageway (R3/E5).
- Exception: border entries and exits keep their link.

---

## 6. Demand: who travels, from where and to where

### 6.1 Balance at 100% (baseline variant B, D17)

| Component | Number | Source | Notes |
|---|---|---|---|
| Employed persons in Kutno | **14 586** | P4507 2024 (17 255) minus outbound commuter NSP (2 669) | Baseline (B). Distribution by districts as in estimation D5. |
| Inbound commuters to Kutno | **8 139** | NSP matrix (8 186) after cutting municipalities > 100 km (D16) | 47 people from municipalities outside the county were cut off. |
| **Total employment places in Kutno** | **22 725** | sum of the two above | **Variant C** (sensitivity): 17 486 (BDL P4508), scaled by one factor. |
| Outbound commuters from Kutno in the model | **2 481** | NSP matrix minus 188 people from municipalities > 100 km | Variant O1 (D17) |

For comparison, the estimation D5 (NSP indicators × district age structure) yielded 20,215 employed residents, which is 17% more than P4507. D5 was replaced by B in D17. **Remains as distribution across districts** (`employed_base`).

**What we know and what we don't:** the identity "workplace = residents staying + inbound commuters" is not closed. Registers give 22,725, while P4508 gives 17,486. The 30% difference has no explanation in the data (G2, `docs/research/G2_warianty.md`). Therefore, C is a sensitivity variant, not an error.

### 6.2 Residents employed in Kutno (`kind = resident`)

1. Number of employed persons: P4507 (17 255) × municipality share. Outbound commuters (2 669) are subtracted.
2. Distribution across **232 statistical districts** proportionally to `employed_base` (estimation by age, D5).
3. At a 25% scale, the number of agents in the district = result × vehicle share × presence (K1-1) × sample, rounded by the largest remainder method so that the sum equals `round(sample × całość)`.

**ASSUMPTION (D5):** we apply the employment indicators from tables for cities in the Łódź voivodeship (production and post-production, GUS method) to age groups within the district. The population table does not cross gender with age, so we do not know if the gender structure changes the result.

### 6.3 Inbound commuters to Kutno (`kind = commuter`)

- Number and source municipalities: NSP 2021 matrix (134 municipalities, 8,186 persons).
- **Municipalities in the Kutno county (D9):** home is a random residential building from BDOT10k in the source municipality (D28, same pool and weight as residents). Start at the entrance to Kutno at the time from the profile (chapter 9).
- **Municipalities outside the county (D16/A):** agent appears at the nearest **border entrance** to the municipality's centroid, at the time from the profile. Commute time outside the network is not added (**ASSUMPTION**: as D16/A; previously 72 km/h × 1.3 was added, resulting in starts after midnight).
- **Cut-off > 100 km (D16/B, ASSUMPTION):** municipalities whose centroid is further than **100 km** from the nearest entrance are omitted. This includes 12 municipalities (47 people in 100%), including Szczecin, Gdańsk, Kraków, Wrocław, Poznań. Warsaw (approx. 89 km from the entrance) remains: 27 inbound commuters, and 457 outbound commuters in the NSP matrix. The threshold `max_border_km` is in `config/kutno.toml`.
- Inflows: 31 links of types `motorway`, `trunk`, `primary`, `secondary` in the zone 1 km from the border, directed to Kutno (ASSUMPTION, `entry_road_types`, `entry_zone_m`).

### 6.4 Outbound commuters from Kutno (`kind = outbound`, D17/O1)

- Number and target municipalities: NSP matrix (83 municipalities, 2,669 people).
- **House:** random residential building in the Kutno district, weighted by employed persons (as residents).
- **Work:** in the county's municipalities, random workplace in the target municipality. Municipalities outside the county: **outbound** (exit link closest to the municipality's centroid, mirror of entrances).
- Departure time from profile, work 8 h. After work returns at the same time, without commute time outside the network (ASSUMPTION).

**Why O1:** traffic exists and loads the same inlets as inbound commuters, but in the opposite direction. Without it, the outlet flows would be underestimated (G2).

### 6.5 Vehicle share and presence at work (K1-1, D19)

- All categories (residents, inbound commuter, outbound commuter) are multiplied by:
  - **vehicle share 0,64** (middle of the range 61–67% from Bochnia and Radom; `car_share`);
  - **1 − 0,073** (working exclusively from home, Łódź according to GUS Mobilność 2024; `work_from_home`).
  - - **× 0.593**
- **Result:** plans drop by 25% from 6,302 to 3,739 persons.
- **Methodological note:** the reduction acts on the count in each group (district, commune), not by randomly omitting specific individuals. Residents in districts with a low share of cars are not distinguished.
- **Status:** adopted in D19. Values come from other cities (**ASSUMPTION**).

### 6.6 Sample and scale

- **Scale:** 10%, 25%, 100%. Results are reported from **25%, 5 runs** (3 MATSim seeds and 2 plan seeds), 50 iterations (user decision 2026-10-23). 100% only on explicit request.
- **Seed:** 4711 (default in the config), 1, 2.
- **Throughput scaled to sample:** `flowCapacityFactor = storageCapacityFactor = sampleSize` (MATSim 2026 requires their equality, D8, D15/5).
- Results at 100% reproduction are achieved by `× 1/sampleSize` (applies to intensities and GEH; `convergence.py` does it automatically).

### 6.7 Resident trips (`errands.py`, D32, D34, D36)

Separate trips `home → cel → home`, car driver only. A trip agent is a separate person, not linked to a worker (**ASSUMPTION**).

- **Number of trips** = GUS Mobilność 2024 rate (table 10, Łódzkie, per 2,146,153 persons aged 6+) × Kutno population aged 6+ × `errand_car_share` × sample.
- **`errand_car_share` = 0.424** (**ASSUMPTION**): Radom GOFR 2022, discretionary trips 53.2%, × 0.797 (drivers among car trips, GUS Łódzkie). Variants 0.304 and 0.479.
- **Participants:** age ≥ 18, `license = yes`, `carAvail ≠ never`, weighted by age from the GUS Time Use Survey 2023.
- **Time:** GBR Gdańsk 2022 „home–other”, intervals 5–20 h.

| Type | Destination | Stop | GUS rate (home–X trips) | Trips in the 25% plan |
|---|---|---:|---:|---:|
| `shop`, `service` | OSM shops (D34): `supermarket`, `mall`, `department_store` and other `shop=*`, weight = number of shops; services from BDOT10k, weight = footprint | 57 min | 102 892 + 229 380 + 25 702 | 711 |
| `visit` | residential buildings | 1 h 28 min | 70 062 | 139 |
| `leisure` | culture, sport, gastronomy (BDOT10k) | 1 h 36 min | 90 163 | 179 |
| `health` | healthcare, hospital, pharmacy (BDOT10k) | 57 min | 78 397 | 156 |
| `escort` | nearest primary school, kindergarten, nursery | 5 min | 146 725 | 292 |

In total 1,477 trips in the 25% plan. Destination choice does not depend on distance (except `escort`). A measurement of distance variants showed almost no effect in Kutno (`reports/etap3/g_zakupy/odleglosc/pomiar_beta.md`). The duration for `health` is an **ASSUMPTION** (as shopping, no category in GUS).

### 6.8 Background traffic (`background_od.py`, D19–D21)

Subpopulations `tlo` (light and delivery, pce 1.0) and `ciezkie` (pce 2.5, 80 km/h). Matrices `scenarios/kutno/demand/background_od_r94e_{lcv,heavy}_gpr.csv` are estimated from GPR 2025 against runs of workers and resident trips without background. In the 25% plan: 11,961 `tlo` agents and 4,840 `ciezkie`, hourly profile from the Lisica station. Border zones per road with GPR weight, heavy trip ends in work buildings (`pipeline/border_zones.py`). Known limitations: zones of DK91 north-west and south-west and DK92 east are not constrained by GPR (D25).

---

## 7. Locations: where are the homes and workplaces from

Residents' homes are **BDOT10k buildings** weighted by **footprint × storeys** (D28). Workplaces are **OSM buildings** weighted by **footprint area** (D7). Background trip ends are OSM buildings. Sampling is with replacement and the seed is in the config (`seed = 4711`). Destinations of resident trips: chapter 6.7.

### 7.1 Building filters

**Residential, BDOT10k** (`home_source = "bdot"`, ASSUMPTION D28): `OT_BUBD_A` of county 1002, `KATEGORIAISTNIENIA = eksploatowany`, main function „budynek jednorodzinny” or „budynek wielorodzinny” (19,520 of 19,644 residential buildings in the county). Rejected include holiday homes, parish houses, care homes, dormitories, monasteries. The variant `home_source = "osm"` reproduces R7b/R8.

**Work, OSM** (`work_buildings`, ASSUMPTION D7): `retail`, `industrial`, `warehouse`, `office`, `commercial`, `school`, `hospital`, `public`, `civic`, `government`, `kindergarten`, `university`, `college`, `supermarket`, `service`, `fire_station`, `train_station`, `transportation`, `manufacture`, `factory`, `hotel`, and also any building tagged `amenity`/`shop`/`office` and `building=yes` in landuse `industrial`, `commercial`, `retail`. Only within the Kutno municipality (for agents from Kutno).

**Exclusions from OSM data:**
- `building=no` is treated as no building (a car dealership yard with `shop=car`, 3.6 ha, was the largest „workplace”, R3/error 1).
- A residential OSM building cannot be a work building (`loc[work, residential] = False`).

### 7.2 Homes

- **Residents:** a BDOT10k building in the census district, weight footprint × `LICZBAKONDYGNACJI` (missing = 1). A district without a candidate takes the nearest home within 100 m (`home_nearest_max_m`, ASSUMPTION), otherwise a random point in the district (district 6509214).
- **Inbound commuters from the county:** the same pool of homes, a random building in the source municipality.
- **Inbound and outbound commuters from outside the county:** they have no home in Kutno. Start/end on a border link.

**Agreement with the GUS 250 m grid:** mass deviation 10.3 pp (OSM) → 8.1 pp (BDOT10k). Traffic unchanged beyond the plan spread (`reports/etap3/g3_domy/g3.md`).

### 7.3 Employment locations

- Random selection with **area weight** from the list of workplaces in the Kutno municipality. Candidates: 1 103, 473 buildings were selected in 10% (F4).
- Top 5 buildings receive 13% of agents (large halls in the eastern zone). These are real objects (`industrial` and `warehouse`, 1.6–3.1 ha), verified during the pre-run check (D16).
- **ASSUMPTION:** employment distribution within the municipality is reflected by building area. There are no REGON or facility addresses in the model (D7, G2 open).

### 7.4 Link assignment

Each home and workplace receives a network link according to the rules from section 5.5 (`snap_mode = route`, D29). Inbound and outbound commuters from outside the county immediately have a border link.

---

## 8. Agent characteristics: what we know about a person

Agents are created from **aggregates**, not microdata. We do not reconstruct households (project rules). Attributes from D30 do not affect QSim: the strategies are only `ChangeExpBeta` and `ReRoute`. A test on GitHub Actions gave identical routes, legs, volumes and score (run 40189940976).

| Attribute | Value | Source |
|---|---|---|
| `subpopulation` | `person`, `tlo`, `ciezkie` | constant (required by SimWrapper and strategies) |
| `kind` | `resident` / `commuter` / `outbound` | demand type (6.2–6.4) |
| `id` | `r<obwód>_<n>`, `c<gmina>_<n>`, `o<gmina>_<n>`, `h…` for heavy | unique (test in `plans.py`) |
| home | BDOT10k building and link | chapter 7.2 |
| work or trip destination | building and link | chapters 6.7, 7.3 |
| departure time | from the GBR profile (chapter 9) | sampled from an interval |
| `age`, `sex` | population × employment (Polish cities) × P(licence) | BDL P4181, NSP 2021 (D30) |
| `license` | yes/no | CEPiK 2019 / NSP 2021, shifted to 60.6% in Łódzkie (GUS Mobilność 2024); men 65+ as 55–64 (**ASSUMPTION**) |
| `carAvail` | always / sometimes / never | cars / licence holders in Łódzkie = 0.73 (**ASSUMPTION**: one car = one holder) |

The full Kutno population (42,255 persons with attributes) is in `scenarios/kutno/demand/population_kutno.csv`. Report: `reports/etap3/g_atrybuty/atrybuty.md`.

**What agents do NOT have:** education, occupation, income, household. The age of inbound commuters comes from the Kutno distribution, not from their municipalities.

---

## 9. Daily plans: chains and hours

**Worker chain:** `home (end_time = departure) → car → work (max_dur = 8:00:00) → car → home`. **Resident trip:** `home → car → destination (max_dur by type, chapter 6.7) → car → home`. Test: three activities and two car legs, `end_time` XOR `max_dur` (project rules). Daily chains of workers (escorting before work, shopping after work) are the variant `chains = on` (D35), not the baseline.

**Departure time of workers (D14):**
1. Sampling of the hourly interval from the "home–work" distribution GBR Gdańsk 2022, Fig. 46 (`config/departure_home_work_gbr2022.csv`, 18 intervals after normalization to 100%). The 20–24 h interval is one 4-hour interval.
2. Time is uniformly randomized in the range (**ASSUMPTION**).
3. Outbound from home = this hour. Inbound commuter from the border: time of entry at the border.

**Time limitations:**
- The distribution is from the Gdańsk metropolis (**ASSUMPTION** that it fits Kutno).
- No local hourly distribution (decision D10 open, R1: `docs/research/R1_godziny.md`). Review of Polish travel surveys for this and other parameters: `docs/research/badania_ruchu_PL.md`.
- Start no later than 23:52.

**8 h working time** (`work_max_dur`): **ASSUMPTION** rounded from GUS BCL 2013 (average of 8 h 11 min for hired workers). This is not a distribution per agent. `TimeAllocationMutator` **disabled** (hours from data should not drift).

**Simulation end:** `qsim.endTime = 48:00:00` (reserve; 36:00 interrupted the agent from Kraków, `stuckAndAbort`, R3).

---

## 10. MATSim simulation (configuration)

Files: `scenarios/kutno/config_{10,25,100}pct.xml`. Paths are relative to the configuration. `controller.outputDirectory` is relative to the working directory, so run from the project directory.

| Parameter | Value | Justification |
|---|---|---|
| MATSim | 2026.0, Java 25 | `matsim/` (matsim-example-project @ 74d23af) |
| `lastIteration` | 100 in the config; GitHub Actions runs use 50 (`--iterations`) | user decision 2026-10-23: new runs at most 50 iterations |
| `flowCapacityFactor` = `storageCapacityFactor` | = sampleSize (0.25 for 25%) | D8, MATSim 2026 requires equality |
| `stuckTime` | 30 s | D18 |
| `trafficDynamics` | `queue` | D18, G5 K5 |
| `endTime` | 48:00:00 | Chapter 9 |
| `randomSeed` | 4711 (1, 2 for variance) | config |
| `coordinateSystem` | EPSG:2180 | project principles (D-spec) |
| `numberOfThreads` | 8 in the configuration; runs with 4 or 2 threads | the number of threads does not shorten the run, 4 and 8 give identical results |
| `linkDynamics` | `PassingQ` | D20: cars overtake heavy vehicles (80 km/h) |
| Strategies | `ChangeExpBeta` 0.8, `ReRoute` 0.2 | separately for `person`, `tlo`, `ciezkie` |
| `fractionOfIterationsToDisableInnovation` | 0.8 | after 80 iterations only the plan selection (the score flattens by definition) |
| Scoring | MATSim default; typical: `home` 16 h, `work` 8 h, `shop` and `service` 57 min, `visit` 1 h 28 min, `leisure` 1 h 36 min, `health` 57 min, `escort` 5 min | **ASSUMPTION**, score is diagnostic only |
| Plans | `plans_g3r95_{10.25.100}pct` | baseline R9.5 (D36) |
| MATSim, linkStats | enabled; linkStats every 10 it. (average of 5) | R3/E2, convergence diagnostics |

**What is in the output:** `output_events.xml.zst` (events, format `.zst`), `output_links.csv.zst`, `modestats`, `scorestats`, `traveldistancestats` (MATSim). Charts: `pipeline/plot_run.py`.

**What MATSim does with legs:** in `car` mode, MATSim automatically attaches teleported legs `walk` (arrival and departure). They are not part of the traffic model, but must be filtered out when counting legs.

---

## 11. Validation and results

### 11.1 Tests

| Test | Script | What it checks |
|---|---|---|
| Events | `pipeline/check_events.py` | `departure = arrival`, 0 `stuck` (also `stuckAndAbort`), number of car legs = number in plans |
| Plans | `pipeline/validate_plans.py` | chain, area, employment in the Kutno municipality, number of people, sha256 repeatability |
| Network | `pipeline/validate_network.py` | area, SCC, attributes, test routes |
| Demand | `pipeline/demand.py` (assertions) | population total 42,255, 8,186 inbound commuters, join 232/232 |
| Link overflow | `pipeline/queues.py` | `overfilled_links_gt2x` (D18) |
| Convergence | `pipeline/convergence.py` | change of intensities for top-50 links, GEH between seeds (scale 100%) |
| Model vs GPR | `pipeline/g5_baseline.py` | GPR on 19 segments (A1, DK, DW) |
| Model vs city streets | `pipeline/pomiary_miejskie.py` | model / WIOŚ 2013 K1–K5 scaled to 2025 (a check, not calibration) |
| O-D matrices | `pipeline/od_warnings.py` | warnings after each estimation |

**Project principle:** A run without errors is not proof. The semantic test counts the stage.

### 11.2 Baseline R9.5 (GitHub Actions test, 2026-10-31)

Source: `reports/etap3/g_inne_cele/inne_cele.md`, `inne_cele_porownanie.json`, run 41200518829. 25%, 50 iterations, median of 5 runs (3 MATSim seeds and 2 plan seeds), control R9.4 on the same platform.

| Measure | R9.5 | R9.4 | Plan-seed spread of R9.4 |
|---|---:|---:|---:|
| stuck | 0 | 0 | – |
| car legs = plans | yes (27,233) | yes (25,701) | – |
| delay, sample vehicle-hours | 243.8 | 236.5 | 17.8 |
| GPR light within ±15% | 15/15 | 15/15 | – |
| GPR heavy within ±15% | 14/15 (outside: 91878, −15.1%) | 13/15 | – |
| workers' trips: time / distance | 17.15 min / 11.11 km | 17.13 min / 11.11 km | 0.26 min |
| U-turns at route start or end, % of trips | 14.3 | 13.5 | – |
| city streets K1–K5, total, % of 2025 target | 43.6 | 40.9 | – |

**City streets (D37), a known limitation:**

| Point | 2025 target [veh/day] | R9.5 | % of target |
|---|---:|---:|---:|
| K1 Toruńska | 12 910 | 2 876 | 22.3 |
| K2 Łąkoszyńska | 8 367 | 3 884 | 46.4 |
| K3 Grunwaldzka | 3 805 | 3 280 | 86.2 |
| K4 Kościuszki | 4 208 | 2 500 | 59.4 |
| K5 Łęczycka | 9 850 | 4 536 | 46.0 |

The target is a one-day count from 2013 scaled by GPR, so this is an order-of-magnitude check. After D36 we do not add demand or tune parameters to K1–K5. Missing are, among others, non-work trips from outside the city, trips not based at home, business and delivery traffic in the city, and school (`reports/etap3/g_pomiary_miejskie/popyt_brak.md`, `k1_zachod.md`).

**Spread:** sampling of plans and O-D estimation points gives a spread 20–100 times larger than MATSim seeds (median 9–12% per section vs 0.1–0.4%, baseline R6). Judge variant differences against the plan-seed spread.

**Travel times:** validation against TomTom (D22, D25) applies to R7b: 58% of routes within 15% or 1 min, against the required > 85% by TAG. The model is calibrated in demand, not validated on times. Later baselines were not checked with new queries.

### 11.3 How the baseline changed

Each step changes one thing, and traffic changes are judged against the plan-seed spread.

| Baseline | Decision | What was added | Effect | Report |
|---|---|---|---|---|
| R6 | D19–D21 | background, delivery and heavy vehicles, fixes after the G5 audit | GPR light 12/15, heavy 12/15 | `reports/etap2/g5_kalibracja/g5_r6_ref.md` |
| R7b | D23, D25 | speeds per road group | GPR light 14/15, time MAPE 20.5 → 18.2% | `reports/etap2/g5_predkosci_d23/d23_podsumowanie.md` |
| R8 | D26 | turn restrictions | below the seed spread | `reports/etap3/g1_skrzyzowania/g1.md` |
| R9 | D28 | homes from BDOT10k | GUS 250 m: 10.3 → 8.1 pp; traffic within spread | `reports/etap3/g3_domy/g3.md` |
| R9.1 | D29 | link direction by route | U-turns 35.1 → 12.4% of trips | `reports/etap3/g_zawrotki/zawrotki.md` |
| R9.2 | D30 | person attributes | simulation unchanged | `reports/etap3/g_atrybuty/atrybuty.md` |
| R9.3 | D32 | shopping and services | delay +5.8% (spread 13.9%), GPR light 15/15 | `reports/etap3/g_zakupy/zakupy.md` |
| R9.4 | D34 | shopping destinations from OSM shops | trips 16% shorter in km, the rest within spread | `reports/etap3/g_zakupy/cel_osm/cel_osm.md` |
| R9.5 | D36 | visits, leisure, health, escorting | K1–K5 40.9 → 43.6% of target, GPR within spread | `reports/etap3/g_inne_cele/inne_cele.md` |

Variants tested but outside the baseline: G1b (D27, inflow capacity), `work_split` (D31, U-turns 12.4 → 1.1%), `chains` (D35, daily chains, traffic within spread). Results before background traffic (D18, R1) are historical: `reports/etap2/g6_kolejki/g6_kolejki.md`, `reports/etap2/g5_kalibracja/`.

---

## 12. Assumptions (summary table)

Each ASSUMPTION has a value, location in the code or config, justification and status.

| ID | ASSUMPTION | Value | Where | Justification / status |
|---|---|---|---|---|
| A-1 | Network scope = district + buffer | 3 000 m | `config/kutno.toml` `network_buffer_m` | D9, for verification in F2 (open: width outside the county) |
| A-2 | Turns at the border | 300 m, 30 km/h, capacity 5 000, zone 1 km | `config/network.properties` | F2 (A1), D9 |
| A-3 | Speed = limit × road-group `f` | A 0.95, B 1.00, C 0.60, D 0.70, E 0.85, F 0.55 | `config/network.properties` | D23, D25; fitted to TomTom aggregates, „as of today” |
| A-4 | Villages as local roads | rural commuters 90 | `config/network.properties` | lack of built-up area boundaries in OSM |
| A-5 | Trunk = 100 km/h | trunk 100 | `config/network.properties` | GP or expressway, for confirmation |
| A-6 | Default capacity Supersonic | tertiary 600, primary 1 500 veh./h/lane | MATSim | **uncalibrated**, lack of local source (G1, G5 K5) |
| A-7 | Employed person residents | P4507 2024 = 17 255 | `config/kutno.toml` `employed_residents_reg` | D17/B, register |
| A-8 | Variant of the number of jobs | B (baseline), C = 17 486 | `config/kutno.toml` `jobs_total` | D17, 30% unexplained gap |
| A-9 | Outbound commuter in the model | O1, anchor year 2024 | `plans.py`, `demand.py` | stage D17, stage G2 |
| A-10 | Employment indicators | production 0,784 (baseline), post-production according to TABL. 5 | `demand.py` (rozkład obwodów) | D5, only the voivodeship |
| A-11 | Range 0–17 for the pre-production group | voivodeship indicator | `demand.py` | D5 |
| A-12 | Cutting municipalities commuters > 100 km from the entrance | 100 km | `config/kutno.toml` `max_border_km` | D16/B, user decision |
| A-13 | Inbound commuter from the border | hour from the profile, without commute | `plans.py` | D16/A |
| A-14 | Entry: link type | motorway, trunk, primary, secondary; 1 km zone | `config/kutno.toml` `entry_road_types`, `entry_zone_m` | D9 |
| A-15 | Inbound commuter from the district | random building in the source municipality | `plans.py` | D9 |
| A-16 | Residential (BDOT10k) and work (OSM) buildings | chapter 7.1 | `config/kutno.toml` | D28, D7 |
| A-17 | Weights: homes footprint × storeys, work footprint | m² | `plans.py` | D28, D7 |
| A-18 | District without a building → nearest home within 100 m, otherwise a random point | 100 m | `config/kutno.toml` `home_nearest_max_m` | D28, applies to districts 6509902 and 6509214 |
| A-19 | Car share home–work | 0.64 (61–67%) | `config/kutno.toml` `car_share` | D19/K1-1, Bochnia 2016, Radom 2022 |
| A-20 | Working from home | 7.3% | `config/kutno.toml` `work_from_home` | GUS Mobilność 2024, table 1 |
| A-21 | Departure profile | GBR Gdańsk 2022 | `config/departure_home_work_gbr2022.csv` | D14, metropolis, not Kutno |
| A-22 | Hour uniformly in the interval | — | `plans.py` | ASSUMPTION D14 |
| A-23 | Working time 8 h | 08:00:00 | `config/kutno.toml` `work_max_dur` | GUS BCL 2013, rounded |
| A-24 | Missing TimeAllocationMutator | — | config | hours from data |
| A-25 | Scoring: typical duration by activity type | chapter 10 | `config_*.xml` | MATSim default, diagnostic score |
| A-26 | Sampling and rounding | 25% (results), method of largest residuals | `plans.py` | D15/3, D8 |
| A-27 | seed | 4711, 1, 2 | config, `output/r3_runs.sh` | D15 |
| A-28 | `stuckTime` | 30 s | config | D18, Berlin/Kelheim |
| A-29 | Dynamics `queue` | — | config | D18, G5 K5 |
| A-30 | Background traffic from O-D estimation (light + freight, heavy) | 20 points for the municipality, τ = 30 min, entry weight = capacity | `pipeline/background_od.py` | D19–D21; calibration estimated to GPR, spread depends on the point seed |
| A-31 | No pedestrians, cyclists or PT; heavy vehicles only as background (pce 2.5, 80 km/h) | — | — | D6, D20; steps 5–6 in ROADMAP |
| A-32 | Delays on the link, not at the intersection; turn restrictions only in the router | — | — | D26; signals later |
| A-33 | Working day | — | — | typical working day (GUS, GBR) |
| A-34 | Link direction by free-flow route, ignoring turn restrictions | `snap_mode = route` | `config/kutno.toml` | D29 |
| A-35 | Attributes: men 65+ as 55–64; one car = one licence holder | 0.73 | `config/kutno.toml`, `pipeline/attributes.py` | D30 |
| A-36 | Driver share of resident trips | 0.424 (variants 0.304, 0.479) | `config/kutno.toml` `errand_car_share` | D32, Radom GOFR 2022 × GUS Łódzkie |
| A-37 | A trip = a separate agent, not linked to a worker | — | `pipeline/errands.py` | D32 |
| A-38 | Trip times = GBR Gdańsk „home–other” | intervals 5–20 h | `config/departure_home_inne_gbr2022.csv` | D32, a metropolis, not Kutno |
| A-39 | Stop durations | chapter 6.7 | `config/kutno.toml` | D32, D36, GUS Time Use Survey 2023; `health` as shopping |
| A-40 | Destinations: independent of distance (except `escort`) | weight per chapter 6.7 | `pipeline/errands.py` | D32, D34, D36 |
| A-41 | Shops: all `shop=*` except `vacant`, Eurocash in type c, OSM incomplete | within 15 m of a building | `config/kutno.toml` `errand_poi_m` | D34 |

---

## 13. Limitations, known problems and gaps

### 13.1 Configuration consistency

- **R-1: `scenarios/kutno/plans.xml.gz` and `plans_25pct_bez_k1`** are files from stages F5–D18, not used by current configs. `config_{10,25,100}pct.xml` point to plans `plans_g3r95_*pct`.
- **R-2: no single script reproduces everything.** The order is in chapter 2, and recipes for individual baselines are in reports. `output/r3_runs.sh` is outside git, and new runs go through GitHub Actions anyway.
- **R-3:** `config_25pct.xml` has 8 threads, while GitHub Actions runs use 2 (`threads`). Threads do not shorten a run, and 1 thread gives different results than 4 and 8.

### 13.2 Data limitations and methods

- NSP matrix: only employed persons, without flows < 3 people and without intra-municipal traffic. Lower bound of outflow and inflow (underestimates traffic).
- Workplace in the matrix = employer address (headquarters). Distant relationships (Warsaw 457) may be a result of the company's headquarters, not actual commute.
- Employment indicators only at the voivodeship level. Estimation D5 is 17% higher than the register.
- Employed person per district (232) is an estimation, not an observation (D5).
- OSM data: 72% of the municipality's buildings have `building=yes` without type, and only 2% in them is `building:levels`. Therefore, the weights of workplaces (outline area) are approximate.
- Rates of resident trips come from the whole voivodeship and cover all transport modes. The driver share is from Radom and Łódzkie.
- Hourly data for trips and commuting are from Gdańsk. Better templates for mid-sized cities: `docs/research/badania_ruchu_PL.md`.
- 1 450 buildings in OSM in Kutno have no counterpart in BDOT10k (G3).
- Person attributes are not crossed with the census district: an agent's age and sex do not follow from the structure of their district.

### 13.3 Limitations of the model

- **City streets outside GPR are underestimated by roughly half (D37):** K1–K5 43.6% of target, Toruńska 22%. On GPR roads the model is within ±15%, but GPR sections are mainly through roads, so they do not test traffic in the city.
- No signals or right of way. Turn restrictions only in the router. Queues result from link capacity and `stuckTime`, not from conflicts at intersections.
- Travel times are not validated by TAG (D25), and have not been checked with new queries after R7b.
- No time during commute outside the network: inbound and outbound commuters "teleport" at the border (ASSUMPTION, D16/A).
- One typical working day, without weekends and holidays.
- No random variability in working time per agent (fixed 8 h).
- Default scoring: route choice is real, but the score is not calibrated and is not used for conclusions. Strategies only choose plans and routes, they do not change times or modes.
- All agents travel by car, so person attributes and the GTFS timetable do not change anything in the simulation yet.
- Non-linearly sensitive results to demand (C vs B: delays -71% at -22% demand). The number of jobs is the most sensitive parameter.

---

## 14. Gaps: what is still missing

Status as of 2026-11-03. The full list of open issues and their order: `docs/projekt/ROADMAP.md`.

| # | Gap | Status | Described in |
|---|---|---|---|
| L-1 | **Traffic on city streets** outside GPR underestimated by about half. | known limitation (D37), until step 6 or new data | `reports/etap3/g_pomiary_miejskie/popyt_brak.md` |
| L-2 | **School** as a trip purpose. | plan without implementation, awaiting decision (D33) | `docs/research/G_szkola_4B_plan.md` |
| L-3 | **Public transport, cycling, walking, mode choice**. GTFS imported technically (22 lines, 446 trips), without PT agents and without ASC calibration. | steps 5–6 | `reports/etap3/g_pt_import/pt_import.md`, `docs/research/G4_tryby.md` |
| L-4 | **Daily chains** of workers. | variant ready (`chains = on`), awaiting decision (D35) | `reports/etap3/g_lancuchy/lancuchy.md` |
| L-5 | **Distance in destination choice** of resident trips. | measured without implementation, almost no effect in Kutno | `reports/etap3/g_zakupy/odleglosc/pomiar_beta.md` |
| L-6 | **Distribution of workplaces within the municipality**: weights by building area, without REGON and company addresses. | known limitation of G2 | `docs/research/G2_miejsca_pracy.md` |
| L-7 | **Car share K1-1**: source from other cities, no local data. | decision made, weak data | `docs/research/G5_plan_kalibracji.md` |
| L-8 | **Departure times from a local source** (D10): today GBR Gdańsk, Lisica profile for background. | research | `docs/research/R1_godziny.md`, `docs/research/badania_ruchu_PL.md` |
| L-9 | **Working time 8 h**: a fixed ASSUMPTION, no per-agent distribution. | research | `docs/research/R1_godziny.md` |
| L-10 | **Capacity of city streets and signals**: no local data, G1b without validation. | possibly after G1 | `reports/etap3/g1_skrzyzowania/g1b.md` |
| L-11 | **Speeds `f`**: „as of today” values, re-validating times requires consent for new queries (D22). | open | `reports/etap2/g5_predkosci_d23/obserwacje_f.md` |
| L-12 | **Rebuild from scratch** on a clean clone and a single script. | step 8 | `docs/projekt/ROADMAP.md` |

Open questions from `docs/projekt/DECISIONS.md`, without a decision: buffer width outside the county, scoring parameters, working-time distribution.

---

## 15. Project structure

| Path | Contents | In git |
|---|---|---|
| `docs/projekt/ROADMAP.md` | phases, status, further plans | yes |
| `docs/projekt/DECISIONS.md` | decisions D1–D37 (change = new entry) | yes |
| `docs/projekt/FACT_CHECK.md` | verified facts from AI reports | yes |
| `docs/projekt/TASKS.md` | phase contracts F0–F6 and stage 2 | yes |
| `docs/projekt/PROGRESS.md` | what passed, with evidence | yes |
| `docs/projekt/ERRORS.md` | errors and rules | yes |
| `config/` | `kutno.toml`, `network.properties`, hourly profiles, trip participation | yes |
| `data/manifest.csv` | URL, date, bytes and SHA-256 of each download | yes |
| `data/raw/` | downloaded sources (read-only) | no |
| `pipeline/` | Python scripts (data, plans, analysis, validation) | yes |
| `matsim/` | Java project (`CreateKutnoNetwork`, `mvnw`) | yes |
| `.github/workflows/` | MATSim runs and O-D estimation (chapter 2) | yes |
| `scenarios/smoke/` | regression test, 10 agents | yes |
| `scenarios/kutno/` | network, plans, configs, demand CSV (`*.xml.gz` excluded from git) | partly |
| `scenarios/kutno_r91/` | GHA test inputs: plans, vehicles, meta of variants `p0`–`p2`, also R9.5 (`r94e`) | yes |
| `scenarios/kutno_od/` | O-D estimation inputs: plans without background, config | yes |
| `scenarios/kutno_pt/` | GTFS import: schedule, vehicles, network with PT links (`pipeline/build_kutno_pt.sh`) | yes |
| `scenarios/kutno_g1b/`, `scenarios/kutno_r7b_*` | inputs of historical tests | yes |
| `reports/` | reports and evidence per phase (`reports/README.md`) | yes |
| `docs/research/` | analyses and methodological background | yes |
| `docs/ZRODLA.md` | source catalogue | yes |
| `output/` | MATSim runs | no |
| `blender/` | G6 visualization | yes |

The run player (visualizer) is in a separate repository, [easy-matplayer](https://github.com/GISBoost/easy-matplayer).

**Current reference results:** baseline R9.5, `reports/etap3/g_inne_cele/inne_cele.md` (25%, 3 MATSim seeds + 2 plan seeds, 50 iterations). Earlier baselines: chapter 11.3.

---

## 16. Glossary

| Abbreviation | Significance |
|---|---|
| BDL | GUS Local Database. P4507 = employed residents, P4508 = employed persons by payer seat |
| BDOT10k | Topographical Object Database (buildings, floors) |
| BREC | Baseline of Registry of Characteristics (areas and statistical districts of NSP 2021) |
| CRS EPSG:2180 | PUWG 1992 layout, E, N axes |
| D1–D37 | project decisions (`docs/projekt/DECISIONS.md`) |
| GEH | Concentration agreement measure (< 5 = good agreement) |
| GPR | General Traffic Measurement of the General Directorate for National Roads and Motorways (SDRR, SDRDR, SDRL) |
| GBR | Gdańskie Badania Ruchu, Report 3a (mobility survey, hourly profile) |
| GTFS | public transport timetable (format) |
| K1–K5, G1–G7 | calibration steps (`G5_plan_kalibracji.md`) and project phases (`docs/projekt/TASKS.md`). In chapter 11, K1–K5 are the WIOŚ 2013 count points |
| GHA | GitHub Actions |
| R6…R9.5 | successive model baselines (chapter 11.3) |
| WIOŚ | Voivodeship Inspectorate for Environmental Protection |
| MVP | first model scope, closed: car, home–work–home |
| NSP 2021 | National Census commuters 2021 |
| Origin-Destination | trip matrix (origin-destination) |
| Peak Congestion Effect | passenger car equivalent factor (truck) |
| QSim | MATSim queueing simulation engine |
| SCPR | Continuous Traffic Measurement Stations (GDDKiA) |
| SDRDR | average daily traffic on weekdays (GPR) |
| TERC | territorial unit identifier (1002011 = municipality of Kutno) |
| TABLE 5 | GUS table "Population in the labor market" (employment indicators) |

## 17. License

- **Code** (`pipeline/`, `matsim/src/`, `blender/`, scripts in `reports/` and `docs/`): GPL-3.0-or-later, file [LICENSE](LICENSE).
- **Data and results from GUS**: CC BY 4.0 (source required: Główny Urząd Statystyczny).
- **Data from OpenStreetMap**: ODbL 1.0 (© OpenStreetMap contributors). Extracted bases from OSM data are published under ODbL.
- **Example MATSim project** in `matsim/`: GPL-2.0-or-later, file `matsim/LICENSE`.
- Full division and reservations: [LICENSE-DATA.md](LICENSE-DATA.md).
