"""Kontrola przed runem (zasady projektu workflow pkt 7): top-10 celów, źródeł i budynków w planach; max(start) + praca + dojazd < endTime.

Użycie: uv run python -W ignore reports/etap2/audyt_g5/poprawki/skrypty/c6_prerun.py <plans_stem>   (np. scenarios/kutno/plans_g5r6_25pct)
Bez importu z pipeline/. Budynki: osm_id z *_meta.csv i sjoin końców tła z features.gpkg.
"""
import sys

import geopandas as gpd
import pandas as pd

stem = sys.argv[1]
m = pd.read_csv(stem + "_meta.csv")
b = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")[["osm_id", "building", "amenity", "shop", "geometry"]]
b["a_m2"] = b.area.round()
bi = b.set_index("osm_id")


def bld(src):
    i = src.str.replace("osm_", "", regex=False)
    t = src.value_counts().head(10).rename("n").to_frame()
    t["building"] = [bi.building.get(int(x[4:]) if x.startswith("osm_") else None, "-") if x.startswith("osm_") else x for x in t.index]
    t["amenity/shop"] = [(str(bi.amenity.get(int(x[4:]))) + "/" + str(bi.shop.get(int(x[4:])))) if x.startswith("osm_") else "" for x in t.index]
    t["a_m2"] = [bi.a_m2.get(int(x[4:])) if x.startswith("osm_") else None for x in t.index]
    return t


pd.set_option("display.width", 200)
print("top-10 budynków pracy (cele pracujących):\n", bld(m.work_src).to_string())
print("top-10 budynków domów:\n", bld(m.home_src).to_string())
print("top-10 linków wjazdu przyjeżdżających:\n", m[m.home_src == "entry"].home_link.value_counts().head(10).to_string())
for f in ("tlo", "ciezkie"):
    t = pd.read_csv(f"{stem}_{f}.csv")
    print(f"top-10 źródeł {f} (o):\n", t.o.value_counts().head(10).to_string())
    print(f"top-10 celów {f} (d):\n", t.d.value_counts().head(10).to_string())
    pts = pd.concat([t[["o_x", "o_y"]].set_axis(["x", "y"], axis=1), t[["d_x", "d_y"]].set_axis(["x", "y"], axis=1)])
    g = gpd.GeoDataFrame(geometry=gpd.points_from_xy(pts.x, pts.y), crs=b.crs)
    j = gpd.sjoin(g, b, predicate="within")
    print(f"top-10 budynków końców {f}:\n", j.groupby(["osm_id", "building", "a_m2"]).size().sort_values(ascending=False).head(10).to_string())
    print(f"{f}: max start {t.start_s.max() / 3600:.2f} h")
print(f"pracujący: max start {m.start_s.max() / 3600:.2f} h + 8 h pracy + dojazd (< 2 h) = {(m.start_s.max() / 3600 + 10):.1f} h < endTime 48 h")
