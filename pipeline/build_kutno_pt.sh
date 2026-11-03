#!/bin/sh
# Odtworzenie scenarios/kutno_pt/ (G4/krok 5, część techniczna). Uruchom z korzenia repo (Git Bash).
# Wymaga: uber-jar matsim/, scenarios/kutno/network.xml.gz (gitignored), data/raw/gtfs/kutno.zip, data/raw/g4/polish_trains.zip.
# Zmienne: ROOT (katalog z data/raw, scenarios/kutno i jarem; domyślnie .), JAR, TMP.
set -e
ROOT=${ROOT:-.}; TMP=${TMP:-$(mktemp -d)}
JAR=${JAR:-$ROOT/matsim/matsim-example-project-0.0.1-SNAPSHOT.jar}
DAY=2026-10-20   # ZAŁOŻENIE: wtorek, mieści się w ważności obu feedów
uv run python pipeline/pt_filter_gtfs.py "$ROOT/data/raw/g4/polish_trains.zip" "$TMP/rail_kutno.zip" --day 20261020 --area "$ROOT/scenarios/kutno/area/network_area.wkt"
mkdir -p "$TMP/out"
java -Xmx4g -cp "$JAR" org.matsim.application.prepare.pt.CreateTransitScheduleFromGtfs \
  "$ROOT/data/raw/gtfs/kutno.zip" "$TMP/rail_kutno.zip" --prefix mzk_,kol_ --date $DAY \
  --network "$ROOT/scenarios/kutno/network.xml.gz" --target-crs EPSG:2180 --name kutno_pt \
  --output "$TMP/out" --pseudo-network singleLinkBetweenStops
mkdir -p scenarios/kutno_pt
mv "$TMP/out/kutno_pt-transitSchedule.xml.gz" scenarios/kutno_pt/transitSchedule.xml.gz
mv "$TMP/out/kutno_pt-transitVehicles.xml.gz" scenarios/kutno_pt/transitVehicles.xml.gz
mv "$TMP/out/network-with-pt.xml.gz" scenarios/kutno_pt/network_pt.xml.gz
