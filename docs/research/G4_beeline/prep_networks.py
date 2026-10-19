"""G4 beeline: z PBF buduje trzy sieci liniowe (walk, bike, car) dla Kutna i parę dom-praca z planów.

Wyjście (EPSG:2180, gitignored): output/g4_beeline/{walk,bike,car}.gpkg, pairs.gpkg (dom, praca), buildings_sample.gpkg
Topologia: way jest cięty w węzłach OSM współdzielonych z innym wayem (jak w OSM), więc analiza sieciowa QGIS
łączy tylko tam, gdzie łączy OSM (mosty/tunele się nie przecinają).
Uruchom: uv run python docs/research/G4_beeline/prep_networks.py
ZAŁOŻENIA filtrów w funkcjach allowed_*; ujęte w docs/research/G4_beeline.md.
"""
import collections, gzip, re, sys
import geopandas as gpd, osmium, shapely
from shapely.geometry import LineString, Point
import pyproj

OUT = "output/g4_beeline"
PBF = "data/raw/osm/lodzkie-261015.osm.pbf"
gm = gpd.read_file("scenarios/kutno/area/gmina.geojson").to_crs(2180).geometry.union_all()
area = gm.buffer(3000)
tr = pyproj.Transformer.from_crs(4326, 2180, always_xy=True)
bb4326 = gpd.GeoSeries([area], crs=2180).to_crs(4326).total_bounds


def car_ok(t):
    hw = t.get("highway")
    if hw not in {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary",
                  "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service"}:
        return False
    return t.get("access") not in {"no", "private"} and t.get("motor_vehicle") not in {"no", "private"} and t.get("motorcar") != "no"


def walk_ok(t):
    hw = t.get("highway")
    if hw not in {"primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
                  "residential", "living_street", "service", "pedestrian", "footway", "path", "steps", "track", "cycleway", "corridor"}:
        return False
    return t.get("foot") != "no" and t.get("access") not in {"no", "private"}  # bez motorway/trunk (zakaz pieszych)


def bike_ok(t):
    hw = t.get("highway")
    bike = t.get("bicycle")
    if bike in {"no", "dismount"} or t.get("access") in {"no", "private"}:
        return False
    if hw in {"primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
              "residential", "living_street", "service", "track", "cycleway"}:
        return True
    if hw in {"path", "footway", "pedestrian"}:  # rower tylko jawnie dozwolony (footway) lub path bez zakazu
        return bike in {"yes", "designated", "permissive"} or (hw == "path" and bike is None)
    return False


def car_dir(t):
    """1 = tylko zgodnie z digitalizacją, -1 = przeciwnie, 0 = dwukierunkowo."""
    ow = t.get("oneway")
    if ow in {"yes", "1", "true"} or t.get("junction") == "roundabout" or t.get("highway") in {"motorway", "motorway_link"}:
        return 1
    if ow == "-1":
        return -1
    return 0


class Count(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.n = collections.Counter()

    def way(self, w):
        t = w.tags
        if t.get("highway") and (car_ok(t) or walk_ok(t) or bike_ok(t)):
            for nd in w.nodes: self.n[nd.ref] += 1


class Seg(osmium.SimpleHandler):
    def __init__(self, shared):
        super().__init__(); self.shared = shared
        self.rows = {"walk": [], "bike": [], "car": []}
        self.bbox = shapely.box(*bb4326)

    def way(self, w):
        t = w.tags
        if not t.get("highway"): return
        modes = [m for m, f in (("walk", walk_ok), ("bike", bike_ok), ("car", car_ok)) if f(t)]
        if not modes: return
        try:
            pts = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if len(pts) < 2 or not self.bbox.intersects(LineString(pts)): return
        refs = [n.ref for n in w.nodes]
        cuts = [0] + [i for i in range(1, len(refs) - 1) if self.shared[refs[i]] > 1] + [len(refs) - 1]
        for a, b in zip(cuts, cuts[1:]):
            xs, ys = tr.transform([p[0] for p in pts[a:b + 1]], [p[1] for p in pts[a:b + 1]])
            g = LineString(zip(xs, ys))
            for m in modes:
                self.rows[m].append({"way": w.id, "hw": t.get("highway"), "dir": car_dir(t) if m == "car" else 0,
                                     "geometry": g})


c = Count(); c.apply_file(PBF, locations=False)
s = Seg(c.n); s.apply_file(PBF, locations=True)
for m, rows in s.rows.items():
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=2180)
    g = g[g.intersects(area)]
    g.to_file(f"{OUT}/{m}.gpkg", driver="GPKG")
    print(m, len(g), round(g.length.sum() / 1000, 1), "km")

# pary dom-praca z planów 100% (mieszkańcy, obie aktywności w gm. Kutno)
txt = gzip.open("scenarios/kutno/plans_100pct.xml.gz", "rt", encoding="utf-8").read()
rows = []
for m in re.finditer(r'<person id="([^"]+)">.*?name="kind"[^>]*>(\w+)<.*?<activity type="home"[^>]*x="([\d.]+)" y="([\d.]+)".*?<activity type="work"[^>]*x="([\d.]+)" y="([\d.]+)"', txt, re.S):
    rows.append((m.group(1), m.group(2), *map(float, m.groups()[2:])))
df = gpd.pd.DataFrame(rows, columns=["id", "kind", "hx", "hy", "wx", "wy"])
home = gpd.GeoSeries([Point(x, y) for x, y in zip(df.hx, df.hy)], crs=2180)
work = gpd.GeoSeries([Point(x, y) for x, y in zip(df.wx, df.wy)], crs=2180)
df = df[home.within(gm).values & work.within(gm).values & (df.kind == "resident").values]
print("pary dom-praca w gminie:", len(df), "z", len(rows))
df["euclid"] = ((df.hx - df.wx) ** 2 + (df.hy - df.wy) ** 2) ** 0.5
df.to_csv(f"{OUT}/pairs.csv", index=False)
print(df.euclid.describe())
