"""Testy semantyczne scenarios/kutno_pt + mapa linii. Uruchom z korzenia repo:
uv run python reports/etap3/g_pt_import/test_pt_import.py --raw <katalog z data/raw> [--area <network_area.wkt>]
Zwraca kod != 0 przy porażce, wynik zapisuje do wyniki_testow.txt i mapa_linii.png obok skryptu."""
import argparse, gzip, subprocess, sys, tempfile, zipfile, collections
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely import wkt

ap = argparse.ArgumentParser()
ap.add_argument("--raw", default="data/raw")
ap.add_argument("--area", default="scenarios/kutno/area/network_area.wkt")
ap.add_argument("--day", default="20261020")
a = ap.parse_args()
here = Path(__file__).parent
pt = Path("scenarios/kutno_pt")
minx, miny, maxx, maxy = wkt.loads(open(a.area).read()).bounds
res, fails = [], []


def check(name, ok, info=""):
    res.append(f"[{'OK ' if ok else 'BLAD'}] {name}: {info}")
    if not ok:
        fails.append(name)


def hms(s):
    sign = -1 if s.startswith("-") else 1
    h, m, sec = map(int, s.lstrip("-").split(":"))
    return sign * (h * 3600 + m * 60 + sec)


def load(p):
    return ET.parse(gzip.open(p)).getroot()


# --- oczekiwania z GTFS (niezależnie od konwertera) ---
def active_trips(zf, day):
    z = zipfile.ZipFile(zf)
    rd = lambda n: pd.read_csv(z.open(n), dtype=str, keep_default_na=False)
    cd = rd("calendar_dates.txt")
    svc = set(cd[(cd.date == day) & (cd.exception_type == "1")].service_id)
    t = rd("trips.txt")
    return t[t.service_id.isin(svc)]


mzk = active_trips(Path(a.raw) / "gtfs/kutno.zip", a.day)
exp_mzk_lines, exp_mzk_trips = mzk.route_id.nunique(), len(mzk)
tmp = tempfile.mkdtemp()
subprocess.run([sys.executable, "pipeline/pt_filter_gtfs.py", str(Path(a.raw) / "g4/polish_trains.zip"),
                f"{tmp}/r.zip", "--day", a.day, "--area", a.area], check=True, capture_output=True)
rail = active_trips(f"{tmp}/r.zip", a.day)
exp_rail_lines, exp_rail_trips = rail.route_id.nunique(), len(rail)

# --- schedule ---
sch = load(pt / "transitSchedule.xml.gz")
net = load(pt / "network_pt.xml.gz")
veh = load(pt / "transitVehicles.xml.gz")
nodes = {n.get("id"): (float(n.get("x")), float(n.get("y"))) for n in net.iter("node")}
links = {l.get("id"): (l.get("from"), l.get("to")) for l in net.iter("link")}
ptl = {k for k in links if k.startswith("pt_")}
vehids = {v.get("id") for v in veh.iter() if v.tag.endswith("vehicle")}
stops = {s.get("id"): s for s in sch.iter("stopFacility")}

lines = {l.get("id"): l for l in sch.iter("transitLine")}
cnt = collections.Counter()
for lid, l in lines.items():
    for d in l.iter("departure"):
        cnt[lid.split("_")[0]] += 1
nl = collections.Counter(k.split("_")[0] for k in lines)
check("linie MZK = GTFS", nl["mzk"] == exp_mzk_lines == 13, f"schedule={nl['mzk']} GTFS={exp_mzk_lines}")
check("kursy MZK = GTFS", cnt["mzk"] == exp_mzk_trips, f"schedule={cnt['mzk']} GTFS={exp_mzk_trips}")
check("linie kolej = GTFS (po filtrze bbox)", nl["kol"] == exp_rail_lines, f"schedule={nl['kol']} GTFS={exp_rail_lines}")
check("kursy kolej = GTFS (po filtrze bbox)", cnt["kol"] == exp_rail_trips, f"schedule={cnt['kol']} GTFS={exp_rail_trips}")

bad = [i for i, s in stops.items() if not (minx <= float(s.get("x")) <= maxx and miny <= float(s.get("y")) <= maxy)]
check("przystanki w zasięgu sieci (bbox network_area, x=E y=N)", not bad, f"{len(stops)} przystanków, poza: {bad[:5]}")
check("wszystkie współrzędne mają x 5xx xxx i y 4xx xxx", all(4e5 <= float(s.get("x")) < 6e5 and 4e5 <= float(s.get("y")) < 5.2e5 for s in stops.values()), "")
nolink = [i for i, s in stops.items() if s.get("linkRefId") not in links]
check("każdy przystanek ma link w sieci", not nolink, f"bez linku: {nolink[:5]}")

