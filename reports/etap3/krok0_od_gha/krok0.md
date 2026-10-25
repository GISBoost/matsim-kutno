# Krok 0 etapu 3: estymacja O-D na GitHub Actions

Data: 2026-10-25. Workflow `.github/workflows/matsim-od.yml` (run 40184363242, [link](https://github.com/GISBoost/matsim-kutno/actions/runs/40184363242)), wejścia `scenarios/kutno_od/` (config, `plans_k1.xml.gz` = `plans_g3r91k1_25pct`, `features.gpkg`) i `scenarios/kutno/area/gminy_powiat.gpkg` (gminy powiatu z BREC; `background_od.py` i `od_warnings.py` czytają tę kopię, gdy istnieje, bo `data/raw` jest poza gitem; lokalnie wynik identyczny bajt w bajt).

Przebieg: 3 runy MATSim bez tła (25%, 50 it., 9,5–12,7 min) → 6 estymacji (lcv, heavy × p0, p1, p2) po 26–39 s → `od_warnings.py` (0 flag we wszystkich 3 wariantach). Całość ok. 25 min. Użycie: Actions → matsim-od → Run workflow (tag, compare, iterations); wynik w artefakcie `od-macierze-<tag>`, commit macierzy robi człowiek.

## Zgodność z macierzami lokalnymi R9.1
- **Runy MATSim: identyczne z lokalnymi** (natężenia modelu bez tła na licznikach np. 4 038,67 / 2 954,67 / 930,67 / 254,67 w obu).
- **Macierze O-D nie są bajt w bajt** (`porownanie.txt`: wszystkie RÓŻNA), choć ten sam kod lokalnie dał identyczny plik. Estymacja losuje punkty gmin (`rng.choice` wagą powierzchni), więc inna platforma (Linux/Windows, GDAL/GEOS) zmienia losowanie. Sumy: lekkie 47 857 vs 47 916 (−0,12%), ciężkie 19 361 vs 19 368 (−0,04%); pary różnią się do 190 podróży/dobę (lekkie), dopasowanie do liczników GPR jednakowe (np. 10044: 3 503,5 vs 3 503,5).
- Wniosek: różnica to szum losowania punktów, rzędu wariantów p1/p2 (seed punktów). R9.1 zostaje z macierzami lokalnymi `background_od_r91_*`; kolejne estymacje (krok 3, 4) robić na GHA, a nie porównywać bajt w bajt z macierzami z Windows.
