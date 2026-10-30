# MATSim Kutno: model guide

**English** | [Polski](README.pl.md)

Status: 2026-10-20. The description assumes decisions D1–D23 from `docs/projekt/DECISIONS.md` and results from `docs/projekt/PROGRESS.md`. Chapters 5–13 describe the model up to D19 (baseline D18 and R1); changes D20–D23 (background traffic, delivery and heavy, baseline R6, speeds per road group) are in chapter 11.4 and 12, with details in `docs/projekt/ROADMAP.md`.
Each assumption is marked as **ASSUMPTION** or has a source (file, line, URL in `data/manifest.csv` and `docs/ZRODLA.md`).
Missing elements are in chapter 14 ("Gaps"), with a reference to the document that describes them. Project map (stages, status, plans): [docs/projekt/ROADMAP.md](docs/projekt/ROADMAP.md).

> **Important:** this is a model of commuting traffic by car in the Kutno municipality, not a traffic forecast. The results are used to check the correctness of the pipeline and the sensibility of the geography (D2). Comparisons with measurements are at the calibration stage (G5, D19).

---

## 1. Purpose, scope and what the model does not do

**Goal:** agent-based simulation of MATSim for the urban commune of Kutno (TERC 1002011, 42,255 inhabitants according to NSP 2021). Kutno is a testing ground for the methodology, which we will later transfer to Łódź, but only after completing work on Kutno itself.

Scope of the MVP (D3, D6):
- agent travels by **car** in the chain `dom → praca → dom`;
- demand includes: residents of Kutno employed in Kutno (D17, register), inbound commuters to Kutno from the GUS matrix, and from D17 also outbound commuters from Kutno for work outside the city;
- from D19 to demand the vehicle share and presence at work factor (K1-1) is added.

What the model DOES NOT do (consciously, scope frozen):
- does not model public transit, pedestrians, cyclists (modes: chapter G4, inactive);
- does not model other trip purposes (shopping, school, errands); freight and heavy traffic is only background traffic from the O-D estimation (D20), not a behavior model;
- does not model traffic light signals, intersections, priority or turning restrictions (G1 set by user);
- no mode choice or scoring calibration available;
- transit and background traffic (traffic from outside the network) is from D19–D21 in runs as subpopulations `tlo` (light and freight) and `ciezkie`, estimated from GPR counter matrices O-D. This is a calibration estimation to measurements, not an observation (chapter 11.4).

---

## 2. How to replay the results

All steps are in the project. Raw data (`data/raw/`) is not in git, but each file has a URL and SHA-256 checksum in `data/manifest.csv`.

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
uv run python -W ignore pipeline/validate_plans.py scenarios/kutno/plans_25pct_bez_k1.xml.gz 0.25 <katalog_raportu>

# 7. Run MATSim (z katalogu projektu, nie z katalogu configu)
java -Xmx10g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run \
  --config scenarios/kutno/config_25pct.xml --output output/r3_25pct --iterations 100

