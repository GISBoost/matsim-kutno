"""G5: mapa punktów GPR 2025 i przypisanych linków (ciemny motyw). Wejście: wynik g5_gpr.py."""
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.collections import LineCollection

sys.path.insert(0, "pipeline")
import g5_gpr as G

OUT = "reports/etap2/g5_walidacja/"
VAL = "scenarios/kutno/validation/"  # wejścia innych skryptów (punkty GPR, czasy GUS)
g = G.links()
p = pd.read_csv(VAL + "gpr_punkty.csv")
m = pd.read_csv(VAL + "gpr_linki.csv")
powiat = gpd.read_file("scenarios/kutno/area/powiat.geojson").to_crs(2180)

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(12, 9))
powiat.boundary.plot(ax=ax, color="#888", lw=1)
major = g[g.hw.isin(["motorway", "trunk", "primary", "secondary", "tertiary"])]
minor = g[~g.index.isin(major.index)]
ax.add_collection(LineCollection([list(l.coords) for l in minor.geometry], colors="#2a2f36", linewidths=0.3))
ax.add_collection(LineCollection([list(l.coords) for l in major.geometry], colors="#5c6672", linewidths=0.9))
hit = g[g.link.isin(m.link)].merge(m[["link", "sdrr_kier"]], on="link")
hit.plot(ax=ax, column="sdrr_kier", cmap="plasma", linewidth=3.2, legend=True,
         legend_kwds={"label": "SDRR GPR 2025 na kierunek [poj./dobę, wszystkie silnikowe]", "shrink": 0.6})
inside = p[p.nr.isin(m.nr)].drop_duplicates("nr")
outside = p[~p.nr.isin(m.nr)].drop_duplicates("nr")
ax.scatter(outside.E, outside.N, s=14, c="#78909c", marker="x", label=f"punkt GPR bez linku w sieci ({len(outside)})")
ax.scatter(inside.E, inside.N, s=40, facecolors="none", edgecolors="w", label=f"punkt GPR przypisany do linków ({len(inside)})")
for _, r in inside.iterrows():
    ax.annotate(f"{r.droga.replace(chr(10), '/')}\n{int(r.sdr)}", (r.E, r.N), xytext=(5, 5), textcoords="offset points", fontsize=7, color="w")
kx, ky = g[g.frm == "331617403"].geometry.iloc[0].coords[0]
ax.scatter([kx], [ky], marker="*", s=160, c="#ffee58", label="Kutno (węzeł najbliżej centroidu GUS)")
ax.set_aspect("equal"); ax.legend(loc="lower left", fontsize=8)
ax.set_title("GPR 2025 (GDDKiA): punkty pomiarowe i linki sieci Kutna, EPSG:2180")
ax.set_xlabel("E [m]"); ax.set_ylabel("N [m]")
fig.tight_layout(); fig.savefig(OUT + "gpr_mapa.png", dpi=150)
print("ok", len(hit), len(inside), len(outside))