n_routes = n_dep = 0
bad_conn, bad_stoplink, bad_time, bad_veh, bad_order = [], [], [], [], []
neg_first = unsorted = 0
for lid, l in lines.items():
    for r in l.iter("transitRoute"):
        n_routes += 1
        rl = [x.get("refId") for x in r.find("route").iter("link")]
        if not rl or any(i not in links for i in rl) or any(links[x][1] != links[y][0] for x, y in zip(rl, rl[1:])):
            bad_conn.append(r.get("id"))
        pos = []
        for rs in r.find("routeProfile").iter("stop"):
            sl = stops[rs.get("refId")].get("linkRefId")
            pos.append(rl.index(sl) if sl in rl else -1)
        if -1 in pos or pos != sorted(pos):
            bad_stoplink.append(r.get("id"))
        prof = [(hms(s.get("arrivalOffset", s.get("departureOffset"))) if s.get("arrivalOffset") or s.get("departureOffset") else 0,
                 hms(s.get("departureOffset", s.get("arrivalOffset"))) if s.get("arrivalOffset") or s.get("departureOffset") else 0)
                for s in r.find("routeProfile").iter("stop")]
        neg_first += prof[0][0] < 0
        flat = [t for p in prof for t in p][1:]  # pierwszy arrivalOffset bywa ujemny (artefakt konwertera), pomijamy
        if flat != sorted(flat):
            bad_order.append(r.get("id"))
        deps = [(hms(d.get("departureTime")), d.get("vehicleRefId")) for d in r.find("departures").iter("departure")]
        n_dep += len(deps)
        ts = [d[0] for d in deps]
        unsorted += ts != sorted(ts)  # kolejność w pliku = kolejność trip_id; MATSim sortuje odjazdy sam
        if len(set(ts)) != len(ts) or not all(0 <= t < 30 * 3600 for t in ts):
            bad_time.append(r.get("id"))
        bad_veh += [d[1] for d in deps if d[1] not in vehids]
check("trasy: ciąg linków połączony w sieci (to==from)", not bad_conn, f"{n_routes} tras, błędne: {bad_conn[:5]}")
check("przystanki trasy leżą na jej linkach w kolejności", not bad_stoplink, f"błędne: {bad_stoplink[:5]}")
check("czasy offsetów w profilu rosną (niemalejąco)", not bad_order, f"błędne: {bad_order[:5]}")
res.append(f"INFO: tras z odjazdami nieposortowanymi w pliku (kolejność trip_id): {unsorted}")
check("odjazdy w trasie: unikalne czasy, w oknie 0-30 h", not bad_time, f"{n_dep} odjazdów, błędne: {bad_time[:5]}")
check("pojazdy z odjazdów istnieją w transitVehicles", not bad_veh, f"{len(vehids)} pojazdów")
check("liczba pojazdów = liczba odjazdów (1 pojazd na kurs)", len(vehids) == n_dep, f"{len(vehids)} vs {n_dep}")
check("brak ujemnego arrivalOffset na 1. przystanku (filtr przycięcia kolei)", neg_first == 0, f"tras z ujemnym: {neg_first}")
check("CRS: węzły PT w EPSG:2180 (x 5xx xxx)", all(4.9e5 < nodes[links[k][0]][0] < 5.6e5 for k in ptl), f"{len(ptl)} linków pt")

# --- mapa ---
plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(10, 9))
gm = gpd.read_file("scenarios/kutno/area/gmina.geojson")
gm.boundary.plot(ax=ax, color="#888", lw=1)
for lid, l in lines.items():
    kol = lid.startswith("kol")
    for r in l.iter("transitRoute"):
        xy = [(float(stops[s.get("refId")].get("x")), float(stops[s.get("refId")].get("y"))) for s in r.find("routeProfile").iter("stop")]
        ax.plot(*zip(*xy), color="#ffb000" if kol else "#4fc3f7", lw=1.6 if kol else 0.8, alpha=0.8)
xs = [float(s.get("x")) for s in stops.values()]; ys = [float(s.get("y")) for s in stops.values()]
ax.scatter(xs, ys, s=5, c="white", zorder=3)
ax.set_aspect("equal"); ax.set_xlabel("x, E [m] (EPSG:2180)"); ax.set_ylabel("y, N [m] (EPSG:2180)")
ax.set_title("Linie PT w scenariuszu kutno_pt, wtorek 2026-10-20")
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color="#4fc3f7", label="MZK Kutno (autobus)"), Line2D([], [], color="#ffb000", label="kolej"),
                   Line2D([], [], color="#888", label="granica gminy Kutno"), Line2D([], [], marker="o", ls="", color="white", ms=3, label="przystanek")], loc="upper left")
fig.savefig(here / "mapa_linii.png", dpi=130, bbox_inches="tight")

res.append(f"\nPODSUMOWANIE: linie={len(lines)} (mzk {nl['mzk']}, kolej {nl['kol']}), trasy={n_routes}, kursy={n_dep}, przystanki={len(stops)}, "
           f"linki pt={len(ptl)}, linki sieci razem={len(links)}")
(here / "wyniki_testow.txt").write_text("\n".join(res), encoding="utf-8")
print("\n".join(res))
sys.exit(1 if fails else 0)
