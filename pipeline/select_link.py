"""Select-link: skąd i dokąd jadą pojazdy przejeżdżające przez wybrane linki (np. DK92 Sklęczkowska).

Użycie: uv run python pipeline/select_link.py <output_dir> <plans_meta.csv> <out_prefix> <link_id> [link_id ...]
Wyjście: <out_prefix>.json (źródła wg gminy/obwodu, cele wg budynku, godziny) i <out_prefix>.png (trasy tych pojazdów).
"""
import collections
import json
import sys
from pathlib import Path

import matplotlib
import pandas as pd
import zstandard
from lxml import etree

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # mapy w ciemnym motywie (prośba użytkownika)

out_dir, meta_csv, prefix, sel = Path(sys.argv[1]), sys.argv[2], sys.argv[3], set(sys.argv[4:])
z = lambda p: zstandard.ZstdDecompressor().stream_reader(open(p, "rb"))
meta = pd.read_csv(meta_csv, dtype={"key": str}).set_index("person")

nodes, links = {}, {}
for _, el in etree.iterparse(z(out_dir / "output_network.xml.zst"), tag=("node", "link")):
    if el.tag == "node":
        nodes[el.get("id")] = (float(el.get("x")), float(el.get("y")))
    else:
        links[el.get("id")] = (el.get("from"), el.get("to"))
    el.clear()
assert sel <= links.keys(), sel - links.keys()

# trasy nóg: pojazd (= osoba) -> lista linków bieżącej nogi; zapisujemy nogi, które przecięły wybrane linki
route, start, hits, legno = collections.defaultdict(list), {}, [], collections.Counter()
for _, el in etree.iterparse(z(out_dir / "output_events.xml.zst"), tag="event"):
    t, v = el.get("type"), el.get("vehicle")
    if t == "vehicle enters traffic":
        route[v] = [el.get("link")]
        start[v] = float(el.get("time"))
        legno[v] += 1
    elif t == "entered link":
        route[v].append(el.get("link"))
    elif t == "vehicle leaves traffic":
        if sel & set(route[v]):
            hits.append((v, start[v], route[v], "do pracy" if legno[v] == 1 else "z pracy"))
        route.pop(v)
    el.clear()

persons = [meta.loc[v] for v, _, _, _ in hits]
src = collections.Counter(f"{p.kind}:{p.key}" for p in persons)
vol = collections.Counter(l for _, _, r, _ in hits for l in r)
report = {
    "links": sorted(sel), "legs": len(hits), "persons": len({h[0] for h in hits}),
    "by_direction": dict(collections.Counter(h[3] for h in hits)),
    "by_kind": dict(collections.Counter(p.kind for p in persons)),
    "top_sources": src.most_common(15),
    "top_work_buildings": collections.Counter(p.work_src for p in persons).most_common(10),
    "by_hour": dict(sorted(collections.Counter(int(h[1] // 3600) for h in hits).items())),
}
json.dump(report, open(prefix + ".json", "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=str)

fig, ax = plt.subplots(figsize=(10, 9))
vmax = max(vol.values())
for lid, (a, b) in links.items():
    (x1, y1), (x2, y2) = nodes[a], nodes[b]
    v = vol.get(lid, 0)
    ax.plot([x1, x2], [y1, y2], color="#d1495b" if v else "0.3", lw=0.3 + 5 * v / vmax, zorder=2 if v else 1)
for lid in sel:
    (x1, y1), (x2, y2) = nodes[links[lid][0]], nodes[links[lid][1]]
    ax.plot([x1, x2], [y1, y2], color="#00e5ff", lw=4, zorder=3)
ax.set_aspect("equal"); ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=7)
ax.set_title(f"select-link: {len(hits)} nóg przez {len(sel)} wybrane linki (czarne); grubość = ile z nich jedzie linkiem",
             fontsize=9)
fig.tight_layout(); fig.savefig(prefix + ".png", dpi=120)
print(json.dumps({k: report[k] for k in ("legs", "persons", "by_kind", "by_direction")}, ensure_ascii=False))
