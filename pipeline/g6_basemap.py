"""G6: podklad mapowy (ciemny motyw) z OSM, przyciety do powiatu. Wejscie: data/raw/osm/lodzkie-*.osm.pbf + scenarios/kutno/area/powiat.geojson.
Wyjscie: <out>/basemap.npz = trojkaty poligonow (<kat>_v, <kat>_f) i odcinki linii (<kat>_s), wspolrzedne wzgledem origin (524805, 485023) EPSG:2180.
 uv run python pipeline/g6_basemap.py --out output/g6_blender_r3"""
import argparse, glob, re
from pathlib import Path
import numpy as np, geopandas as gpd, shapely, pyogrio
from shapely.geometry import box

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="output/g6_blender_r3"); a = ap.parse_args()
ROOT = Path(__file__).resolve().parents[1]; ORG = np.array((524805.0, 485023.0))
pbf = sorted(glob.glob(str(ROOT / "data/raw/osm/*.osm.pbf")))[-1]
pw = gpd.read_file(ROOT / "scenarios/kutno/area/powiat.geojson").to_crs(2180).geometry.iloc[0]
bb = tuple(gpd.GeoSeries([box(*pw.buffer(500).bounds)], crs=2180).to_crs(4326).total_bounds)
tag = lambda s, k: (re.search(rf'"{k}"=>"([^"]*)"', s) or [None, None])[1] if isinstance(s, str) else None
def poly_cat(r):    # kolejnosc = priorytet kategorii przy wielu tagach
    b = r.building
    if isinstance(b, str) and b != "no": return "building"
    ot = r.other_tags; nat, lu, le = r.natural, r.landuse, r.leisure
    if nat == "water" or lu in ("reservoir", "basin") or tag(ot, "waterway") == "riverbank": return "water"
    if lu == "forest" or nat == "wood": return "forest"
    if le in ("park", "garden", "pitch", "playground", "sports_centre", "golf_course") or lu in ("grass", "meadow", "recreation_ground", "cemetery", "village_green", "allotments") or nat in ("scrub", "grassland", "wetland"): return "green"
    if lu in ("industrial", "commercial", "retail", "garages", "construction", "railway", "quarry", "landfill"): return "industrial"
    if lu == "residential": return "residential"
    if lu in ("farmland", "orchard", "vineyard", "farmyard"): return "farmland"
    return None
print("pbf", pbf, "bbox", bb)
P = pyogrio.read_dataframe(pbf, layer="multipolygons", bbox=bb, columns=["building", "natural", "landuse", "leisure", "other_tags"]).to_crs(2180)
P["cat"] = [poly_cat(r) for r in P.itertuples()]; P = P[P.cat.notna()]
print(P.cat.value_counts().to_dict())
out = {}
def tris(geoms):
    V, F, n = [], [], 0
    for g in geoms:
        for pg in (g.geoms if hasattr(g, "geoms") else [g]):
            if pg.geom_type != "Polygon" or pg.is_empty: continue
            for t in shapely.constrained_delaunay_triangles(pg).geoms:
                c = np.array(t.exterior.coords)[:3] - ORG; V.append(c); F.append([n, n + 1, n + 2]); n += 3
    return (np.concatenate(V).astype(np.float32), np.array(F, np.int32)) if V else (np.zeros((0, 2), np.float32), np.zeros((0, 3), np.int32))
for cat, g in P.groupby("cat"):
    gm = g.geometry.make_valid()
    if cat == "building": gm = gm[gm.centroid.within(pw)]
    else: gm = gm.simplify(3).intersection(pw)
    gm = gm[~gm.is_empty]; v, f = tris(gm); out[f"{cat}_v"], out[f"{cat}_f"] = v, f; print(cat, len(gm), "poligonow", len(f), "trojkatow")
L = pyogrio.read_dataframe(pbf, layer="lines", bbox=bb, columns=["railway", "waterway", "other_tags"]).to_crs(2180)
def segs(g):
    S = []
    for ln in g.geometry.intersection(pw):
        for l in (ln.geoms if hasattr(ln, "geoms") else [ln]):
            if l.geom_type == "LineString" and len(l.coords) > 1:
                c = np.array(l.coords)[:, :2] - ORG; S.append(np.c_[c[:-1], c[1:]])
    return np.concatenate(S).astype(np.float32) if S else np.zeros((0, 4), np.float32)
out["rail_s"] = segs(L[L.railway == "rail"]); out["river_s"] = segs(L[L.waterway.isin(["river", "canal"])]); out["stream_s"] = segs(L[L.waterway.isin(["stream", "drain"])])
print({k: len(v) for k, v in out.items() if k.endswith("_s")})
np.savez_compressed(Path(a.out) / "basemap.npz", **out); print("zapisano", Path(a.out) / "basemap.npz")
