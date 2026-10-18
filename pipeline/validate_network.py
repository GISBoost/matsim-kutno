"""F2: walidacja sieci MATSim + mapa kontrolna.

Użycie: uv run python pipeline/validate_network.py scenarios/kutno/network.xml.gz
Wyjście: reports/etap1_mvp/f2_network/f2_network.json, reports/etap1_mvp/f2_network/f2_network.png. Kod 1, gdy test nie przechodzi.
"""
import collections
import gzip
import json
import random
import sys

import geopandas as gpd
import matplotlib
import networkx as nx
from lxml import etree
from shapely.geometry import Point

matplotlib.use("Agg")
import matplotlib.pyplot as plt

KUTNO_CENTRE = (524805, 485023)  # FACT_CHECK #17
N_RANDOM, SEED = 5, 42

path = sys.argv[1]
nodes, links = {}, []
with gzip.open(path, "rb") as f:
    for _, el in etree.iterparse(f, tag=("node", "link")):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
        else:
            attrs = {a.get("name"): a.text for a in el.iter("attribute")}
            links.append(dict(id=el.get("id"), a=el.get("from"), b=el.get("to"), length=float(el.get("length")),
                              speed=float(el.get("freespeed")), cap=float(el.get("capacity")),
                              lanes=float(el.get("permlanes")), modes=el.get("modes"), hw=attrs.get("type"), src=attrs.get("speed_source")))
        el.clear()

area = gpd.read_file("scenarios/kutno/area/network_area.geojson").geometry.iloc[0]
gmina = gpd.read_file("scenarios/kutno/area/gmina.geojson").geometry.iloc[0]
powiat = gpd.read_file("scenarios/kutno/area/powiat.geojson").geometry.iloc[0]

G = nx.DiGraph()
for l in links:
    G.add_edge(l["a"], l["b"], t=l["length"] / l["speed"])
scc = max(nx.strongly_connected_components(G), key=len)

xs, ys = zip(*nodes.values())
# Supersonic bierze całą drogę do najbliższego skrzyżowania, gdy jeden z jej węzłów jest w obszarze,
# więc końce odcinków mogą wychodzić poza obszar. Raportujemy je; porażka dopiero > OUTSIDE_MAX_M.
OUTSIDE_MAX_M = 5000
dist_out = [area.distance(Point(p)) for p in nodes.values() if not area.contains(Point(p))]
outside = len(dist_out)


def nearest(pt):
    return min(scc, key=lambda n: (nodes[n][0] - pt[0]) ** 2 + (nodes[n][1] - pt[1]) ** 2)


# punkty testowe: centrum Kutna, 4 skrajne węzły sieci (wjazdy z 4 kierunków), 5 losowych z seeda
ext = {"N": max(scc, key=lambda n: nodes[n][1]), "S": min(scc, key=lambda n: nodes[n][1]),
       "E": max(scc, key=lambda n: nodes[n][0]), "W": min(scc, key=lambda n: nodes[n][0])}
test = {"centrum": nearest(KUTNO_CENTRE), **ext}
rnd = random.Random(SEED)
test.update({f"los{i}": n for i, n in enumerate(rnd.sample(sorted(scc), N_RANDOM))})

routes, failed = {}, []
for oa, o in test.items():
    for da, d in test.items():
        if o == d:
            continue
        try:
            t = nx.shortest_path_length(G, o, d, weight="t")
            routes[f"{oa}->{da}"] = round(t / 60, 1)
        except nx.NetworkXNoPath:
            failed.append(f"{oa}->{da}")

