"""F4: walidacja plans.xml.gz + mapa kontrolna.

Użycie: uv run python -W ignore pipeline/validate_plans.py scenarios/kutno/plans.xml.gz
Test (TASKS F4): każda osoba ma dokładnie home-car-work-car-home; współrzędne w obszarze sieci; praca w gminie Kutno;
liczba osób = round(sample x (pracujący w Kutnie + przyjeżdżający)); ten sam sha256 po ponownym uruchomieniu plans.py.
Wyjście: reports/f4_plans.json, reports/f4_plans.png. Kod 1, gdy test nie przechodzi.
"""
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd
from lxml import etree
from shapely.geometry import Point

matplotlib.use("Agg")
import matplotlib.pyplot as plt

path = Path(sys.argv[1])
P = tomllib.loads(Path("config/kutno.toml").read_text(encoding="utf-8"))["plans"]
f3 = json.load(open("reports/f3_demand.json", encoding="utf-8"))
area = gpd.read_file("scenarios/kutno/area/network_area.geojson").geometry.iloc[0]
gmina = gpd.read_file("scenarios/kutno/area/gmina.geojson").geometry.iloc[0]
powiat = gpd.read_file("scenarios/kutno/area/powiat.geojson").geometry.iloc[0]

persons, bad_chain = [], []
with gzip.open(path, "rb") as f:
    for _, el in etree.iterparse(f, tag="person"):
        plans = el.findall("plan")
        seq = [c.get("type") if c.tag == "activity" else c.get("mode") for c in plans[0]] if len(plans) == 1 else []
        acts = plans[0].findall("activity") if plans else []
        timing_ok = (len(acts) == 3 and acts[0].get("end_time") and not acts[0].get("max_dur")
                     and acts[1].get("max_dur") and not acts[1].get("end_time"))
        if seq != ["home", "car", "work", "car", "home"] or not timing_ok:
            bad_chain.append(el.get("id"))
        else:
            h, w = (Point(float(a.get("x")), float(a.get("y"))) for a in acts[:2])
            persons.append(dict(id=el.get("id"), h=h, w=w, same_home=acts[0].get("x") == acts[2].get("x")
                                and acts[0].get("y") == acts[2].get("y")))
        el.clear()

