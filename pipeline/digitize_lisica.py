"""D19/K3-2: godzinowy profil ruchu dnia roboczego, stacja SCPR 14005 Lisica (DK60c Kutno–Gostynin), 2025.

Źródło: data/raw/g5/scpr2025/st_14005.pdf, s. 9, R03_04-1 (pojazdy lekkie) i R03_04-2 (ciężkie), „Uśrednione dobowe rozkłady ruchu”.
Wykresy są wektorowe: krzywa „Dni robocze” = łamana 24 punktów w kolorze legendy (RGB 0.267/0.447/0.769).
Oś Y kalibrowana z poziomych linii siatki i osi (0 % na osi X, krok 1 %).
Uruchom: uv run python pipeline/digitize_lisica.py
Wyjście: config/hourly_profile_lisica2025.csv (hour_from, light_pct, heavy_pct).
"""
import csv

import pymupdf

PDF, PAGE = "data/raw/g5/scpr2025/st_14005.pdf", 9
WORKDAY = [0.267, 0.447, 0.769]
page = pymupdf.open(PDF)[PAGE - 1]
dr = page.get_drawings()


def curve(top, bottom):
    """Krzywa dni roboczych w pasie y ∈ [top, bottom] i jej kalibracja z siatki."""
    inside = [x for x in dr if top <= x["rect"].y0 and x["rect"].y1 <= bottom]
    grid = sorted({round(i[1].y, 2) for x in inside if x["color"] and round(x["color"][0], 3) == 0.537
                   for i in x["items"] if i[0] == "l" and abs(i[1].y - i[2].y) < 0.01 and i[2].x - i[1].x > 100})
    step = (grid[-1] - grid[0]) / (len(grid) - 1)  # 1 % na kreskę siatki; ostatnia (najniższa) linia to oś 0 %
    c = [x for x in inside if x["color"] and [round(v, 3) for v in x["color"]] == WORKDAY and len(x["items"]) == 23]
    assert len(c) == 1, len(c)
    pts = [c[0]["items"][0][1]] + [i[2] for i in c[0]["items"]]
    assert len(pts) == 24 and all(pts[k].x < pts[k + 1].x for k in range(23))
    return [round((grid[-1] - p.y) / step, 3) for p in pts], len(grid)


light, n1 = curve(230, 420)   # R03_04-1, oś 0–9 %
heavy, n2 = curve(490, 670)   # R03_04-2, oś 0–8 %
assert (n1, n2) == (10, 9), (n1, n2)  # linie siatki 1..9 % + oś (lekkie), 1..8 % + oś (ciężkie)
with open("config/hourly_profile_lisica2025.csv", "w", newline="\n", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["hour_from", "light_pct", "heavy_pct"])
    w.writerows((h, l, hv) for h, (l, hv) in enumerate(zip(light, heavy)))
print("lekkie", light, "suma", round(sum(light), 2))
print("ciężkie", heavy, "suma", round(sum(heavy), 2))
