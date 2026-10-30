import sys, geopandas as gpd, pandas as pd
G = sys.argv[1]
pool = gpd.read_file(G, layer="bdot_errand_pool"); poi = gpd.read_file(G, layer="osm_poi")
# centrum: Pl. Piłsudskiego ~ mediana POI
c = poi.geometry.union_all().centroid
pool["d_cent_km"] = (pool.geometry.representative_point().distance(c) / 1000).round(2)
# nazwy OSM w budynku (do 15 m)
j = gpd.sjoin(pool.set_geometry(pool.buffer(15)), poi[["name", "shop", "amenity", "geometry"]], how="left")
nm = j.groupby(level=0).apply(lambda g: "; ".join(sorted({str(x) for x in g["name"].dropna()})[:3]) or ("; ".join(sorted({str(x) for x in g.shop.dropna()} | {str(x) for x in g.amenity.dropna()})[:3]) or "-"))
pool["osm"] = nm; pool["n_poi"] = j.groupby(level=0).index_right.count()
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
for t in "csu":
    q = pool[pool.errand == t].sort_values("w_pct", ascending=False)
    print(f"\n== {t}: {len(q)} budynków, top3 {q.w_pct.head(3).sum():.0f}% wagi, top10 {q.w_pct.head(10).sum():.0f}%, bez POI OSM: {(q.n_poi==0).sum()} ({100*q.w_pct[q.n_poi==0].sum()/100:.0f}% wagi)")
    print(q.head(12)[["fun", "area_m2", "LICZBAKONDYGNACJI", "w_pct", "d_cent_km", "n_poi", "osm"]].to_string())
    print("odl. od centrum (ważona wagą), km:", round((q.w_pct * q.d_cent_km).sum() / 100, 2), " >2 km: %.0f%% wagi" % q.w_pct[q.d_cent_km > 2].sum())
print("\nPOI OSM odl. od centrum: mediana %.2f km, >2 km: %.0f%%" % ((poi.distance(c) / 1000).median(), 100 * (poi.distance(c) > 2000).mean()))
print("Supermarkety OSM:"); sm = poi[poi.shop.isin(["supermarket", "mall", "department_store"])]
print(sm[["name", "shop", "bdot_fun", "bdot_errand", "bdot_area"]].sort_values("name").to_string())
pool.to_file(G, layer="bdot_errand_pool", driver="GPKG")
