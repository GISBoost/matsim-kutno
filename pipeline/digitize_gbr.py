"""D10: rozkład godzin wyjazdu dom -> praca z GBR Gdańsk 2022, Raport 3a, Rys. 46 (s. 36).

Wykres w PDF jest wektorowy: punkty danych = końce segmentów Béziera krzywej „dom - praca”
(linia ciągła, kolor RGB 0.2/0.396/0.541). Oś Y kalibrowana z poziomych linii siatki (0–65%, co 5).
Uruchom: uv run python pipeline/digitize_gbr.py
Wyjście: config/departure_home_work_gbr2022.csv (from_h, to_h, share_pct).
"""
import csv

import pymupdf

PDF, PAGE = "data/raw/gbr/GBR2022_raport3a.pdf", 36
BINS = [(0, 5)] + [(h, h + 1) for h in range(5, 20)] + [(20, 24)]  # etykiety osi X: 0:00-4:59 ... 20:00-23:59
COLOR = [0.2, 0.396, 0.541]

dr = pymupdf.open(PDF)[PAGE - 1].get_drawings()
chart = [x for x in dr if x["rect"].y1 < 340 and len(x["items"]) > 3 and x["color"]]
grid_y = sorted({i[1].y for g in chart if g["color"][0] > 0.8 for i in g["items"]
                 if i[0] == "l" and abs(i[1].y - i[2].y) < 0.01})
assert len(grid_y) == 13, grid_y  # 65, 60, ..., 5 (linia 0 to oś)
step = (grid_y[-1] - grid_y[0]) / 12  # 5 pp
y0 = grid_y[-1] + step  # poziom 0%
curve = [x for x in chart if [round(c, 3) for c in x["color"]] == COLOR and not x["dashes"].startswith("[ ")]
assert len(curve) == 1, len(curve)
pts = [curve[0]["items"][0][1]] + [i[4] for i in curve[0]["items"]]
assert len(pts) == len(BINS)
share = [round((y0 - p.y) / step * 5, 2) for p in pts]

with open("config/departure_home_work_gbr2022.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["from_h", "to_h", "share_pct"])
    w.writerows((a, b, s) for (a, b), s in zip(BINS, share))
print(dict(zip([f"{a}-{b}" for a, b in BINS], share)), "suma", round(sum(share), 2))
