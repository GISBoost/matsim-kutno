"""K5: korytarz DK60 Objazdowa (GPR 91124) -> Bitwy pod Kutnem (91866): atrybuty sieci vs tagi OSM i select-link (skąd/dokąd ruch). Run: stała RUN."""
import io, re, gzip, sys
from collections import Counter, defaultdict
import networkx as nx
import osmium
import pandas as pd
import zstandard
from lxml import etree

RUN = "output/g5r3_25pct_s4711"
L = pd.read_csv(f"{RUN}/output_links.csv.zst", sep=";", dtype={"link": str, "from_node": str, "to_node": str}).set_index("link")
G = nx.DiGraph()
for lid, r in L.iterrows():
    G.add_edge(r.from_node, r.to_node, link=lid, t=r.length / r.freespeed)
# korytarz w obie strony: od linku 91124 do linku 91866 i odwrotnie
out = []
for a, b in (("3177068500003f", "2485778070001r"), ("2485778070001f", "2446692050004f")):
    for x, y in ((a, b),):
        p = nx.shortest_path(G, L.to_node[x], L.from_node[y], weight="t")
        chain = [x] + [G[u][v]["link"] for u, v in zip(p, p[1:])] + [y]
        out.append(chain)
ids = {int(str(int(L.origid[l]))) for c in out for l in c if pd.notna(L.origid[l])}
tags = {}
for w in osmium.FileProcessor("data/raw/osm/lodzkie-261015.osm.pbf", osmium.osm.WAY):
    if w.id in ids:
        t = w.tags
        tags[w.id] = dict(name=t.get("name"), ref=t.get("ref"), hw=t.get("highway"), maxspeed=t.get("maxspeed"), lanes=t.get("lanes"),
                          lanes_f=t.get("lanes:forward"), lanes_b=t.get("lanes:backward"), oneway=t.get("oneway"), junction=t.get("junction"))
for c in out:
    print("=== korytarz", c[0], "->", c[-1])
    rows = []
    for l in c:
        r = L.loc[l]
        tg = tags.get(int(r.origid), {}) if pd.notna(r.origid) else {}
        rows.append(dict(link=l, len=round(r.length), type=r.type, lanes=r.lanes, cap=r.capacity, v_kmh=round(r.freespeed * 3.6),
                         allowed=round(r.allowed_speed * 3.6), src=r.speed_source, vol100=r.vol_car * 4, name=tg.get("name"), ref=tg.get("ref"),
                         osm_max=tg.get("maxspeed"), osm_lanes=tg.get("lanes"), junction=tg.get("junction")))
    d = pd.DataFrame(rows)
    print(d.to_string())
    print("czas swobodny [min]", round(sum(L.length[l] / L.freespeed[l] for l in c) / 60, 2), "długość [km]", round(L.length[c].sum() / 1000, 2))

# select-link: skąd i dokąd przejeżdżający przez 91124 i 91866 (oba kierunki), wg rodzaju agenta
SEL = {"3177068500003f": "91124 N?", "2446692050004f": "91124 S?", "2485778070001r": "91866 a", "2485778070001f": "91866 b"}
pat = re.compile(r'time="([\d.]+)" type="(entered link|vehicle enters traffic|vehicle leaves traffic)"[^>]*?(?:link="([^"]+)"[^>]*vehicle="([^"]+)"|person="[^"]+" link="([^"]+)" vehicle="([^"]+)")')
trip_links = defaultdict(list)
res = defaultdict(Counter)
with zstandard.ZstdDecompressor().stream_reader(open(f"{RUN}/output_events.xml.zst", "rb")) as f:
    for line in io.TextIOWrapper(f, encoding="utf-8"):
        m = pat.search(line)
        if not m:
            continue
        typ = m[2]
        link, veh = (m[3], m[4]) if m[3] else (m[5], m[6])
        if typ == "vehicle enters traffic":
            trip_links[veh] = [link]
        elif typ == "entered link":
            trip_links[veh].append(link)
        else:
            tl = trip_links.pop(veh, [])
            for k, l in enumerate(tl):
                if l in SEL:
                    kind = veh[0]
                    od = "_".join(veh.split("_")[:-1]) if kind == "t" else kind
                    res[l][(kind, od)] += 1
                    res[l + "|prev"][tl[k - 1] if k else "-"] += 1
                    res[l + "|next"][tl[k + 1] if k + 1 < len(tl) else "-"] += 1
for l, name in SEL.items():
    tot = sum(res[l].values())
    print(f"\n=== {name} {l}: {tot * 4} poj./dobę (100%)")
    byk = Counter()
    for (k, od), n in res[l].items():
        byk[k] += n
    print("  wg rodzaju:", {k: v * 4 for k, v in byk.items()})
    print("  top relacje tła:", [(od, n * 4) for (k, od), n in res[l].most_common(40) if k == "t"][:10])
    print("  poprzedni link:", [(x, n * 4) for x, n in res[l + "|prev"].most_common(4)])
    print("  następny link:", [(x, n * 4) for x, n in res[l + "|next"].most_common(4)])
