"""G5: czas dojazdu gmina powiatu -> Kutno w runie (z kongestią) vs czas swobodny tych samych nóg vs macierz GUS 2021.

Użycie: uv run python -W ignore pipeline/g5_gus_czasy_r3.py <out_prefix> <plans_meta.csv> <output_dir> [<output_dir> ...]
Nogi: car, przyjeżdżający z domem w budynku gminy powiatu (home_src osm_*, nie wjazd graniczny), podróż 1 (dom -> praca).
Czas swobodny: ta sama para linków, najkrótsza ścieżka po length/freespeed od końca linku startu do końca linku celu
(tak MATSim liczy nogę car). Kongestia = czas w runie / czas swobodny. GUS: centroid -> centroid (reports/g5_walidacja/gus_vs_siec.csv).
Wyjście: <out_prefix>.csv (per gmina), <out_prefix>.json, <out_prefix>.png.
"""
import json
import sys
from pathlib import Path

import matplotlib
import networkx as nx
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # ciemny motyw (prośba użytkownika)

out, meta, runs = sys.argv[1], sys.argv[2], [Path(a) for a in sys.argv[3:]]
m = pd.read_csv(meta, dtype={"key": str})
m = m[(m.kind == "commuter") & m.home_src.str.startswith("osm_")].set_index("person")
L = pd.read_csv(runs[0] / "output_links.csv.zst", sep=";", dtype={"link": str, "from_node": str, "to_node": str}).set_index("link")
L["t"] = L.length / L.freespeed
G = nx.DiGraph()
G.add_weighted_edges_from(zip(L.from_node, L.to_node, L.t))

legs = []
for d in runs:
    l = pd.read_csv(d / "output_legs.csv.zst", sep=";", dtype={"start_link": str, "end_link": str})
    l = l[(l["mode"] == "car") & l.trip_id.str.endswith("_1") & l.person.isin(m.index)].copy()
    l["run"] = d.name
    legs.append(l)
l = pd.concat(legs)
l["model_s"] = pd.to_timedelta(l.trav_time).dt.total_seconds()
l["teryt"] = l.person.map(m.key)

ff = {}
for a, grp in l.groupby("start_link"):
    dist = nx.single_source_dijkstra_path_length(G, L.to_node[a], weight="weight")
    for b in grp.end_link.unique():
        ff[(a, b)] = dist[L.from_node[b]] + L.t[b] if a != b else 0.0
l["ff_s"] = [ff[(a, b)] for a, b in zip(l.start_link, l.end_link)]
l["congestion"] = l.model_s / l.ff_s
dep = pd.to_timedelta(l.dep_time).dt.total_seconds() / 3600

gus = pd.read_csv("reports/g5_walidacja/gus_vs_siec.csv", dtype={"teryt": str})
g = l.groupby("teryt").agg(legs=("model_s", "size"), model_min=("model_s", "median"), ff_min=("ff_s", "median"),
                           km=("distance", "median"), congestion=("congestion", "median")).reset_index()
g[["model_min", "ff_min"]] /= 60
g["km"] /= 1000
g = g.merge(gus[["teryt", "gmina", "gus_min", "gus_km", "siec_min"]], on="teryt")
g["model_vs_gus"] = g.model_min / g.gus_min
g["ff_vs_gus"] = g.ff_min / g.gus_min
g = g.sort_values("gus_min").round(3)
g.to_csv(out + ".csv", index=False, lineterminator="\n")

rep = {"runs": [str(d) for d in runs], "legs": len(l), "gminy": len(g),
       "median_congestion_all_legs": round(float(l.congestion.median()), 3),
       "p90_congestion_all_legs": round(float(l.congestion.quantile(0.9)), 3),
       "median_congestion_dep_6_9": round(float(l.congestion[(dep >= 6) & (dep < 9)].median()), 3),
       "sum_model_vs_sum_ff": round(float(l.model_s.sum() / l.ff_s.sum()), 3),
       "median_model_vs_gus": round(float(g.model_vs_gus.median()), 3),
       "median_ff_vs_gus": round(float(g.ff_vs_gus.median()), 3),
       "median_ff_legs_vs_ff_centroid": round(float((g.ff_min / g.siec_min).median()), 3)}
json.dump(rep, open(out + ".json", "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print(json.dumps(rep, ensure_ascii=False, indent=1))
print(g.to_string())

fig, ax = plt.subplots(figsize=(7, 6))
mx = g[["gus_min", "model_min", "ff_min"]].values.max() * 1.05
ax.scatter(g.gus_min, g.ff_min, s=22, c="#aed581", label="sieć, czas swobodny tych samych nóg")
ax.scatter(g.gus_min, g.model_min, s=22, c="#4fc3f7", label="run R3 (z kongestią)")
ax.plot([0, mx], [0, mx], "w--", lw=0.8, label="y = x")
ax.set_xlabel("GUS 2021, centroid -> centroid [min]"); ax.set_ylabel("model, mediana nóg dom -> praca [min]")
ax.set_title(f"Dojazd gmina powiatu -> Kutno ({len(runs)} seed(y), {len(l)} nóg)", fontsize=10)
ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(out + ".png", dpi=130)
