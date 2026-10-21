"""D23 krok 3: sieć R7 vs R6. Te same id węzłów i linków, geometria i atrybuty, różni się tylko freespeed (i speed_group).
Użycie: uv run python reports/etap2/g5_predkosci_d23/check_network_r7.py <network_r6> <network_r7>"""
import gzip, sys, collections
import xml.etree.ElementTree as ET

def load(p):
    r = ET.parse(gzip.open(p)).getroot()
    nodes = {n.get("id"): (n.get("x"), n.get("y")) for n in r.iter("node")}
    links = {}
    for l in r.iter("link"):
        at = {a.get("name"): (a.text or "").strip() for a in l.iter("attribute")}
        links[l.get("id")] = dict(l.attrib, **at)
    return nodes, links

n6, l6 = load(sys.argv[1]); n7, l7 = load(sys.argv[2])
assert n6 == n7, "węzły różne"
assert l6.keys() == l7.keys(), "id linków różne"
diff = collections.Counter(); grp = collections.defaultdict(list)
for i, a in l6.items():
    b = l7[i]
    for k in set(a) | set(b):
        if k in ("freespeed", "speed_group"): continue
        if a.get(k) != b.get(k): diff[k] += 1
    g = b.get("speed_group", "boundary"); grp[g].append(float(b["freespeed"]) / float(a["freespeed"]))
print(f"węzły {len(n6)}, linki {len(l6)}; różnice w atrybutach poza freespeed/speed_group: {dict(diff) or 'brak'}")
for g, v in sorted(grp.items()):
    print(f"grupa {g}: linków {len(v)}, freespeed R7/R6 min {min(v):.3f} maks {max(v):.3f}")
assert not diff
