"""Pole izochrony (obwiednia osiągalnej sieci w odległości d) vs koło o promieniu d. Wejście: output/g4_beeline/isochrones.csv"""
import pandas as pd, numpy as np
d = pd.read_csv("output/g4_beeline/isochrones.csv")
for c in ("convex", "concave"):
    d[f"ratio_{c}"] = d[f"A_{c}"] / d.A_circle              # pole/πd²
    d[f"f_area_{c}"] = 1 / np.sqrt(d[f"ratio_{c}"])         # d / r_ekw
d["f_meanend"] = d.d / d.mean_end_euclid
d["f_max"] = d.d / d.max_end_euclid
g = d.groupby(["mode", "d"]).agg(n=("d", "size"), pole_concave_ratio=("ratio_concave", "mean"), pole_convex_ratio=("ratio_convex", "mean"),
    f_area_concave=("f_area_concave", "mean"), f_area_convex=("f_area_convex", "mean"), f_meanend=("f_meanend", "mean"), f_max=("f_max", "mean"))
print(g.round(3).to_string())
print("\nodwrotność stosunku pól (hipoteza użytkownika: A_koło/A_izochrona):")
print((1 / g[["pole_concave_ratio", "pole_convex_ratio"]]).round(2).to_string())
