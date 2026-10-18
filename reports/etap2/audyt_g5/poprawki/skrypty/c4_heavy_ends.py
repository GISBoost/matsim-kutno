"""Kontrola S3 / D9 (krok 4): w jakich budynkach są końce ciężkich w gminach powiatu (jak audyt: sjoin punktów z plans_*_ciezkie.csv).

Użycie: uv run python -W ignore reports/etap2/audyt_g5/poprawki/skrypty/c4_heavy_ends.py <plans_*_ciezkie.csv> [...]
Bez importu z pipeline/. Typy mieszkalne i gospodarcze jak w audycie D9.
"""
import sys

import geopandas as gpd
import pandas as pd

RES = {"house", "detached", "apartments", "residential", "semidetached_house", "terrace", "bungalow", "farm", "dormitory"}
FARM = {"farm_auxiliary", "outbuilding", "garage", "shed"}
b = gpd.read_file("scenarios/kutno/osm/features.gpkg", layer="buildings")[["building", "geometry"]]
for f in sys.argv[1:]:
    h = pd.read_csv(f)
    pts = []
    for e in ("o", "d"):
        pts.append(pd.DataFrame({"x": h[f"{e}_x"], "y": h[f"{e}_y"]}))
    p = pd.concat(pts)
    g = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.x, p.y), crs=b.crs)
    j = gpd.sjoin(g, b, predicate="within", how="inner")  # końce graniczne nie leżą w budynkach i odpadają
    t = j.building.map(lambda x: "mieszkalne" if x in RES else "gospodarcze" if x in FARM else "inne").value_counts(normalize=True)
    print(f, "końce w budynkach:", len(j), (t * 100).round(1).to_dict(),
          "top:", (j.building.value_counts(normalize=True).head(6) * 100).round(1).to_dict())
