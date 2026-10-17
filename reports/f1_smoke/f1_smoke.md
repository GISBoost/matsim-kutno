# F1 — smoke test, 10 agentów na sieci syntetycznej (2026-10-16)

**Status: ZALICZONA**

Wejścia: `scenarios/smoke/` (4 węzły po przekątnej w EPSG:2180 koło Kutna, 6 linków car, 10 osób `home 07:00 → car → work dur 8 h → car → home`, plany bez linków i tras), `coordinateSystem = EPSG:2180`.
Polecenie: `java -Xmx10g -jar matsim\matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios\smoke\config.xml --output output\f1_smoke --iterations 1`. Kod wyjścia 0, 7 s, log w `reports/f1_smoke/f1_smoke_run.log`.

| Test | Oczekiwane | Wynik |
|---|---|---|
| nogi car (`departure` legMode=car) | 20 | 20 |
| `vehicle enters traffic` / `leaves traffic` | 20 / 20 | 20 / 20 |
| departure = arrival, per osoba | tak | tak |
| stuck | 0 | 0 |
| osoby z podróżami | 10 | 10 |
| współrzędne aktywności w outpucie | E 523 500 / 525 500, N 484 250 / 485 250 | identyczne z wejściem, **bez zamiany osi** |
| dowiązanie do linków | najbliższe | home → AB, work → CD |
| pierwsza podróż | 07:00, 2 × 1 118 m | 07:00:00, 2 236 m, 3:01 min |
| koniec pracy | ≈ 07:03 + 8 h | 54 163 s = 15:02:43 |

Walidator: `reports/f1_smoke/f1_smoke_events.json` (`ok: true`).
Ostrzeżenia w `logfileWarningsErrors.log` są informacyjne (brak randomizacji routingu, `usePersonIdForMissingVehicleId`). Ewentualną decyzję o nich podejmiemy w F5.
