# Mapa projektu MATSim Kutno

Stan: 2026-10-20. Zacznij od tego pliku: fazy, bieżąca praca, dalsze plany i miejsce każdej rzeczy w repo.

## 1. Gdzie czego szukać

| pytanie | plik |
|---|---|
| Na jakim etapie jesteśmy, co dalej? | **ten plik** |
| Co zdecydowaliśmy i dlaczego? | [DECISIONS.md](DECISIONS.md) (D1–D24) |
| Co zrobione, z jakim dowodem? | [PROGRESS.md](PROGRESS.md) (dziennik chronologiczny) |
| Kontrakty faz (wejścia, test, zaliczenie) | [TASKS.md](TASKS.md) |
| Jak działa model i jak go odtworzyć | [README.md](../../README.md) |
| Skąd są dane i liczby | [docs/ZRODLA.md](../../docs/ZRODLA.md), [data/manifest.csv](../../data/manifest.csv), [FACT_CHECK.md](FACT_CHECK.md) |
| Znane błędy i reguły pracy | [ERRORS.md](ERRORS.md) |
| Raporty faz (wyniki, wykresy) | [reports/README.md](../../reports/README.md) |
| Tło metodyczne i research | [docs/research/](../../docs/research/) |

## 2. Fazy

### Etap 1: MVP (zamknięty)

Dojazdy do pracy autem, `dom → praca → dom`.

| faza | co | stan | raport |
|---|---|---|---|
| F0 | środowisko, build, run equil | ✅ | [f0_env](../../reports/etap1_mvp/f0_env/f0_env.md) |
| F1 | sieć syntetyczna, 10 agentów (test regresyjny) | ✅ | [f1_smoke](../../reports/etap1_mvp/f1_smoke/f1_smoke.md) |
| F2 | sieć z OSM (powiat + bufor) | ✅ | [f2_network](../../reports/etap1_mvp/f2_network/f2_network.md) |
| F3 | popyt z GUS (pracujący per obwód, przyjeżdżający) | ✅ | [f3_demand](../../reports/etap1_mvp/f3_demand/f3_demand.md) |
| F4 | plany (domy, praca, godziny) | ✅ | [f4_plans](../../reports/etap1_mvp/f4_plans/f4_plans.md) |
| F5 / F6 | run 10% i 100% (przed naprawami R3) | ✅ | [f5](../../reports/etap1_mvp/f5_run_10pct/f5_run.md), [f6](../../reports/etap1_mvp/f6_run_100pct/f6_run.md) |
| R3 | naprawy techniczne, wyniki 25% × 3 seedy (D15) | ✅ | [r3_ocena](../../reports/etap1_mvp/r3_ocena/wyniki_25pct/r3_25pct.md) |
| D16 | przyjeżdżający spoza powiatu | ✅ | [d16](../../reports/etap1_mvp/d16_przyjezdzajacy/d16_przyjezdzajacy.md) |

### Etap 2: rozszerzenia (G1–G7, każde wymaga decyzji w DECISIONS)

| faza | co | stan | gdzie |
|---|---|---|---|
| G1 | skrzyżowania, sygnalizacja, zakazy skrętu | ⏸ odłożone przez użytkownika | [TASKS.md](TASKS.md) |
| G2 | miejsca pracy (suma z rejestru, wyjeżdżający) | ✅ suma (D17); otwarte: rozkład w gminie (REGON) | [g2](../../reports/etap2/g2_miejsca_pracy/g2_miejsca_pracy.md) |
| G3 | domy (dobór budynków, BDOT10k) | 🔍 zbieranie danych | [G3_domy.md](../../docs/research/G3_domy.md) |
| G4 | tryby: PT, rower, pieszo, wybór trybu | 🔍 research, poza modelem | [G4_tryby.md](../../docs/research/G4_tryby.md), [G4_beeline.md](../../docs/research/G4_beeline.md) |
| **G5** | **ruch tła i kalibracja do GPR** | **✅ baza R6 po audycie; otwarte rozbieżności w §3** | niżej, §3 |
| G6 | kolejki (D18) i wizualizacja w Blenderze | ✅ D18; Blender w osobnej sesji | [g6_kolejki](../../reports/etap2/g6_kolejki/g6_kolejki.md), [G6_blender.md](../../docs/research/G6_blender.md) |
| G7 | przeniesienie na Łódź | ⏸ po G2–G5 | [TASKS.md](TASKS.md) |

## 3. Bieżąca praca: G5

Historia G5, każdy krok z decyzją:

| krok | co | raport |
|---|---|---|
| plan | metoda kalibracji (D19) | [G5_plan_kalibracji.md](../../docs/research/G5_plan_kalibracji.md) |
| R1–R3 | dojazdy × 0,593, tło lekkie z estymacji O-D; R3 = 25% × 3 seedy | [g5_r3.md](../../reports/etap2/g5_kalibracja/g5_r3.md) |
| czasy, PCE | walidacja czasów z GUS, źródło PCE | [g5_czasy_pce.md](../../reports/etap2/g5_kalibracja/g5_czasy_pce.md) |
| R4, R5 | dostawcze i ciężkie (D20); wybór R4 | [g5_r4.md](../../reports/etap2/g5_kalibracja/g5_r4.md), [decyzja](../../reports/etap2/g5_kalibracja/g5_r4_vs_r5_decyzja.md) |
| audyt | niezależny audyt kodu, kalibracji i walidacji | [audyt_g5.md](../../reports/etap2/audyt_g5/audyt_g5.md) |
| poprawki | K1, K2, I4, estymacja R6, I1, D6, I2, I3, D1–D9 ✅ | [plan_poprawek.md](../../reports/etap2/audyt_g5/plan_poprawek.md), [podsumowanie](../../reports/etap2/audyt_g5/poprawki/podsumowanie.md) |
| **R6** | **baza po audycie, referencja 3 seedy MATSim + 2 seedy planów** | **[g5_r6.md](../../reports/etap2/g5_kalibracja/g5_r6.md), [g5_r6_ref.md](../../reports/etap2/g5_kalibracja/g5_r6_ref.md)** |
| czasy TomTom | walidacja czasów i prędkości R6 (D22, wariant A: tylko agregaty): skalibrowany tylko w popycie, niezwalidowany wg TAG (czasy 48–77% tras w kryterium) | [g5_czasy_tomtom.md](../../reports/etap2/g5_czasy_tomtom/g5_czasy_tomtom.md), **[wnioski i plan](../../reports/etap2/g5_czasy_tomtom/wnioski_i_dalej.md)** |

Baza: R6 (A1 99% / 101%, 12/15 odcinków w ±15% dla lekkich i ciężkich). Odcinki 91124 i 91866 są kontrolne (użyte w wyborze wariantów), nie walidacja niezależna. Otwarte: bilans stref DK91/DK92 wsch. (odcinki GPR poza siecią), liczniki lokalne, podział Objazdowa/Bitwy (K5), brak pomiarów miejskich (`podsumowanie.md`).

## 4. Dalsze plany (po zamknięciu G5)

| pomysł | stan | uwagi |
|---|---|---|
| **Prędkości sieci (cruise speeds) + ponowna walidacja TomTom** | ▶ **D23 w toku**: krok 1 ✅, krok 2: dopasowanie 18.10 (C ≈ 0,58, F na granicy 0,5); dobrane trasy C, **ponowne dopasowanie 19.10** ([krok2](../../reports/etap2/g5_predkosci_d23/krok2_dopasowanie.md), [plan](../../reports/etap2/g5_predkosci_d23/plan.md)) | factor 0,8 (D13) zaniża prędkości o ok. 15% wobec TomTom, a czasy tras zgadzają się tylko przez brak opóźnień węzłów. Warianty, pułapki i procedura powtórki: [wnioski_i_dalej.md](../../reports/etap2/g5_czasy_tomtom/wnioski_i_dalej.md). Wymaga decyzji w DECISIONS |
| Walidacja czasów TomTom (D22) | ✅ zrobiona dla R6; HERE przygotowane (brak klucza) | [g5_czasy_tomtom.md](../../reports/etap2/g5_czasy_tomtom/g5_czasy_tomtom.md) |
| Geometria linków z OSM | 💡 propozycja | potrzebna do zgodności tras i walidacji dróg tertiary/unclassified; przyda się w G6 |
| Transport publiczny i wybór trybu | G4 | GTFS, SubtourModeChoice, kalibracja ASC |
| Inne aktywności (szkoła, zakupy, sprawy) | 💡 **brak fazy** | wykluczone z MVP (zasady projektu); wymaga nowej fazy w TASKS i decyzji |
| Skrzyżowania | G1 | odłożone |
| Łódź | G7 | po G2–G5 |
| Lokalny wizualizer runu | ▶ **D24, kroki 1–3 kod ✅, oś harmonogramu ✅, spike ✅** (WebView2 + Leaflet). Akceptacja ludzka okna otwarta. Podkład, łamane OSM, drugi run, bake i Łódź czekają | faza po zamkniętym MVP; nie zastępuje G5 ani D23. Kod: `pipeline/viz_index.py`, `pipeline/viz_engine.py`, `viz_player/`. Plan: `docs/research/wizualizer_plan.md` |

## 5. Układ folderów

| folder | zawartość | w gicie |
|---|---|---|
| `config/` | parametry pipeline'u (`kutno.toml`, profile godzinowe, prędkości) | tak |
| `pipeline/` | Python: dane → popyt → plany → analizy | tak |
| `matsim/` | Java: konwersja sieci i runner MATSim | tak (bez jar) |
| `scenarios/kutno/` | wejścia MATSim: sieć, plany, configi XML, `demand/` (macierze) | częściowo |
| `scenarios/kutno/validation/` | dane pomiarowe przygotowane dla kodu: liczniki GPR na linkach, czasy GUS, sumy F3 | tak |
| `scenarios/smoke/` | test regresyjny (10 agentów) | tak |
| `reports/` | raporty: `etap1_mvp/` (F0–F6, R3, D16) i `etap2/` (G1–G7, audyt); spis w [reports/README.md](../../reports/README.md) | tak |
| `docs/` | źródła ([ZRODLA.md](../../docs/ZRODLA.md)) i research faz (`research/`) | tak |
| `blender/` | skrypty wizualizacji G6 | tak |
| `data/raw/` | pobrane źródła, tylko do odczytu | nie (manifest tak) |
| `output/` | runy MATSim | nie |
| `references/` | filmy referencyjne | nie (nieśledzone) |