# 8. Walidacja eventów i wyniki
uv run python pipeline/check_events.py output/r3_25pct/output_events.xml.zst --expect-car-legs 12604   # 12 604 = wyniki D18 (bez K1-1, patrz R-1)
uv run python pipeline/queues.py ...   # przepełnione linki (D18), argumenty: patrz nagłówek skryptu
```

Baseline from D21 to R6 (replaces R4). Configs indicate plans and vehicles `plans_g5r6_*pct`, so the run does not require overrides. Background matrices (`scenarios/kutno/demand/background_od_r6b_*_gpr.csv`) are created in `pipeline/background_od.py`, boundary zones in `pipeline/border_zones.py`. After each estimation, run `pipeline/od_warnings.py`. Reference 25%: `output/g5r6_25pct_s{4711,1,2}` and plan seeds `g5r6p{1,2}_25pct_s4711` (`reports/etap2/g5_kalibracja/g5_r6_ref.md`). Steps 6–8 above describe the state from D18/R1.

Regression test (after every change in `matsim/`): `scenarios/smoke/config.xml` (10 agents, synthetic network), then `check_events.py --expect-car-legs 20`. Before the test, delete the old output.

Note: before regenerating the plans read chapter 13, point R-1 (`car_share` in `config/kutno.toml`). Without this, 25% of the plans will not match the reference results.

---

## 3. Data flow (pipeline)

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

Responsibility division: Python counts the data and plans, Java converts the network and runs the simulation. Each file is created in one place.

---

## 4. Data sources

Full list of limitations: `docs/ZRODLA.md`. Below is what influences the model.

| Source | What we get | Where in the model | limitations |
|---|---|---|---|
| GUS NSP 2021, population in regions and statistical districts `gus/ludnosc_rejony_obwody_nsp2021.xlsx` | 232 districts of Kutno: total population, age groups (pre/productive/post-productive). Total 42,255. | Distribution of employed persons on districts (D5, D17) | Lack of gender cross-section with age and lack of employment status. |
| GUS NSP 2021, labor market, TABLE 5 `gus/rynek_pracy_nsp2021_tablice.xlsx` | Employment indicators for cities in the Łódź voivodeship: production 0.739 (low variant: employed person / total) or 0.784 (baseline: without undetermined status, GUS method); post-production approx. 0.12 | Employed person estimate per district (D5), "baseline" variant | Only the voivodeship, not the commune. Estimation, not observation. Values: `scenarios/kutno/validation/f3_demand.json`. |
| GUS NSP 2021, employment flow matrix `gus/macierz_przeplywow_nsp2021.xlsx` | Inbound commuter to Kutno: 8,186 persons in 134 municipalities. Outbound: 2,669 in 83 municipalities. | Inbound and outbound @@N@@ (D3, D9, D17) | Only employed persons. Ignores flows < 3 people and background traffic within the municipality. The workplace is the employer's address (e.g., company headquarters in Warsaw). |
| BDL P4507 and P4508, 2024 `g2/bdl_kutno.json`, BDL API | P4507: employed person residents of the municipality (17 255). P4508: workplaces by payer headquarters (17 486). | Anchor of the number of employed persons in Kutno (D17/B) and variant C | ZUS/KRUS registers, counted by payer's headquarters. There is a 30% gap between P4507 + NSP and P4508 that cannot be explained (G2). |
| GUS BREC 2021, geometry (`brec/AreaStatisticalUnit_10_2021.zip`, `brec/SU_BREC_2021_REJ.zip`) | Municipal boundaries, county, region and district boundaries in EPSG:2180 | Area, districts, source municipalities (D9, D11) | Cities with county rights have district codes in BREC (we combine by county code). |
| OSM Geofabrik, `lodzkie-261015.osm.pbf` (data up to 2026-10-15) | Road network, buildings (tag `building`), landuse (`residential`, `industrial`, `commercial`, `retail`), tags `amenity`/`shop`/`office` | Network (chapter 5), buildings of homes and work (chapter 7) | Tag quality depends on volunteers. In the Kutno municipality, 72% of buildings have `building=yes` (without type), and `building:levels` is in this group only at 2% (blocks: 84%). |
| GBR Gdańsk 2022, Report 3a, Fig. 46 `gbr/GBR2022_raport3a.pdf` | Hourly schedule of "home-work" `config/departure_home_work_gbr2022.csv` commutes | Departure hours (D14) | Gdańsk Metropolis, not Kutno. Data read from the vector PDF chart. |
| GDDKiA GPR 2025 `g5/gpr2025/` | Average daily traffic on 19 segments in the network (A1, DK, DW), SDRR/SDRDR, share of light and heavy | Validation (G5), calibration goal | One value for the entire segment, without hours. No urban streets except DK. |
| GDDKiA SCPR 2025, station 14005 Lisica `g5/scpr2025/st_14005.pdf` | Weekday hourly curves (digitized) | Background traffic hourly profile (K3-2) | Station 13 km from Kutno, on DK60. Digitization from the graph. |
| GUS Mobility 2024 `gus_transport/mobilnosc_*` | Working from home Łódź 7.3%, share of car in trips for all purposes 60.1% | Presence at work (K1-1) | For all purposes, not for commuting to work. Only the voivodeship. |
| Bochnia 2016, Radom 2022 `g4/` | Share of car in commuting home-work: 61–67% | Vehicle share (K1-1) | Other cities, values from the charts. |
| BDOT10k district 1002, 2025-12-09 `g3/bdot10k/1002_GPKG.zip` | Residential buildings with number of floors (99.9% filled) | Not used in the model (G3 recommendation, open decision) | 39% of the geometry from the orthophoto map. |
| GUS statistical address points, NSP `g2/adr_kutno_2026_0.csv` | 4 807 address points of residential buildings in Kutno | Only control (G2, G3) | Nothing about entities and work. |
| GUS accessibility matrix `gus_transport/macierz_dostepnosci_20210331.xlsx` | Travel time by car between municipalities | Time control (G5), threshold D16 in minutes (unused) | GUS road model, without congestion. |
| GTFS collection.live Kutno, GTFS rail (Kuranowski) | Bus and train schedules | Beyond MVP (G4) | No license in the zbiorkom.live feed. Railway feed valid for 30 days. |
| VSP and MATSim MUM 2026 Literature (`g5/lit/`, `mum2026/`) | Reference configurations (matsim-berlin v6.3, matsim-kelheim v3.1), calibration practice | Justification `stuckTime` (D18) and dynamics `queue` | Other scales. They are not copied directly. |

Principle: numbers and parameters are taken only from sources `docs/ZRODLA.md` and `data/manifest.csv`. Assertions from auxiliary reports are checked in `docs/projekt/FACT_CHECK.md`.

---

## 5. Road network

### 5.1 Area

- Kutno Municipality (gm. miejska 1002011): total of 41 BREC districts, 33.55 km².
- Kutno county @@N@@ (1002): 117 districts, 885.6 km².
- Network area = county + **3 km buffer** (`network_buffer_m = 3000` in `config/kutno.toml`).
  ASSUMPTION: the buffer retains the entry roads outside the county so that inbound commuters from further municipalities have somewhere to enter. The width of the buffer outside the county is open (D-open).
- Coordinates: EPSG:2180, axis order **E, N** (x ≈ 525 000, y ≈ 485 000). Transformation from WGS84 is performed once in the Java converter.

### 5.2 Conversion from OSM

- Converter: `SupersonicOsmNetworkReader` (contrib `osm`, MATSim 2026.0), only `car` mode.
- Area filter: links whose nodes lie within the network area.
- `NetworkCleaner` usuwa węzły i linki nieosiągalne (F2: usunięto 116 węzłów i 127 linków).
- Border loops (correction F2, A1): when the A1 motorway is truncated, it remains with unidirectional lanes that end blindly at the border, and `NetworkCleaner` would remove them until the nearest node. Therefore, every node-exit (only entrances) we connect with the nearest node-source (only exits) within a radius of **300 m**. Links receive type `boundary_turnaround`, speed 30 km/h and capacity 5 000 veh/h (ASSUMPTION values). They operate only in the band of **1 km** from the border (`boundary_zone_m`).

Network result (F2): 4 453 nodes, 10 296 links, 4 426 km. The largest strongly connected component includes **100%** of the nodes. 90/90 test route pairs are reachable. No link has capacity, freespeed, length or lanes ≤ 0.

### 5.3 Speeds (D13)

Default Supersonic speeds (VSP values for German cities) yielded **15 km/h** on approx. 3,000 km of local roads, mainly rural. Therefore, the speeds are explicitly set in `config/network.properties`, in the following order:

1. OSM `maxspeed` (also `PL:urban`, `PL:rural` etc.) converted to km/h;
2. no tag → statutory limit according to road type (Road Traffic Law, art. 20): city 50, outside city 90, residential 50, living_street 20, motorway 140, trunk 100 (**ASSUMPTION**: trunk 100, because in PL it is usually GP or express road);
3. freespeed = allowed speed × 0,8 (ASSUMPTION: 0,8 is the practical VSP value, not calculated for Kutno).

"City" = urban municipality and cities in urban-rural municipalities with BREC `towns.wkt`. **ASSUMPTION**: villages with development are treated as urban roads (OSM does not have built-up area boundaries).

Control: the free time in the network is the median **0,76 × GUS time** (29 municipalities, `scenarios/kutno/validation/gus_vs_siec.csv`). The network is faster than ORS/GUS, so there is no indication that speeds are underestimated. ORS itself is also a model.

**Change D23 (2026-10-18, in progress):** one factor of 0.8 is replaced by factors per road group (A motorway, B DK/DW outside city, C tertiary/unclassified outside city, D residential outside city, E main inside city, F local inside city), matched to TomTom times (D22, variant A: metrics only in repo). Values after calibration are in `reports/etap2/g5_predkosci_d23/`. Validation of D22 showed free-flow speeds approx. 15% lower than TomTom on A1, DK and DW; times for 48–77% of routes fall within the TAG M3.1 criterion.

### 5.4 Throughput and dynamics (uncalibrated)

- Capacity and number of lanes: default Supersonic values (e.g., tertiary 600 veh./h/lane, primary 1 500 veh./h/lane). They are not calibrated and do not have a local source. Half of the delays are on tertiary streets `reports/etap2/g6_kolejki/g6_kolejki.md`.
- Intersections: lack of signaling and priority. Throughput is only a link property (G1, delayed).
- Queue dynamics: `trafficDynamics = queue`. kinematicWaves (like Berlin, Kelheim) gave +56% delays, and with 300 s stuckTime gridlock (D18, G5 K5).
- At `qsim.stuckTime = 30 s` (D18). At 10 s and `removeStuckVehicles=false` QSim pushed vehicles onto full short links (82 vehicles on a capacity of 1.2). After the change: overloaded links 13 $\rightarrow$ 4–7.

### 5.5 Activity attachment to the network

- Activities are pinned to the **nearest link** based on distance to its segment. Types skipped: `motorway`, `motorway_link`, `trunk`, `trunk_link`, `boundary_turnaround` (`snap_exclude_types`). Without this, MATSim would pin the home to road A1 (R3/E5).
- Exception: entries and exits at the border retain their link.

---

## 6. Demand: who is commuting and from where

### 6.1 Balance at 100% (baseline variant B, D17)

| Component | Number | From | Notes |
|---|---|---|---|
| Employed persons in Kutno | **14 586** | P4507 2024 (17 255) minus outbound commuter NSP (2 669) | Baseline (B). Distribution by districts as in estimation D5. |
| Inbound commuter to work in Kutno | **8 139** | NSP matrix (8 186) after cutting municipalities > 100 km (D16) | 47 people from municipalities outside the county were cut off. |
| Total employment places in Kutno | **22 725** | sum of the two above | Variant C (sensitivity): 17 486 (BDL P4508), scaled by one factor. |
| Outbound commuter from Kutno in the model | **2 481** | NSP matrix minus 188 people from municipalities > 100 km | Variant O1 (D17) |

For comparison, the estimation D5 (NSP indicators × district age structure) yielded 20,215 employed residents, which is 17% more than P4507. D5 was replaced by B in D17. **Remains as distribution across districts** (`employed_base`).

What we know and what we don't: the identity "workplace = residents staying + inbound commuters" is not closed. Registers give 22,725, while P4508 gives 17,486. The 30% difference has no explanation in the data (G2, `docs/research/G2_warianty.md`). Therefore, C is a sensitivity variant, not an error.

### 6.2 Residents employed person in Kutno (`kind = resident`)

1. Number of employed persons: P4507 (17 255) $\times$ municipality share. Outbound commuters (2 669) are subtracted.
2. Distribution across **232 statistical districts** proportionally to `employed_base` (estimation by age, D5).
3. At a scale of 25%, the number of agents in the district = result $\times$ vehicle share $\times$ presence (K1-1) $\times$ sample, rounded using the largest remainder method so that the sum equals `round(sample × całość)`.

ASSUMPTION (D5): we apply employment indicators from tables for the cities of the Łódź voivodeship (production and post-production, GUS method) to age groups in the district. The population table does not cross gender with age, so we do not know if the gender structure changes the result.

### 6.3 Inbound commuter to work in Kutno (`kind = commuter`)

- Number and source municipalities: NSP 2021 matrix (134 municipalities, 8,186 persons).
- Municipalities in the Kutno county (D9): home is a random residential building from OSM in the source municipality (weighted by area). Start at the entrance to Kutno at the time from the profile (chapter 9).
- Municipalities outside the county (D16/A): agent appears at the nearest **border entrance** to the municipality's centroid, at the time from the profile. Commute time outside the network is not added (**ASSUMPTION**: as D16/A; previously 72 km/h × 1.3 was added, resulting in starts after midnight).
- Cut > 100 km (D16/B, ASSUMPTION): municipalities whose centroid is further than **100 km** from the nearest entrance are omitted. This includes 12 municipalities (47 people in 100%), including Szczecin, Gdańsk, Kraków, Wrocław, Poznań. Warsaw (approx. 89 km from the entrance) remains: 27 inbound commuters and 457 outbound commuters in the NSP matrix. The threshold `max_border_km` is in `config/kutno.toml`.
- Inflows: 31 links of types `motorway`, `trunk`, `primary`, `secondary` in the zone 1 km from the border, directed to Kutno (ASSUMPTION, `entry_road_types`, `entry_zone_m`).

### 6.4 Outbound commuter from Kutno (`kind = outbound`, D17/O1)

- Number and target municipalities: NSP matrix (83 municipalities, 2,669 people).
- House: random residential building in the Kutno district, weighted by employed persons (as residents).
- Work: in the county's municipalities, random workplace in the target municipality. Municipalities outside the county: **outbound** (exit link closest to the municipality's centroid, mirror of entrances).
- Departure time from profile, work 8 h. After work returns at the same time, without commute time outside the network (ASSUMPTION).

Why O1: traffic exists and loads the same inlets as inbound commuters, but in the opposite direction. Without it, the outlet flows would be underestimated (G2).

### 6.5 Vehicle share and presence at work (K1-1, D19)

- All categories (residents, inbound commuter, outbound commuter) are multiplied by:
  - vehicle share 0,64 (middle of the range 61–67% from Bochnia and Radom; `car_share`);
  - **1 − 0,073** (working exclusively from home, Łódź according to GUS Mobility 2024; `work_from_home`).
  - **× 0.593**
- Result: plans drop by 25% from 6,302 to 3,739 persons.
- Methodological note: the reduction acts on the count in each group (district, commune), not by randomly omitting specific individuals. Residents in districts with a low share of cars are not distinguished.
- **Status:** scope change of the MVP ("everyone drives", D6) and requires decision confirmation. Values come from other cities (**ASSUMPTION**).

### 6.6 Sample and scale

- Scope: 10%, 25%, 100%. Results are reported from **25%, 3 seeds** (D15, user decision). 100% only upon explicit request.
- Seed: 4711 (default in the config), 1, 2.
- Throughput scaled to sample: `flowCapacityFactor = storageCapacityFactor = sampleSize` (MATSim 2026 requires their equality, D8, D15/5).
- Results at 100% reproduction are achieved by `× 1/sampleSize` (applies to intensities and GEH; `convergence.py` does it automatically).

---

## 7. Locations: where are the homes and workplaces from

All locations are **buildings from OSM** (the same PBF as the network), randomly selected with weight based on **building footprint area** (D7, D11). The random selection is done with replacement, and the seed is in the config (`seed = 4711`).

### 7.1 Building filters

Residential (`residential_buildings`, ASSUMPTION D11): `house`, `detached`, `apartments`, `residential`, `semidetached_house`, `terrace`, `bungalow`, `farm`, `dormitory`, as well as `building=yes` within landuse `residential`, without tags `amenity`/`shop`/`office`.

**Employment** (`work_buildings`, ASSUMPTION D7): `retail`, `industrial`, `warehouse`, `office`, `commercial`, `school`, `hospital`, `public`, `civic`, `government`, `kindergarten`, `university`, `college`, `supermarket`, `service`, `fire_station`, `train_station`, `transportation`, `manufacture`, `factory`, `hotel`, as well as every building with tag `amenity`/`shop`/`office` and `building=yes` in landuse `industrial`, `commercial`, `retail`. Only within the boundaries of Kutno municipality (for agents from Kutno).

Exclusions from OSM data:
- `building=no` traktujemy jak brak budynku (plac komisu z `shop=car`, 3,6 ha, był największym „miejscem pracy”, R3/błąd 1).
- Residential building cannot be a work building `loc[work, residential] = False`.

### 7.2 Houses

- Residents: residential building in the statistical district, randomly weighted by area. District without a residential building → **random point** in the district (D11). There is 100% one such district, `6509902`, with 6 people (in 10%). We do not know if this is lack of development or lack of data in OSM (to be checked in QGIS).
- Inbound commuter from the county: random residential building in the source municipality (geometry from BREC areas).
- Inbound commuter from outside the district and outbound commuter from outside the district: do not have a home in Kutno. Start/end on the border link.
- Only 26,611 residential buildings in the network area.

Alternative (unaccepted): buildings from BDOT10k with the number of floors (weight "outline × floors"). Analysis G3 showed a better fit to the GUS 250 m grid (error 8.5 pp compared to 9.4–10.3 pp currently, depending on the comparison variant; `docs/research/G3_domy.md`). The decision is open (chapter 13).

### 7.3 Employment locations

- Random selection with **area weight** from the list of workplaces in the Kutno municipality. Candidates: 1 103, 473 buildings were selected in 10% (F4).
- Top 5 buildings receive 13% of agents (large halls in the eastern zone). These are real objects (`industrial` and `warehouse`, 1.6–3.1 ha), verified during the pre-run check (D16).
- ASSUMPTION: employment distribution within the municipality is reflected by building area. There are no REGON or facility addresses in the model (D7, G2 open).

### 7.4 Link assignment

Each house and workplace gets the **nearest link** in the network (excluding types from `snap_exclude_types`, section 5.5). Inbound and outbound commuters from outside the county have a border link immediately.

---

## 8. Agent characteristics: what we know about the person

Agents are created from **aggregates**, not from microdata. We do not reproduce households or individuals (project rules).

| Attribute | Value | From |
|---|---|---|
| `subpopulation` | `person` (wymagane przez SimWrapper) | constant |
| `kind` | `resident` / `commuter` / `outbound` | type of demand (6.2–6.4) |
| `id` | `r<obwód>_<n>`, `c<gmina>_<n>`, `o<gmina>_<n>` | unique (test in `plans.py`) |
| home | OSM building and link | Chapter 7.2 |
| work | OSM building and link | Chapter 7.3 |
| departure time | from the GBR profile (chapter 9) | randomized from the range |

What agents DO NOT have: age, gender, education, profession, income, car ownership, number of people in the household. Employment indicators by age only affect the **distribution across districts** (district weight), not the attributes of individuals. There is also no consistency check (e.g., a person with a low employment indicator in a district works the same as another).

---

## 9. Daily plans: chain and hours

(each person): `home (end_time = wyjazd) → car → work (max_dur = 8:00:00) → car → home`. Test: three activities and two car legs, `end_time` XOR `max_dur` (design rules).

Departure time (D14):
1. Sampling of the hourly interval from the "home–work" distribution GBR Gdańsk 2022, Fig. 46 (`config/departure_home_work_gbr2022.csv`, 18 intervals after normalization to 100%). The 20–24 h interval is one 4-hour interval.
2. Time is uniformly randomized in the range (**ASSUMPTION**).
3. Outbound from home = this hour. Inbound commuter from the border: time of entry at the border.

Time limitations:
- The distribution is from the Gdańsk metropolis (**ASSUMPTION**, that fits Kutno).
- Lack of hourly local schedule (decision D10 open, R1: `docs/research/R1_godziny.md`).
- Start no later than 23:52.

8 h working time (`work_max_dur`): **ASSUMPTION** rounded from GUS BCL 2013 (average of 8 h 11 min for hired workers). This is not a distribution per agent. `TimeAllocationMutator` **disabled** (hours from data should not drift).

Simulation end: `qsim.endTime = 48:00:00` (reserve; 36:00 interrupted the agent from Kraków, `stuckAndAbort`, R3).

---

## 10. MATSim simulation (configuration)

Files: `scenarios/kutno/config_{10,25,100}pct.xml`. Paths are relative to the configuration. `controller.outputDirectory` is relative to the working directory, so run from the project directory.

| Parameter | Value | Justification |
|---|---|---|
| MATSim | 2026.0, Java 25 | `matsim/` (matsim-example-project @ 74d23af) |
| `lastIteration` | 100 | D15/3 (maximum 100 iterations) |
| `flowCapacityFactor` = `storageCapacityFactor` | = sampleSize (0.25 for 25%) | D8, MATSim 2026 requires equality |
| `stuckTime` | 30 s | D18 |
| `trafficDynamics` | `queue` | D18, G5 K5 |
| `endTime` | 48:00:00 | Chapter 9 |
| `randomSeed` | 4711 (1, 2 for variance) | config |
| `coordinateSystem` | EPSG:2180 | project principles (D-spec) |
| `numberOfThreads` | 8 in the configuration; runs with 4 or 2 threads | the number of threads does not shorten the run, 4 and 8 give identical results |
| Strategies | `ChangeExpBeta` 0,8, `ReRoute` 0,2 | `subpopulation = person` |
| `fractionOfIterationsToDisableInnovation` | 0,8 | after 80 iterations only the plan selection (the score flattens by definition) |
| Scoring | default MATSim; `home` typical 16 h, `work` typical 8 h | ASSUMPTION, diagnostic score only, calibration outside of MVP |
| MATSim, linkStats | enabled; linkStats every 10 it. (average of 5) | R3/E2, convergence diagnostics |

What is in the output: `output_events.xml.zst` (events, format `.zst`), `output_links.csv.zst`, `modestats`, `scorestats`, `traveldistancestats` (MATSim). Charts: `pipeline/plot_run.py`.

What MATSim does with legs: in `car` mode, MATSim automatically attaches teleported legs `walk` (arrival and departure). They are not part of the traffic model, but must be filtered out when counting legs.

---

## 11. Validation and results

### 11.1 Tests

| Test | Script | What it checks |
|---|---|---|
| Events | `pipeline/check_events.py` | `departure = arrival`, 0 `stuck` (also `stuckAndAbort`), number of car legs = number in plans |
| Plans | `pipeline/validate_plans.py` | chain, area, employment in the Kutno municipality, number of people, sha256 repeatability |
| Network | `pipeline/validate_network.py` | area, SCC, attributes, test routes |
| Demand | `pipeline/demand.py` (asercje) | population sum 42 255, 8 186 inbound commuters, merging 232/232 |
| Link overflow | `pipeline/queues.py` | `overfilled_links_gt2x` (D18) |
| Convergence | `pipeline/convergence.py` | change of intensities for top-50 links, GEH between seeds (scale 100%) |
| Model vs GPR | `pipeline/g5_baseline.py` | GPR on 19 segments (A1, DK, DW) |

Project principle: A run without errors is not proof. The semantic test counts the stage.

### 11.2 D18 results (25%, 3 seeds; historical, without background traffic)

Source: `reports/etap2/g6_kolejki/d18_25pct/`, `reports/etap2/g6_kolejki/g6_kolejki.md`.

| Indicator | Value |
|---|---|
| feet car | 12 604 (consistent with plans), 0 stuck |
| total delay, 3 seeds [sample-hours] | 735–854 |
| overloaded links 06–09 | 4–7 |
| GEH < 5 in the peak of 7–8 (between seeds) | 98,8–100% |
| median travel time s4711: residents / inbound commuter / outbound commuter | 15.0 / 23.5 / 24.1 min |
| largest bottleneck | DK92 Sklęczkowska (narrowing 2 → 1 lane). In the diagnosis of variant B (the same demand) 44% of delays are due to the queue behind this narrowing, and 51% to tertiary streets with a capacity of 600 veh./h/lane |

This is the starting point for calibration, not a calibrated result. For reference: R1 (with K1-1, 25%, 3 seeds) yields 7,478 car trips and delays of 106–113 veh-h. This indicates strong nonlinearity of congestion with respect to demand.

### 11.3 Validation against GPR 2025 (G5, R1; historical)

| Link group | Model (D18) / GPR | Model (R1, K1-1) / GPR |
|---|---|---|
| A1 (3 segments) | 7% | 3% |
| DK in Kutno (Objazdowa, Bitwy pod Kutnem, Sklęczkowska) | 56% | 30% |
| other DKs | 16% | 8% |
| Driving Way | 7% | 4% |

Gap is expected: the model without background traffic lacks transit, local traffic other than commuting, and freight/heavy goods traffic. Therefore, after K1-1, the intensity in the city decreases instead of increasing. The background filled this gap in D19–D21 (chapter 11.4).

### 11.4 Baseline R6 after audit G5 (D19–D21), state 2026-10-18

Source: `reports/etap2/g5_kalibracja/g5_r6_ref.md`. 25%, 100 iterations, 5 runs (3 seedy MATSim + 2 seedy plans). Commuting × 0.593 (K1-1), light background traffic with delivery vehicles (pce 1.0) and heavy (pce 2.5, 80 km/h, `linkDynamics=PassingQ`, D20), boundary zones per road with GPR weight, ends of heavy traffic in work buildings (D21).

| Indicator (median of 5 runs, min–max.) | light | heavy |
|---|---|---|
| A1 (3 sections), model / GPR | 99% (98–99%) | 101% (99–101%) |
| DK in Kutno (3 sections) | 105% (104–113%) | 68% (67–71%) |
| other @@N@@ DK | 82% (80–90%) | 83% (76–83%) |
| Driving Way | 60% (60–63%) | 75% (74–83%) |
| segments in $\pm$15% (with 15 matching) | 12/15 (11–13) | 12/15 (12–15) |

- Segments 91124 (Objazdowa) and 91866 (Bitwy pod Kutnem) are control segments (used in variant selection), not independent validation.
- Dispersion: randomizing the plans and O-D estimation points gives 20–100 times greater dispersion than MATSim seeds (median 9–12% per link versus 0.1–0.4%). Variant differences smaller than approx. 20 pp on a single link are not significant.
- Daily delay: 239–243 sample-hours (MATSim seed), 243–298 (plan seeds). 0 saturated links.
- Validation of times against TomTom (D22): the model is calibrated in demand, not validated regarding times (`reports/etap2/g5_czasy_tomtom/g5_czasy_tomtom.md`).

---

## 12. Assumptions (summary table)

Each ASSUMPTION has a value, location in the code or config, justification and status.

| ID | ASSUMPTION | Value | Where | Justification / status |
|---|---|---|---|---|
| A-1 | Network scope = district + buffer | 3 000 m | `config/kutno.toml` `network_buffer_m` | D9, for verification in F2 (open: width outside the county) |
| A-2 | Turns at the border | 300 m, 30 km/h, capacity 5 000, zone 1 km | `config/network.properties` | F2 (A1), D9 |
| A-3 | Speed = limit × 0,8 | factor 0,8 | `config/network.properties` | VSP practice, not calculated for Kutno |
| A-4 | Villages as local roads | rural @@N@@ 90 | `config/network.properties` | lack of built-up area boundaries in OSM |
| A-5 | Trunk = 100 km/h | trunk 100 | `config/network.properties` | GP or expressway, for confirmation |
| A-6 | Default capacity Supersonic | tertiary 600, primary 1 500 veh./h/pax | MATSim | uncalibrated, lack of local source (G1, G5 K5) |
| A-7 | Employed person residents | P4507 2024 = 17 255 | `config/kutno.toml` `employed_residents_reg` | D17/B, register |
| A-8 | Variant of the number of jobs | B (baseline), C = 17 486 | `config/kutno.toml` `jobs_total` | D17, 30% unexplained gap |
| A-9 | Outbound commuter in the model | O1, anchor year 2024 | `plans.py`, `demand.py` | stage D17, stage G2 |
| A-10 | Employment indicators | production 0,784 (baseline), post-production according to TABL. 5 | `demand.py` (rozkład obwodów) | D5, only the voivodeship |
| A-11 | Range 0–17 for the pre-production group | voivodeship indicator | `demand.py` | D5 |
| A-12 | Cutting municipalities @@N@@ > 100 km from the entrance | 100 km | `config/kutno.toml` `max_border_km` | D16/B, user decision |
| A-13 | Inbound commuter from the border | hour from the profile, without commute | `plans.py` | D16/A |
| A-14 | Entry: link type | motorway, trunk, primary, secondary; 1 km zone | `config/kutno.toml` `entry_road_types`, `entry_zone_m` | D9 |
| A-15 | Inbound commuter from the district | random building in the source municipality | `plans.py` | D9 |
| A-16 | Residential and employment buildings (type lists) | Chapter 7.1 | `config/kutno.toml` | D7, D11 |
| A-17 | Building weights = footprint area | m² | `plans.py` | D7, D11; alternative BDOT × floors not accepted (G3) |
| A-18 | District without buildings $\rightarrow$ random point | — | `plans.py` | D11, concerns district 6509902 |
| A-19 | Car share home–work | 0,64 (61–67%) | `config/kutno.toml` `car_share` | D19/K1-1, Bochnia 2016, Radom 2022 |
| A-20 | Working from home | 7,3% | `config/kutno.toml` `work_from_home` | GUS Mobility 2024, table 1 |
| A-21 | Departure profile | GBR Gdańsk 2022 | `config/departure_home_work_gbr2022.csv` | D14, metropolis, not Kutno |
| A-22 | Hour uniformly in the interval | — | `plans.py` | ASSUMPTION D14 |
| A-23 | Working time 8 h | 08:00:00 | `config/kutno.toml` `work_max_dur` | GUS BCL 2013, rounded |
| A-24 | Missing TimeAllocationMutator | — | config | hours from data |
| A-25 | Scoring: typical duration home 16 h, work 8 h | — | `config_*.xml` | default MATSim, diagnostic score |
| A-26 | Sampling and rounding | 25% (results), method of largest residuals | `plans.py` | D15/3, D8 |
| A-27 | seed | 4711, 1, 2 | config, `output/r3_runs.sh` | D15 |
| A-28 | `stuckTime` | 30 s | config | D18, Berlin/Kelheim |
| A-29 | Dynamics `queue` | — | config | D18, G5 K5 |
| A-30 | Background traffic from O-D estimation (light + freight, heavy) | 20 points for the municipality, $\tau$ = 30 min, entry weight = capacity | `pipeline/background_od.py` | D19–D21; calibration estimated to GPR, spread depends on the point seed |
| A-31 | No pedestrians, cyclists and PT; heavy only as background traffic (pce 2.5, 80 km/h) | — | — | D6, D20, G4 |
| A-32 | Delays on the link, not at the intersection | — | — | G1 postponed |
| A-33 | Working day | — | — | typical working day (GUS, GBR) |

---

## 13. Limitations, known problems and gaps

### 13.1 Configuration consistency (requires decision or correction before the next run)

- R-1: `car_share` and `work_from_home` are enabled by default in `config/kutno.toml` (D19/K1-1, decision: remains). Reference results D16, D17/B and D18 (`reports/etap2/g6_kolejki/d18_25pct/`) use plans **without K1-1**: `scenarios/kutno/plans_25pct.xml.gz` (6 302 persons), which `config_25pct.xml` reads as input. The default `plans.py ... 0.25` yields 3 739 persons today (K1-1), so without parameters it does not reproduce the reference. Plans without K1-1 have a separate name `scenarios/kutno/plans_25pct_bez_k1.xml.gz`. They were generated using the command with the parameters below, sha256 identical to `plans_25pct.xml.gz` (`1be78c27…027`), 6 302 persons (3 647 / 2 041 / 614). Plans K1-1 for R1 are in `plans_g5r1_25pct.xml.gz`.
- R-2: default files `scenarios/kutno/plans.xml.gz`, `config_10pct.xml` and `config_100pct.xml` originate from stage F5/F6 (`inputPlansFile = plans.xml.gz`). It is not certain which state `kutno.toml` they were created from. They are not described in `docs/projekt/PROGRESS.md`. **Proposal:** remove from the default configuration or describe in `reports/README.md`.
- R-3: `output/r3_runs.sh` (script launching seeds in parallel) is in `output/`, that is in `.gitignore`. It is not versioned. The Build `CreateKutnoNetwork` also does not have the script in the repo (chapter 2 provides the command from Javadoc).
- R-4: the comment in `config_25pct.xml` mentions 8 threads, while the reference runs used 4 (without affecting results, but for improvement).

### 13.2 Data limitations and methods

- NSP matrix: only employed persons, without flows < 3 people and without intra-municipal traffic. Lower bound of outflow and inflow (underestimates traffic).
- Workplace in the matrix = employer address (headquarters). Distant relationships (Warsaw 457) may be a result of the company's headquarters, not actual commute.
- Employment indicators only at the voivodeship level. Estimation D5 is 17% higher than the register.
- Employed person per district (232) is an estimation, not an observation (D5).
- OSM data: 72% of the municipality's buildings have `building=yes` without type, and only 2% in them is `building:levels`. Weights (outline area) are therefore approximate.
- 1 450 buildings in OSM in Kutno have no counterpart in BDOT10k (G3).
- The number of employed persons is not assigned to age or gender.

### 13.3 Limitations of the model

- No signals, intersections, or turning restrictions. Queues are the result of link capacity and `stuckTime`, not intersection conflicts.
- No time during commute outside the network: inbound and outbound commuters "teleport" at the border (ASSUMPTION, D16/A).
- One typical working day, without weekends and holidays.
- No random variability in working time per agent (fixed 8 h).
- Default scoring: route selection is true, but the score is not calibrated and is not used for inferences.
- Non-linearly sensitive results to demand (C vs B: delays -71% at -22% demand). The number of jobs is the most sensitive parameter.

---

## 14. Gaps: what is still missing

Status as of 2026-10-20. The full list of open issues is in `docs/projekt/ROADMAP.md` (chapter 3 and 4).

| # | gap | Status | Where described |
|---|---|---|---|
| stage 1 | Background traffic and transit: implemented in D19–D21 (O-D estimation from GPR, light, delivery and heavy, baseline R6). Open: balance of DK91/DK92 east districts, local counters. | partially closed | `reports/etap2/g5_kalibracja/g5_r6.md`, `docs/projekt/ROADMAP.md` §3 |
| L-2 | K1-1 vehicle participation (MVP narrowing "all cars"): accepted in D19, source from other cities, no local data. | decision made, data weak | `docs/research/G5_plan_kalibracji.md` |
| L-3 | Modal split (G4): PT, pedestrian, bicycle absent. No source for commuting to work in Kutno. | open | `docs/research/G4_tryby.md` |
| L-4 | Distribution within the municipality of workplaces: weights according to building area. REGON, NACE and facility addresses not used (G2). | open | `docs/research/G2_miejsca_pracy.md` |
| L-5 | Building weights (BDOT × floors vs outline): G3 recommendation without decision. | user decision | `docs/research/G3_domy.md` |
| L-6 | Departure times from local source (D10): today GBR Gdańsk, background profile Lisica. | research | `docs/research/R1_godziny.md` |
| L-7 | 8 h working time: constant ASSUMPTION, without schedule per agent. | research | `docs/research/R1_godziny.md` |
| L-8 | Urban street and intersection capacity (A-6, G1): no data. Municipal measurements (UM, ZDP, GDDKiA Kutno Region) to be obtained. | waiting for data | G1 `docs/projekt/TASKS.md` |
| L-9 | Trucks and PCE: pce 2.5 and 80 km/h (D20), source WR-D-13-01. Closed in D20. | closed | `reports/etap2/g5_kalibracja/g5_czasy_pce.md` |
| L-10 | Configuration reconstruction (R-1, R-2, R-3): one script replaying all runs and files. | to be done | — |
| L-11 | Network speeds (D23) and re-validation of TomTom times (D22, variant A). | in progress | `reports/etap2/g5_predkosci_d23/`, `docs/projekt/ROADMAP.md` §4 |
| L-12 | Blender visualization (G6): videos locally, outside of git. Does not affect the model. | description in `docs/research/G6_blender.md` | `blender/` |

Open questions from `docs/projekt/DECISIONS.md`, without decisions: buffer width outside the county, scoring parameters, car share (D6), REGON (D7).

---

## 15. Project structure

| Path | Contents | in the git |
|---|---|---|
| `docs/projekt/DECISIONS.md` | decisions D1–D23 (change = new entry) | yes |
| `docs/projekt/FACT_CHECK.md` | verified facts from AI reports | yes |
| `docs/projekt/TASKS.md` | stages F0–F6 and stage 2 (G1–G7) | yes |
| `docs/projekt/PROGRESS.md` | what was included, with proof | yes |
| `docs/projekt/ERRORS.md` | errors and rules | yes |
| `config/` | `kutno.toml`, `network.properties`, time profile | yes |
| `data/manifest.csv` | URL, data, bytes and SHA-256 of each download | yes |
| `data/raw/` | downloaded sources (read-only) | no |
| `pipeline/` | Python scripts (data, plans, analysis, validation) | yes |
| `matsim/` | Java project (`CreateKutnoNetwork`, `mvnw`) | yes |
| `scenarios/smoke/` | regression test, 10 agents | yes |
| `scenarios/kutno/` | network, plans, configs, demand CSV (`plans_*.xml.gz` excluded from git) | partially |
| `reports/` | reports and evidence per stage (`reports/README.md`) | yes |
| `docs/research/` | analysis of G2–G6 and methodological background | yes |
| `docs/ZRODLA.md` | source catalog | yes |
| `output/` | MATSim runs | no |
| `blender/` | G6 visualization | yes |

Reference results (current): baseline R6, `reports/etap2/g5_kalibracja/g5_r6_ref.md` (25%, 3 seedy MATSim + 2 seedy plans). Results D18 (`reports/etap2/g6_kolejki/d18_25pct/`) are historical.

---

## 16. Glossary

| Abbreviation | Significance |
|---|---|
| BDL | GUS Local Database. P4507 = employed person residents, P4508 = employed persons by payer seat |
| BDOT10k | Topographical Object Database (buildings, floors) |
| BREC | Baseline of Registry of Characteristics (areas and statistical districts of NSP 2021) |
| CRS EPSG:2180 | PUWG 1992 layout, E, N axes |
| D1–D23 | design decisions (`docs/projekt/DECISIONS.md`) |
| GEH | Concentration agreement measure (< 5 = good agreement) |
| GPR | General Traffic Measurement of the General Directorate for National Roads and Motorways (SDRR, SDRDR, SDRL) |
| GBR | Gdańsk Development Office, Report 3a (mobility study, hourly profile) |
| GTFS | public transport timetable (format) |
| K1-K5, G1-G7 | calibration steps (`G5_plan_kalibracji.md`) and project stages (`docs/projekt/TASKS.md`) |
| Minimum Viable Product | scope: car, home–work–home |
| NSP 2021 | National Census @@N@@ 2021 |
| Origin-Destination | trip matrix (origin-destination) |
| Peak Congestion Effect | passenger car equivalent factor (truck) |
| QSim | MATSim queueing simulation engine |
| SCPR | Continuous Traffic Measurement Stations (GDDKiA) |
| SDRDR | average daily traffic on weekdays (GPR) |
| TERC | territorial unit identifier (1002011 = municipality of Kutno) |
| TABLE 5 | GUS table "Population in the labor market" (employment indicators) |

## 17. License

- Code (`pipeline/`, `matsim/src/`, `blender/`, scripts in `reports/` and `docs/`): GPL-3.0-or-later, file [LICENSE](LICENSE).
- Data and results from GUS: CC BY 4.0 (source required: Główny Urząd Statystyczny).
- Data from OpenStreetMap: ODbL 1.0 (© OpenStreetMap contributors). Extracted bases from OSM data are published under ODbL.
- Example MATSim project in `matsim/`: GPL-2.0-or-later, file `matsim/LICENSE`.
- Full division and reservations: [LICENSE-DATA.md](LICENSE-DATA.md).
