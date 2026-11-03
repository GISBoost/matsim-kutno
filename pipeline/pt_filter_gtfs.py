"""Filtr GTFS kolei (polish_trains.zip) do dnia typowego i bbox sieci Kutna.

Zostają kursy aktywne w DAY (calendar_dates, exception_type=1) z >=2 przystankami w bbox
sieci (EPSG:2180, network_area.wkt). Kurs jest przycinany do ciągłego odcinka od pierwszego
do ostatniego przystanku w bbox (konwerter MATSim i tak buduje pseudo-sieć tylko z tych przystanków).
Wynik: osobny zip (bez shapes), np. w katalogu tymczasowym. data/raw nie jest modyfikowane.
"""
import argparse, zipfile
import pandas as pd
from pyproj import Transformer
from shapely import wkt

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--day", default="20261020")
ap.add_argument("--area", default="scenarios/kutno/area/network_area.wkt")
a = ap.parse_args()

minx, miny, maxx, maxy = wkt.loads(open(a.area).read()).bounds
z = zipfile.ZipFile(a.src)
rd = lambda n, **k: pd.read_csv(z.open(n), dtype=str, keep_default_na=False, **k)

cd = rd("calendar_dates.txt")
svc = set(cd[(cd.date == a.day) & (cd.exception_type == "1")].service_id)
trips = rd("trips.txt")
trips = trips[trips.service_id.isin(svc)]
stops = rd("stops.txt")
x, y = Transformer.from_crs(4326, 2180, always_xy=True).transform(
    stops.stop_lon.astype(float).values, stops.stop_lat.astype(float).values)
stops["inb"] = (x >= minx) & (x <= maxx) & (y >= miny) & (y <= maxy)  # x=E, y=N
inb = set(stops[stops.inb].stop_id)

st = rd("stop_times.txt")
st = st[st.trip_id.isin(set(trips.trip_id))].copy()
st["seq"] = st.stop_sequence.astype(int)
st = st.sort_values(["trip_id", "seq"])
st["inb"] = st.stop_id.isin(inb)
g = st[st.inb].groupby("trip_id").seq
lo, hi = g.min(), g.max()
n = g.count()
keep = n[n >= 2].index
st = st[st.trip_id.isin(keep)]
st = st[(st.seq >= st.trip_id.map(lo)) & (st.seq <= st.trip_id.map(hi))]
# Po przycięciu nowy pierwszy przystanek zachowuje postój z rozkładu (przyjazd < odjazd), co konwerter
# zapisuje jako ujemny arrivalOffset; nowy pierwszy = tylko odjazd, nowy ostatni = tylko przyjazd.
first, last = st.seq == st.trip_id.map(lo), st.seq == st.trip_id.map(hi)
st.loc[first, "arrival_time"] = st.loc[first, "departure_time"]
st.loc[last, "departure_time"] = st.loc[last, "arrival_time"]
trips = trips[trips.trip_id.isin(keep)]
routes = rd("routes.txt")
routes = routes[routes.route_id.isin(set(trips.route_id))]
stops = stops[stops.stop_id.isin(set(st.stop_id))].drop(columns="inb")
cd = cd[(cd.date == a.day) & cd.service_id.isin(set(trips.service_id))]
with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as o:
    for name, df in [("agency.txt", rd("agency.txt")), ("routes.txt", routes), ("trips.txt", trips),
                     ("stops.txt", stops), ("stop_times.txt", st.drop(columns=["seq", "inb"])),
                     ("calendar_dates.txt", cd)]:
        o.writestr(name, df.to_csv(index=False))
print(f"kursy={len(trips)} linie={len(routes)} przystanki={len(stops)} stop_times={len(st)} bbox=({minx:.0f},{miny:.0f},{maxx:.0f},{maxy:.0f})")