bad = [l["id"] for l in links if l["speed"] <= 0 or l["cap"] <= 0 or l["length"] <= 0 or l["lanes"] <= 0]
non_car = [l["id"] for l in links if l["modes"] != "car"]
report = {
    "network": path, "nodes": len(nodes), "links": len(links),
    "scc_largest_nodes_share": round(len(scc) / len(nodes), 4),
    "bbox_EN": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))],
    "nodes_outside_area": outside,
    "nodes_outside_max_m": round(max(dist_out, default=0)),
    "network_km_by_freespeed_kmh": {k: round(v) for k, v in sorted(collections.Counter(
        {}).items())},
    "kutno_centre_nearest_node_m": round(((nodes[test["centrum"]][0] - KUTNO_CENTRE[0]) ** 2 + (nodes[test["centrum"]][1] - KUTNO_CENTRE[1]) ** 2) ** .5),
    "links_bad_attrs": len(bad), "links_non_car": len(non_car),
    "highway_types": dict(collections.Counter(l["hw"] for l in links).most_common()),
    "km_and_median_freespeed_kmh_by_type": {hw: [round(sum(l["length"] for l in ls) / 1000),
                                                  round(sorted(l["speed"] for l in ls)[len(ls) // 2] * 3.6)]
                                             for hw in {l["hw"] for l in links}
                                             for ls in [[l for l in links if l["hw"] == hw]]},
    "total_length_km": round(sum(l["length"] for l in links) / 1000),
    "test_points": {k: [round(v) for v in nodes[n]] for k, n in test.items()},
    "routes_ok": len(routes), "routes_failed": failed,
    "route_minutes_centrum_to": {k.split("->")[1]: v for k, v in routes.items() if k.startswith("centrum->")},
}
km = collections.Counter()
for l in links:
    km[round(l["speed"] * 3.6)] += l["length"] / 1000
report["km_by_speed_source"] = {k: round(v) for k, v in collections.Counter(
    {src: sum(l["length"] for l in links if l["src"] == src) / 1000 for src in {l["src"] for l in links}}).most_common()}
report["network_km_by_freespeed_kmh"] = {k: round(v) for k, v in sorted(km.items()) if v >= 1}
report["motorway_km"] = round(sum(l["length"] for l in links if l["hw"] == "motorway") / 1000, 1)
report["turnaround_links"] = sum(1 for l in links if l["hw"] == "boundary_turnaround")
MOTORWAY_MIN_KM = 60  # A1 przecina powiat N-S: ~2 jezdnie x ~35 km (OSM PBF ma 94 km jezdni A1 w bbox obszaru)
report["ok"] = (report["motorway_km"] >= MOTORWAY_MIN_KM and not failed and not bad and not non_car and report["nodes_outside_max_m"] <= OUTSIDE_MAX_M
                and report["scc_largest_nodes_share"] > 0.98 and report["kutno_centre_nearest_node_m"] < 300)
json.dump(report, open("reports/etap1_mvp/f2_network/f2_network.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# mapa kontrolna
fig, ax = plt.subplots(figsize=(11, 9))
gpd.GeoSeries([area]).boundary.plot(ax=ax, color="0.6", lw=1, ls="--")
gpd.GeoSeries([powiat]).boundary.plot(ax=ax, color="0.3", lw=1.2)
gpd.GeoSeries([gmina]).plot(ax=ax, color="#fde9c9", edgecolor="#c47f17", lw=1.2)
cmap = plt.get_cmap("plasma_r")
order = {"motorway": 5, "trunk": 4, "primary": 3, "secondary": 2, "tertiary": 1.2}
for l in sorted(links, key=lambda l: order.get((l["hw"] or "").replace("_link", ""), 0.5)):
    w = order.get((l["hw"] or "").replace("_link", ""), 0.4)
    a, b = nodes[l["a"]], nodes[l["b"]]
    ax.plot([a[0], b[0]], [a[1], b[1]], color=cmap(min(l["speed"] * 3.6, 100) / 100), lw=max(w, 0.6) * 0.6,
            solid_capstyle="round")
for k, n in test.items():
    ax.plot(*nodes[n], "o", color="#d1495b", ms=6, zorder=5)
    ax.annotate(k, nodes[n], xytext=(4, 4), textcoords="offset points", fontsize=8, color="#d1495b")
ax.set_title(f"F2 sieć car — {len(links)} linków, {report['total_length_km']} km | "
             f"trasy testowe: {len(routes)} OK, {len(failed)} błędów | {'ZALICZONA' if report['ok'] else 'NIE ZALICZONA'}",
             fontsize=10)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 100)); fig.colorbar(sm, ax=ax, shrink=0.6, label="freespeed [km/h]")
ax.set_xlabel("E [m] EPSG:2180"); ax.set_ylabel("N [m]"); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig("reports/etap1_mvp/f2_network/f2_network.png", dpi=130)
print(json.dumps({k: report[k] for k in ("nodes", "links", "scc_largest_nodes_share", "nodes_outside_area",
                  "nodes_outside_max_m", "kutno_centre_nearest_node_m", "links_bad_attrs", "routes_ok", "routes_failed",
    "km_and_median_freespeed_kmh_by_type", "km_by_speed_source", "motorway_km", "turnaround_links", "route_minutes_centrum_to", "ok")}, indent=1, ensure_ascii=False))
sys.exit(0 if report["ok"] else 1)
