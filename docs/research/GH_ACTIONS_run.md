# Run scenariusza Kutna na GitHub Actions (25%, 100 i 400 iteracji)

Data: 2026-10-21. Status: **technicznie możliwe**, szkic workflow gotowy (`.github/workflows/matsim-run.yml`), **nie uruchomiony na GitHubie** (nie wolno bez pushu; push tylko na prośbę użytkownika, CLAUDE.md D12). Lokalnie sprawdzono scenariusz samodzielny i polecenia analizy.

## Czy się da

| wymaganie | stan |
|---|---|
| repozytorium | `GISBoost/matsim-kutno` jest **publiczne** (API GitHub, `private: false`), więc standardowe runnery są darmowe |
| runner | `ubuntu-latest` w publicznym repo: 4 vCPU, 16 GB RAM, ok. 14 GB dysku, limit joba 6 h (parametry z pamięci, nie zweryfikowane w wyszukiwaniu; przy zmianie specyfikacji sprawdzić w dokumentacji GitHub). Run potrzebuje ok. 3–6 GB sterty |
| Java 25 (MATSim 2026.0) | `actions/setup-java@v5`, `temurin`, `25` (wg dokumentacji Adoptium i testów w PR setup-java 25 jest wspierana) |
| jar | budowany w jobie: `bash mvnw -B package -DskipTests` w `matsim/` (Maven Wrapper jest w repo, ok. 1–3 min z cache) |
| wejścia | **brakowało**: sieć i plany są w `.gitignore` (`scenarios/kutno/*.xml.gz`), a zbudowanie ich od zera wymaga `data/raw/` (OSM, BREC, GUS; setki MB i skrypt pipeline). Rozwiązanie: samodzielny katalog `scenarios/kutno_r7b_25pct/` (config, sieć 365 KB, plany 528 KB, pojazdy 58 KB), ok. 1 MB, poza wzorcem `.gitignore`. Zawiera dane syntetyczne pochodne OSM (ODbL) i GUS (CC BY 4.0), licencje i atrybucja jak w `LICENSE-DATA.md` |
| czas | lokalnie ok. 7–11 s na iterację (jeden run albo 5 równolegle). 100 it. ≈ 12–19 min, **400 it. ≈ 50–75 min** na tym komputerze. Runner GitHub jest zwykle wolniejszy (współdzielone rdzenie), więc 400 it. szacuję na 1,5–2,5 h, z zapasem do limitu 6 h. QSim nie przyspiesza od liczby wątków (CLAUDE.md), więc 4 vCPU wystarczą |
| wyniki | `output_events.xml.zst` ok. 40 MB, całość runu ok. 250 MB. Do artefaktu trafia pakiet wybranych plików (zdarzenia z ostatniej iteracji, linkstats, legs, trips, logi, wyniki analizy). Artefakty liczą się do limitu miejsca konta (500 MB na koncie Free), więc retencja 30 dni i tylko pakiet, nie cały `output/` |

## Co zawiera workflow

- `workflow_dispatch` (ręcznie), pola: `iterations_list` (domyślnie `[100, 400]`, osobny job na każdą wartość, `fail-fast: false`), `seed` (4711), `threads` (2, jak R6 i R7b; wyniki przy 4 i 8 wątkach identyczne, przy 1 inne).
- Kroki: checkout → Java 25 → Python 3.12 → build jar → run MATSim z `scenarios/kutno_r7b_25pct/config.xml` → analiza tymi samymi skryptami co lokalnie (`check_events.py`, `convergence.py`, `g5_baseline.py` lcv/heavy względem GPR, `link_delay.py`, `queues.py`) → upload pakietu.
- Job `porownanie`: pobiera artefakty i uruchamia `compare_runs.py` dla pierwszej i ostatniej liczby iteracji (czasy podróży, prędkość wg godziny, score).
- Dlaczego 100 i 400 w jednym uruchomieniu: ten sam runner, Java, seed, config, więc różnica to wyłącznie liczba iteracji (`fractionOfIterationsToDisableInnovation` = 0,8 skaluje się z `lastIteration`: innowacje wyłączone od it. 80 albo 320).

## Jak uruchomić (po akceptacji pushu przez użytkownika)

1. Scalić gałąź `d23` (scenariusz, workflow, configi) do `main`.
2. GitHub → Actions → `matsim-run` → Run workflow (lista `[100, 400]`, seed 4711, wątki 2).
3. Po zakończeniu pobrać artefakty `kutno-r7b-100it`, `kutno-r7b-400it`, `porownanie` i położyć `kutno-r7b-*` jako `output/gha_100it` i `output/gha_400it`.

## Porównanie wyników (plan analizy)

1. **Odtwarzalność:** `gha_100it` kontra lokalny `output/g5r7b_25pct_s4711` (ten sam seed i wątki). Jeśli wyniki są identyczne (natężenia linków, score), run na GitHubie jest odtwarzalny i to dowód na „pipeline na czystym klonie” (etap 3, zadanie 7). Różnica = inna kolejność liczb zmiennoprzecinkowych albo inny runner; wtedy porównujemy statystycznie. Lokalny test samego scenariusza: `r7b/test_scenariusz_samodzielny_100it.log`.
2. **100 vs 400 iteracji:** `convergence.py` (zmiana natężeń top-50 linków między kolejnymi `linkstats`, GEH 100 vs 400), GPR (`g5_baseline.py` lcv i heavy: odcinki w ±15%, A1), opóźnienie dobowe i `queues.py` (przepełnione linki), czasy podróży i score z `compare_runs.py`. Pytanie badawcze: czy 100 iteracji wystarcza (CLAUDE.md zakłada max 100), czy GPR i opóźnienia są stabilne po 400.

## Ryzyka i ograniczenia

- Workflow nieprzetestowany na GitHubie. Możliwe poprawki: wersje akcji, ścieżki artefaktów, pamięć (`-Xmx6g` przy 16 GB powinno wystarczyć).
- `uv sync --frozen` pobiera geopandas, shapely itp. (kilka minut). Skrypty analizy czytają `scenarios/kutno/validation/gpr_linki.csv` (jest w gicie) i `config/kutno.toml`; nie potrzebują `data/raw/`. Jeśli któryś skrypt się wywróci, krok ma `|| true`, a pakiet i tak zawiera dane do analizy lokalnej.
- Runy > 100 iteracji tylko na wyraźną prośbę (zasada projektu); to jest taka prośba (400), więc zgłoszenie jest tu.
- Limit miejsca na artefakty (500 MB Free): 2 × ok. 80 MB, bez problemu, ale kolejne uruchomienia trzeba czyścić.
