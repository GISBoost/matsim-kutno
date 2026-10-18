"""G5: składa docs/research/G5_walidacja.md z szablonu, tabel (csv) i wierszy manifestu (sha256 liczone z plików)."""
import hashlib
import os

import pandas as pd

OUT = "reports/etap2/g5_walidacja/"
VAL = "scenarios/kutno/validation/"  # wejścia innych skryptów (punkty GPR, czasy GUS)
A = "https://www.gov.pl/attachment/"
S = "https://www.archiwum.gddkia.gov.pl/frontend/web/userfiles/articles/s/stacje-ciaglych-pomiarow-ruchu-d_41706/"
URLS = {
    "gpr2025/dk_wykaz.xlsx": A + "b3083bea-6336-45a9-b304-df68e95a3cb3",
    "gpr2025/dk_sdrr.xlsx": A + "28194e66-2fb2-4dd7-becf-fedcf2b26908",
    "gpr2025/dk_sdrdr.xlsx": A + "a6686f5b-db6d-4077-b37b-b7758ffa805b",
    "gpr2025/dk_sdrl.xlsx": A + "364315a0-b9bd-4b18-a622-90697f60d66d",
    "gpr2025/dk_odcpom_web.zip": A + "7f8ca805-e384-4802-bf10-d36538e6ef84",
    "gpr2025/dw_wykaz.xlsx": A + "866ec42e-25fe-41f1-9693-17712d7b0e38",
    "gpr2025/dw_sdrr.xlsx": A + "17ff216a-615f-4593-afa9-e62d5bffc738",
    "gpr2025/ruch_drogowy_2025.pdf": A + "8d1e9123-12e8-4611-8397-d5b129e7630a",
    "gpr2025/rozklady_srodowiskowe.pdf": A + "52b2e6d3-7104-4f1d-baa1-73ef172310ca",
    "gpr2025/dw_synteza.pdf": A + "5b21e9c5-40f5-41c3-ae84-f0479b275669",
    "scpr2025/r02_04.pdf": A + "3b78214f-a760-4336-a669-981d4c13978b",
    "scpr2025/r02_05.pdf": A + "4a8942cd-2508-4448-b215-02d45a1f8376",
    "scpr2025/r02_06.pdf": A + "dd721b73-833d-462d-b44a-f7591ef0d0df",
    "scpr2025/karta_lodz.pdf": S + "LODZ/2025/R00_02_10_2025.pdf",
    "scpr2025/st_10617.pdf": S + "LODZ/2025/10617_2025.pdf",
    "scpr2025/st_10636.pdf": S + "LODZ/2025/10636_2025.pdf",
    "scpr2025/st_14005.pdf": S + "WARSZAWA/2025/14005_2025.pdf",
    "scpr2025/st_30025.pdf": S + "POZNAN/2025/30025_2025.pdf",
    "lit/MUM25_paper_3_Ewert.pdf": "https://matsim.org/conferences/mum2025/abstracts/MUM25_paper_3.pdf",
    "lit/ewert_slides.pdf": "https://matsim.org/conferences/mum2025/presentations/ewert.pdf",
    "lit/lu2022_longhaul_freight.pdf": "https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2022/22-02/LuEtAl2022LongHaulFreightGER_submitted.pdf",
    "lit/rakow2024_berlin_commercial.pdf": "https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2024/24-22/RakowEtAl_MATSimBerlinEWGT.pdf",
    "lit/ziemke2019_openberlin.pdf": "https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2019/19-01/ZiemkeEtAl2019OpenBerlinScenarioVSPWP.pdf",
}


def f0(x):
    return "" if pd.isna(x) else f"{x:.0f}"


m = pd.read_csv(VAL + "gpr_linki.csv")
rows = []
for nr, d in m.groupby("nr", sort=False):
    r = d.iloc[0]
    lk = "<br>".join(f"`{x.link}` ({x.osm_type}, {x.dist_m:.0f} m, {x.sdrr_kier:.0f})" for x in d.itertuples())
    rows.append(f"| {r.klasa} {r.droga} | {nr} | {r.nazwa[:70]} | {r.miejsc} | {f0(r.sdr)} | {f0(r.sdrdr)} | {f0(r.sdrl)} | {f0(r.lekkie_osob)} | {100 * r.ciez_udzial:.0f}% | {lk} |")

t = pd.read_csv(VAL + "gus_vs_siec.csv")
g = ["| gmina (TERYT) | odl. centroid–węzeł [m] | GUS [min] | sieć [min] | sieć/GUS | GUS [km] | sieć [km] | v GUS [km/h] | v sieć [km/h] |", "|---|---|---|---|---|---|---|---|---|"]
for r in t.itertuples():
    g.append(f"| {r.gmina} ({r.teryt}) | {r.snap_m} | {r.gus_min:.1f} | {r.siec_min:.1f} | {r.czas_ratio:.2f} | {r.gus_km:.1f} | {r.siec_km:.1f} | {r.v_gus_kmh:.0f} | {r.v_siec_kmh:.0f} |")

man = []
for rel, url in URLS.items():
    p = "data/raw/g5/" + rel
    b = open(p, "rb").read()
    man.append(f"{p},{url},2026-10-17,{len(b)},{hashlib.sha256(b).hexdigest()}")

s = open(OUT + "szablon.md", encoding="utf8").read()
s = s.replace("{{TAB_GPR}}", "\n".join(rows)).replace("{{TAB_GUS}}", "\n".join(g)).replace("{{MANIFEST}}", "\n".join(man))
os.makedirs("docs/research", exist_ok=True)
open("docs/research/G5_walidacja.md", "w", encoding="utf8").write(s)
print(len(rows), "odcinków,", len(g) - 2, "gmin,", len(man), "plików w manifeście")
