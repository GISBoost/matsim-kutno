# F5 — run integracyjny 10% (2026-10-16)

**Status: ZALICZONA** (test zdarzeń). Ocena „czy to ma sens dla Kutna” należy do człowieka (CLAUDE.md).

Polecenie (z katalogu projektu):

```
java -Xmx10g -jar matsim/matsim-example-project-0.0.1-SNAPSHOT.jar run --config scenarios/kutno/config_10pct.xml
```

- Wynik: kod 0, ok. 2,5 min, 20 iteracji.
- Log: `reports/f5_run.log`. Jedyny wyjątek w logu to nieszkodliwe ostrzeżenie Guice/ASM.
- Output: `output/f5_10pct/`.

| Test | Wynik |
|---|---|
| departure car = arrival = 2N | 5 146 = 2 × 2 573 (`reports/f5_events.json`, `check_events.py --expect-car-legs 5146`) |
| stuck | 0 |
| każda osoba: odjazdy = przyjazdy | 2 573/2 573 |
| udział car (`modestats.csv`) | 1,0 we wszystkich iteracjach (D6) |

## Config (`scenarios/kutno/config_10pct.xml`)

- `flowCapacityFactor = storageCapacityFactor = 0,1` (D8), seed 4711, `qsim.endTime` 36:00 (ostatni przedział wyjazdów 20–24 + 8 h).
- Strategie: ChangeExpBeta 0,8 + ReRoute 0,2. Innowacja jest wyłączana po 80% iteracji.
- **Bez TimeAllocationMutator**, bo godziny wyjazdu pochodzą ze źródła (D14) i nie powinny dryfować.
- Scoring: home 16 h, work 8 h, bez godzin otwarcia. To ZAŁOŻENIE: score jest tylko diagnostyką, a parametry scoringu to decyzja otwarta.

## Godziny wyjazdu (D14)

GBR Gdańsk 2022, Raport 3a, Rys. 46, seria „dom - praca”. Wykres w PDF jest wektorowy, więc wartości to dokładne punkty krzywej (`pipeline/digitize_gbr.py`), a nie odczyt „na oko”. Wynik: `config/departure_home_work_gbr2022.csv`.

| przedział | 0–5 | 5–6 | 6–7 | 7–8 | 8–9 | 9–10 | 10–11 | 11–20 | 20–24 |
|---|---|---|---|---|---|---|---|---|---|
| % | 1,3 | 10,0 | 25,7 | 32,3 | 16,3 | 6,6 | 2,1 | 5,4 | 0,4 |

Suma odczytu to 100,17%, normalizowana do 100%. Wewnątrz przedziału rozkład jest jednostajny (ZAŁOŻENIE).

## Wyniki (iteracja 20)

| | mieszkańcy | przyjeżdżający |
|---|---|---|
| podróże | 3 524 | 1 622 |
| czas podróży, mediana (z dojściem pieszym) | 17,3 min | 25,6 min |
| p90 | 42,1 min | 41,8 min |
| dystans, mediana | 6,2 km | 17,7 km |

- Noga car: mediana 16,3 min, mediana prędkości 35,6 km/h. Dojście i odejście piesze: mediana 1,7 min, maks. 28,5 min (dom/praca daleko od drogi w sieci).
- Mediana prędkości car według godziny wyjazdu: 44 km/h o 5:00, **27 km/h o 7:00**, 41 km/h o 9:00, 34 km/h o 15:00, **26 km/h o 17:00**. Szczyty są widoczne.
- Score (avg executed): 114,2 w iteracji 0, 133,2 w 10 i 134,7 w 20. Stabilizuje się po wyłączeniu innowacji.

## Kongestia (`pipeline/link_delay.py` → `reports/f5_delay.json`, `.png`)

- Opóźnienie względem czasu swobodnego wynosi łącznie 624 poj.-h, średnio 7,3 min na nogę car. Prawie całość przypada na 6–9 i 14–18.
- Największe opóźnienia leżą na jednym ciągu dróg primary na SE od centrum (okolice E 526 000, N 483 500).
  - Około 685 pojazdów, czyli ok. 6 850 przy 100%.
  - Średnio 3–8 min opóźnienia na linku.
  - To dojazd do wschodniej strefy pracy (duże hale z F4). Drugi odcinek leży przy węźle z A1 (E 531 000, N 485 500).
- Możliwe przyczyny (do oceny, nie wniosek):
  - **D6** (wszyscy autem, ruch zawyżony).
  - **D7** (waga powierzchni hal kieruje dużo pracy na wschód).
  - Capacity domyślne Supersonic (1 pas primary = 1 500 poj./h).
  - Wszyscy jadą do pracy w jednym oknie. Rozkład GBR jest bardziej skupiony niż dla miasta z przemysłem zmianowym.
- **Nie interpretujemy tego jako realnej kongestii w Kutnie (D2, D6).** To jest diagnostyka pipeline'u.

## Wykresy

- `reports/f5_run.png`: aktywności, obciążenia, odjazdy w ciągu doby, czasy podróży.
- `reports/f5_delay.png`: mapa opóźnień.
- Wykresy MATSim w `output/f5_10pct/`: `scorestats.png`, `modestats.png`, `traveldistancestatslegs.png`, `traveldistancestatstrips.png`, `stopwatch.png`, `ph_modestats.png`, `pkm_modestats.png`.

## Gotcha znalezione w tej fazie

- **`controller.outputDirectory` jest rozwiązywany względem katalogu roboczego, a nie configu.** Pierwszy run zapisał wynik do `C:\Users\Michal\output`. Wynik przeniesiono, a run powtórzono z `output/f5_10pct`, uruchamiając z katalogu projektu.
