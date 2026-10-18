# reports/: spis

Każdy folder to jedna faza. Raport główny to plik `.md` w folderze. Obok leżą dowody: `.json` (testy i liczby), `.png` (wykresy) i `.log` (logi poleceń).

| folder | co zawiera | raport |
|---|---|---|
| `f0_env/` | środowisko, build, run equil | `f0_env.md` |
| `f1_smoke/` | sieć syntetyczna, 10 agentów (test regresyjny) | `f1_smoke.md` |
| `f2_network/` | obszar i sieć z OSM | `f2_network.md` |
| `f3_demand/` | popyt z GUS: pracujący per obwód, przyjeżdżający | `f3_demand.md` |
| `f4_plans/` | plany 10% (domy, praca, godziny) | `f4_plans.md` |
| `f5_run_10pct/` | pierwszy run 10%, 20 it. (przed naprawami R3) | `f5_run.md` |
| `f6_run_100pct/` | run 100%, 20 it. (przed naprawami R3) | `f6_run.md` |
| `r3_ocena/` | ocena modelu i naprawy, runy 100 it. | niżej |
| `g6_kolejki/` | **wyniki referencyjne (25%, 3 seedy) w `d18_25pct/`**: diagnoza kolejek z G6, test stuckTime/kinematicWaves, poprawka D18 | `g6_kolejki.md` |
| `g2_miejsca_pracy/` | wyniki 25% po D17 w `B_25pct/` (przed D18); porównanie B (22 725, baza) i C (17 486) na 10%, wyjeżdżający O1 | `g2_miejsca_pracy.md` |
| `d16_przyjezdzajacy/` | wyniki 25%, 3 seedy po D16 (przed D17): wjazd o godzinie z profilu, odcięcie gmin > 100 km | `d16_przyjezdzajacy.md` |
| `g5_walidacja/` | punkty GPR przypisane do linków (`gpr_linki.csv` to **wejście kodu**, nie przenosić) | – |
| `g5_kalibracja/` | runy R1–R5 vs GPR, czasy GUS, PCE, decyzja R4/R5 | `g5_r3.md` … `g5_r5.md`, `g5_r4_vs_r5_decyzja.md` |
| `audyt_g5/` | audyt G5 i poprawki D21 (`k1/`, `k2/`) | `audyt_g5.md`, **`plan_poprawek.md`** |
| `g3_domy/`, `g4_beeline/`, `g6_blender/` | materiały robocze faz G3, G4 i G6 (opisy w `docs/research/`) | – |

Przegląd faz i dalszych planów: [`../ROADMAP.md`](../ROADMAP.md).

Folder `r3_ocena/`:

| podfolder / plik | co zawiera |
|---|---|
| `wyniki_25pct/` | wyniki przed D16: 3 seedy, zbieżność, opóźnienia, select-link DK92. Raport: `r3_25pct.md` |
| `wyniki_10pct/` | 3 seedy 10%, do porównania |
| `r3_10_vs_25pct.md` (+ `.json`/`.png`) | porównanie próbek 10% i 25% |
| `run_100pct_przerwany/` | run 100% przerwany na prośbę użytkownika (dowód `stuckAndAbort` przy endTime 36:00) |
| `testy/` | build, test storage ≠ flow (odrzucony przez MATSim 2026) |

Analiza metodyczna jest w `docs/research/` (`R3_ocena_modelu.md`, `R3_recenzja_agenta.md`).

Pliki z folderów f5 i f6 pochodzą sprzed napraw R3. Nie porównuj ich liczb wprost z `r3_ocena/`.
