"""G5: czas przejazdu gmina -> Kutno: macierz dostępności GUS 2021 vs czas swobodny w naszej sieci (D13).

Sieć: najkrótszy czas po length/freespeed (freespeed = 0,8 x dozwolona, D13), z węzła najbliższego centroidowi gminy
do węzła najbliższego centroidowi Kutna (1002011), czyli tak, jak liczy GUS (centroid -> centroid).
Wyjście: scenarios/kutno/validation/gus_vs_siec.csv, reports/etap2/g5_walidacja/gus_vs_siec.png

Wariant `ors <output_dir>` (K5): te same trasy liczone z prędkościami jak w profilu car openrouteservice (VehicleFlagEncoder,
GIScience/openrouteservice main, docs/ZRODLA.md): tag maxspeed -> 0,9 × maxspeed, bez tagu -> prędkość domyślna klasy.
Bez kar za nawierzchnię i krótkie odcinki residential. Atrybuty linków z output_links runu. Wyjście: gus_vs_siec_ors.{csv,png}.
"""
import sys
import gzip
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from pyproj import Transformer

OUT = "reports/etap2/g5_walidacja/"
VAL = "scenarios/kutno/validation/"  # wejścia innych skryptów (punkty GPR, czasy GUS)
ORS = len(sys.argv) > 2 and sys.argv[1] == "ors"
SUF = "_ors" if ORS else ""
ORS_KMH = {"motorway": 100, "motorway_link": 60, "trunk": 85, "trunk_link": 60, "primary": 65, "primary_link": 50,
           "secondary": 60, "secondary_link": 50, "tertiary": 50, "tertiary_link": 40, "unclassified": 30,
           "residential": 30, "living_street": 10, "service": 20, "road": 20, "track": 15}
tr = Transformer.from_crs(4326, 2180, always_xy=True)

nodes, G = {}, nx.DiGraph()
for _, e in ET.iterparse(gzip.open("scenarios/kutno/network.xml.gz")):
    if e.tag == "node":
        nodes[e.get("id")] = (float(e.get("x")), float(e.get("y")))
    elif e.tag == "link":
        L, v = float(e.get("length")), float(e.get("freespeed"))
        G.add_edge(e.get("from"), e.get("to"), t=L / v, L=L)
        e.clear()
if ORS:
    A = pd.read_csv(sys.argv[2] + "/output_links.csv.zst", sep=";", dtype={"from_node": str, "to_node": str})
    v = np.where(A.speed_source == "tag", 0.9 * A.allowed_speed, A.type.map(ORS_KMH).fillna(30) / 3.6)
    v = np.where(A.speed_source == "boundary_turnaround", A.freespeed, v)
    for a, b, L, vv in zip(A.from_node, A.to_node, A.length, v):
        G[a][b]["t"] = L / vv
ids = np.array(list(nodes))
xy = np.array([nodes[i] for i in ids])


def snap(lon, lat):
    x, y = tr.transform(lon, lat)
    d = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
    k = d.argmin()
    return ids[k], d[k], x, y


c = pd.read_excel("data/raw/gus_transport/macierz_dostepnosci_20210331.xlsx", sheet_name="centroidy_gmin", dtype={"TERYT": str})
c.columns = ["teryt", "gmina", "lon", "lat", "opis", "opis_en"]
gus = pd.read_csv("scenarios/kutno/demand/gus_czas_do_kutna_2021.csv", dtype={"teryt": str})
c = c.merge(gus[["teryt", "czas_s_do_kutna", "droga_km_do_kutna"]], on="teryt")
dest = c[c.teryt == "1002011"].iloc[0]
dnode, ddist, dx, dy = snap(dest.lon, dest.lat)
print("cel Kutno: węzeł", dnode, "odl. %.0f m" % ddist)

# najkrótsze ścieżki DO Kutna = Dijkstra z Kutna na grafie odwróconym; długość trasy po tej samej ścieżce
R = G.reverse(copy=False)
tt, paths = nx.single_source_dijkstra(R, dnode, weight="t")
rows = []
for _, r in c.iterrows():
    if r.teryt == "1002011":
        continue
    n, d, x, y = snap(r.lon, r.lat)
    if d > 3000 or n not in tt:  # centroid poza obszarem sieci (powiat + bufor)
        continue
    p = paths[n][::-1]
    km = sum(G[a][b]["L"] for a, b in zip(p, p[1:])) / 1000
    rows.append(dict(teryt=r.teryt, gmina=r.gmina, snap_m=round(d), gus_min=r.czas_s_do_kutna / 60, siec_min=tt[n] / 60,
                     gus_km=r.droga_km_do_kutna, siec_km=km))
t = pd.DataFrame(rows)
t["czas_ratio"] = t.siec_min / t.gus_min
t["km_ratio"] = t.siec_km / t.gus_km
t["v_gus_kmh"] = t.gus_km / (t.gus_min / 60)
t["v_siec_kmh"] = t.siec_km / (t.siec_min / 60)
t = t.sort_values("gus_min").round(2)
t.to_csv(VAL + f"gus_vs_siec{SUF}.csv", index=False)
print(t.to_string())
print(t[["czas_ratio", "km_ratio", "v_gus_kmh", "v_siec_kmh"]].describe().round(2))
w = t[t.gus_min <= 60]
print("do 60 min GUS: mediana czas_ratio %.2f, ważona km %.2f" % (w.czas_ratio.median(), w.siec_min.sum() / w.gus_min.sum()))

plt.style.use("dark_background")
fig, ax = plt.subplots(1, 2, figsize=(11, 4.8))
ax[0].scatter(t.gus_min, t.siec_min, s=22, c="#4fc3f7")
m = t[["gus_min", "siec_min"]].values.max()
ax[0].plot([0, m], [0, m], "w--", lw=0.8, label="y = x")
ax[0].plot([0, m], [0, 1.25 * m], color="#ff8a65", lw=0.8, ls=":", label="y = 1,25x")
ax[0].set_xlabel("GUS 2021 [min]"); ax[0].set_ylabel("sieć, czas swobodny" + (" (prędkości ORS)" if ORS else "") + " [min]"); ax[0].legend(); ax[0].set_title("Czas przejazdu do Kutna")
ax[1].scatter(t.gus_km, t.siec_km, s=22, c="#aed581")
mk = t[["gus_km", "siec_km"]].values.max()
ax[1].plot([0, mk], [0, mk], "w--", lw=0.8)
ax[1].set_xlabel("GUS 2021 [km]"); ax[1].set_ylabel("sieć [km]"); ax[1].set_title("Długość trasy")
fig.tight_layout(); fig.savefig(OUT + f"gus_vs_siec{SUF}.png", dpi=150)