df = pd.DataFrame(persons)
expected = round(P["sample"] * f3["agents_100pct"][P["variant"]])
sha = hashlib.sha256(path.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as d:
    subprocess.run([sys.executable, "-W", "ignore", "pipeline/plans.py", str(Path(d) / "plans.xml.gz")], check=True,
                   capture_output=True)
    sha2 = hashlib.sha256((Path(d) / "plans.xml.gz").read_bytes()).hexdigest()

meta = pd.read_csv(path.parent / "plans_meta.csv")
meta["dist_km"] = ((meta.home_x - meta.work_x) ** 2 + (meta.home_y - meta.work_y) ** 2) ** .5 / 1000
report = {
    "plans": str(path), "sha256": sha, "sha256_rerun": sha2, "deterministic": sha == sha2,
    "persons": len(df) + len(bad_chain), "expected": expected, "bad_chain": bad_chain[:10], "bad_chain_n": len(bad_chain),
    "home_outside_area": int((~df.h.apply(area.contains)).sum()),
    "work_outside_gmina": int((~df.w.apply(gmina.contains)).sum()),
    "return_home_differs": int((~df.same_home).sum()),
    "by_kind": meta.kind.value_counts().to_dict(),
    "home_source": meta.home_src.str.split("_").str[0].value_counts().to_dict(),
    "random_point_homes_keys": sorted(meta[meta.home_src == "random_point"].key.astype(str).unique().tolist()),
    "distinct_work_buildings": int(meta.work_src.nunique()),
    "top5_work_buildings_share": round(meta.work_src.value_counts().head(5).sum() / len(meta), 3),
    "entry_links_used": meta[meta.home_src == "entry"].groupby("home_link").size().sort_values(ascending=False).to_dict(),
    "home_work_crowfly_km_median": {k: round(v, 1) for k, v in meta.groupby("kind").dist_km.median().items()},
    "times": {"home_end_time": P["home_end_time"], "work_max_dur": P["work_max_dur"], "status": "ZAŁOŻENIE (D10)"},
}
report["ok"] = (report["deterministic"] and not bad_chain and report["persons"] == expected
                and report["home_outside_area"] == 0 and report["work_outside_gmina"] == 0 and report["return_home_differs"] == 0)
json.dump(report, open("reports/f4_plans.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# --- mapa: domy, praca, wjazdy -------------------------------------------------------------------------
fig = plt.figure(figsize=(16, 8))
ax = fig.add_axes([0.01, 0.05, 0.47, 0.86])
gpd.GeoSeries([area]).boundary.plot(ax=ax, color="0.6", lw=1, ls="--")
gpd.GeoSeries([powiat]).boundary.plot(ax=ax, color="0.3", lw=1.2)
gpd.GeoSeries([gmina]).plot(ax=ax, color="#fde9c9", edgecolor="#c47f17", lw=1)
for kind, col in (("resident", "#2e86ab"), ("commuter", "#7b2cbf")):
    m = meta[(meta.kind == kind) & (meta.home_src != "entry")]
    ax.scatter(m.home_x, m.home_y, s=3, color=col, alpha=0.5, label=f"dom: {'mieszkaniec' if kind == 'resident' else 'przyjeżdżający z powiatu'} ({len(m)})")
e = meta[meta.home_src == "entry"].groupby(["home_x", "home_y"]).size().reset_index(name="n")
ax.scatter(e.home_x, e.home_y, s=e.n * 4, color="#d1495b", edgecolor="k", lw=0.5, zorder=5,
           label=f"wjazd spoza powiatu ({int(e.n.sum())} os., {len(e)} punktów)")
for r in e.itertuples():
    ax.annotate(str(r.n), (r.home_x, r.home_y), xytext=(5, 3), textcoords="offset points", fontsize=7, color="#d1495b")
ax.set_aspect("equal"); ax.set_axis_off(); ax.legend(loc="lower left", fontsize=8)
ax.set_title("domy agentów i punkty wjazdu", fontsize=10)

ax2 = fig.add_axes([0.5, 0.3, 0.3, 0.62])
gpd.GeoSeries([gmina]).plot(ax=ax2, color="#fde9c9", edgecolor="#c47f17", lw=1)
wc = meta.groupby(["work_x", "work_y"]).size().reset_index(name="n")
ax2.scatter(wc.work_x, wc.work_y, s=wc.n * 2, color="#f18f01", alpha=0.6, edgecolor="k", lw=0.2)
ax2.set_aspect("equal"); ax2.set_axis_off()
ax2.set_title(f"miejsca pracy w Kutnie: {report['distinct_work_buildings']} budynków\n"
              f"(wielkość = liczba agentów; top 5 budynków = {report['top5_work_buildings_share']:.0%})", fontsize=10)

ax3 = fig.add_axes([0.84, 0.55, 0.14, 0.35])
for kind, col in (("resident", "#2e86ab"), ("commuter", "#7b2cbf")):
    ax3.hist(meta[meta.kind == kind].dist_km, bins=range(0, 41), color=col, alpha=0.6, label=kind)
ax3.set_title("odl. dom-praca w linii prostej [km]", fontsize=9); ax3.legend(fontsize=7); ax3.tick_params(labelsize=7)
ax4 = fig.add_axes([0.81, 0.08, 0.14, 0.35]); ax4.set_axis_off()
ax4.text(0, 1, "\n".join([
    f"osoby: {report['persons']} (oczekiwane {expected})",
    f"łańcuch h-car-w-car-h: {'OK' if not bad_chain else len(bad_chain)}",
    f"domy poza obszarem: {report['home_outside_area']}",
    f"praca poza gm. Kutno: {report['work_outside_gmina']}",
    f"sha256 powtórzony: {'OK' if report['deterministic'] else 'RÓŻNY'}",
    f"domy losowe (brak bud.): {report['home_source'].get('random', 0)}",
    f"godziny: wyjazd {P['home_end_time']}, praca {P['work_max_dur']}",
    "(ZAŁOŻENIE D10)",
]), va="top", fontsize=8, family="monospace")
fig.suptitle(f"F4 plans {P['sample']:.0%} ({P['variant']}) | {'ZALICZONA' if report['ok'] else 'NIE ZALICZONA'}", fontsize=12)
fig.savefig("reports/f4_plans.png", dpi=120)
print(json.dumps(report, indent=1, ensure_ascii=False))
sys.exit(0 if report["ok"] else 1)
