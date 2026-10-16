"""F2: granica gminy Kutno i obszaru sieci (powiat + bufor) z geometrii BREC 2021.

Wejście: data/raw/brec/gml/AreaStatisticalUnit_10.xml (EPSG:4258).
Wyjście (EPSG:2180, osie E,N): scenarios/kutno/area/{gmina,powiat,network_area}.geojson
oraz network_area.wkt dla konwertera Java.
"""
import json
import tomllib
from pathlib import Path

import pyogrio

cfg = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))["area"]
out = Path("scenarios/kutno/area")
out.mkdir(parents=True, exist_ok=True)

df = pyogrio.read_dataframe("data/raw/brec/gml/AreaStatisticalUnit_10.xml",
                            columns=["LocationString", "thematicId|ThematicIdentifier|identifier"])
df["teryt"] = df["LocationString"].astype(str).str.zfill(7)
df["unit_id"] = df["thematicId|ThematicIdentifier|identifier"].astype(str)
rej = df[df["unit_id"].str.len() == 6].to_crs("EPSG:2180")  # rejony; obwody (7 cyfr) pokrywają ten sam obszar

gmina = rej[rej["teryt"] == cfg["teryt_gmina"]]
powiat = rej[rej["teryt"].str.startswith(cfg["teryt_powiat"])]
g_geom, p_geom = gmina.union_all(), powiat.union_all()
area_geom = p_geom.buffer(cfg["network_buffer_m"])

stats = {"rejony_gmina": len(gmina), "rejony_powiat": len(powiat),
         "gminy_teryt_w_powiecie": sorted(powiat["teryt"].unique()),
         "gmina_km2": round(g_geom.area / 1e6, 2), "powiat_km2": round(p_geom.area / 1e6, 2),
         "network_area_km2": round(area_geom.area / 1e6, 2),
         "network_area_bounds_EN": [round(v) for v in area_geom.bounds],
         "buffer_m": cfg["network_buffer_m"]}
assert stats["rejony_gmina"] == 41, stats  # FACT_CHECK #13
from shapely.geometry import Point
# centrum Kutna 19,3633 E / 52,2307 N -> pyproj EPSG:2180 (FACT_CHECK #17); zamiana osi by to złamała
assert g_geom.contains(Point(524805, 485023)), "osie E,N?"

import geopandas as gpd
for name, geom in [("gmina", g_geom), ("powiat", p_geom), ("network_area", area_geom)]:
    gpd.GeoSeries([geom], crs="EPSG:2180").to_file(out / f"{name}.geojson", driver="GeoJSON")
(out / "network_area.wkt").write_text(area_geom.simplify(10).wkt)
Path("reports/f2_area.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
print(json.dumps(stats, indent=2, ensure_ascii=False))
