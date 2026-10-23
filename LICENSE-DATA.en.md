# Data and results licenses

> Machine translation of [LICENSE-DATA.md](LICENSE-DATA.md) (Polish). The Polish text is binding; this translation is for reference only.

The MATSim Kutno repository has two licenses. The code is under GPL-3.0-or-later (file `LICENSE`). Data, results, and reports have the licenses described below.

## Code (GPL-3.0-or-later)

Relates to the code in `pipeline/`, `matsim/src/`, `blender/`, `docs/research/G4_beeline/` and scripts in `reports/`. Full text: [LICENSE](LICENSE).

The example MATSim project in `matsim/` has its own GPL-2.0-or-later license (`matsim/LICENSE`). GPL-3.0-or-later is compatible with it.

## Data outputs from GUS (CC BY 4.0)

Relates to data extracted from GUS publications: NSP 2021 tables, BDL (P4507, P4508, TABL. 5), commuting matrices, BREC 2021 geometry, and district tables. The source data author is the Central Statistical Office.

Results from these data (plans, population, matrices, tables, charts) are under the **Creative Commons Attribution 4.0 (CC BY 4.0)** license. Source attribution is required: "Central Statistical Office" and publication name.

## Data from OpenStreetMap (ODbL 1.0)

Relates to the road network, buildings and land use extracted from OSM. Source: © OpenStreetMap contributors. Data from OSM is under the **Open Database License 1.0 (ODbL)** license.

According to ODbL, every public, derived database containing data from OSM must be made available under the same license (ODbL) with attribution. This applies, among others, to `scenarios/kutno/network*.xml.gz` and OSM files in `scenarios/kutno/osm/`, if they are published.

## Data that must not be published

Data from TomTom (variant A, D22) and other commercial APIs are not in the repository. Exception is aggregated metrics and reports. They are not under CC BY or ODbL license.

Data from Senozon AG (proprietary license) are not used in this project.

## Sources

Each source has a description, status, and license in [docs/ZRODLA.en.md](docs/ZRODLA.en.md) (English) and [docs/ZRODLA.md](docs/ZRODLA.md) (Polish).
