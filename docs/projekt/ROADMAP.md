# Mapa projektu MATSim Kutno

Stan: 2026-10-25. Zacznij od tego pliku: fazy, bieżąca praca, dalsze plany i miejsce każdej rzeczy w repo.

## 1. Gdzie czego szukać

| pytanie | plik |
|---|---|
| Na jakim etapie jesteśmy, co dalej? | **ten plik** |
| Co zdecydowaliśmy i dlaczego? | [DECISIONS.md](DECISIONS.md) (D1–D25) |
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

### Etap 2: rozszerzenia (zamknięty 2026-10-23)

| faza | co | stan | gdzie |
|---|---|---|---|
| G2 | miejsca pracy (suma z rejestru, wyjeżdżający) | ✅ suma (D17); otwarte: rozkład w gminie (REGON) | [g2](../../reports/etap2/g2_miejsca_pracy/g2_miejsca_pracy.md) |
| G3 | domy: dwie wersje (OSM, działa zawsze; BDOT10k, polska) | ✅ zrobione w etapie 3 (D28, baza R9, 2026-10-23) | [G3_domy.md](../../docs/research/G3_domy.md) |
| **G5** | **ruch tła i kalibracja do GPR i do prędkości TomTom** | **✅ zamknięte (D25): baza R7b; znane ograniczenia w §3** | niżej, §3, [d23_podsumowanie](../../reports/etap2/g5_predkosci_d23/d23_podsumowanie.md) |
| G6 | kolejki (D18) i wizualizacja w Blenderze | ✅ D18; Blender w osobnej sesji | [g6_kolejki](../../reports/etap2/g6_kolejki/g6_kolejki.md), [G6_blender.md](../../docs/research/G6_blender.md) |

**Etap 2 zamknięty 2026-10-23** (decyzja użytkownika): (1) D23 zakończone ✅, (2) G3 przeniesione do etapu 3 jako zadanie po G1, (3) G5 zamknięte ✅ (D25), rozbieżności z §3 zostają znanymi ograniczeniami. G2 zostaje z otwartym rozkładem w gminie (REGON) jako znane ograniczenie.

### Etap 3: pełne Kutno (plan do przemodelowania)

Kolejność zadań. Każde wymaga decyzji w DECISIONS.

| kolejność | zadanie | uwagi |
|---|---|---|
| 1 | **G1: skrzyżowania** (tylko geometria i zakazy skrętu) | ✅ zakazy skrętu wdrożone (D26, baza R8), efekt poniżej rozrzutu seedów, `f` bez zmian ([g1.md](../../reports/etap3/g1_skrzyzowania/g1.md)); sygnalizacja świetlna później; rozdziela opóźnienia węzłów od prędkości (D23, `f` w mieście) |
| 2 | **G3: domy** (z etapu 2) | ✅ D28, baza R9: BDOT10k jedno- i wielorodzinne, waga obrys × kondygnacje; zgodność z GUS 250 m TV 10,3 → 8,1 pp, ruch bez zmian ponad rozrzut planów ([g3.md](../../reports/etap3/g3_domy/g3.md)) |
| 3 | ✅ **atrybuty osób** (D30, baza R9.2: wiek, płeć, prawo jazdy, carAvail; pełna populacja Kutna w CSV; [atrybuty.md](../../reports/etap3/g_atrybuty/atrybuty.md)) | wiek z NSP 2021; dostęp do auta i odsetek prawa jazdy z ogólnych statystyk GUS (łódzkie); najpierw research |
| 4 | **dodatkowe aktywności** (szkoła, zakupy, sprawy) | nowa faza, zmiana planów i godzin; dane o celach i rozkładzie godzin z GUS Mobilność |
| 5 | **GTFS i transport publiczny** | GTFS Kutno: licencja potwierdzona przez użytkownika 2026-10-21; kolej z feedu Kuranowskiego; research: [G4_tryby.md](../../docs/research/G4_tryby.md) |
| 6 | **wybór trybu i kalibracja ASC**: car, ride (pasażer), pt, bike, walk | wzorzec: Kelheim i Berlin (`ride` jako tryb sieciowy, rower i pieszo wg wzorca); cel kalibracji z GUS Mobilność |
| 7 | **pomiary miejskie do walidacji** | tylko dane publicznie dostępne; jeśli ich nie ma, zapisujemy to jako ograniczenie |
| 8 | **odtworzenie od zera i wnioski** | dokończenie README, pipeline na czystym klonie, spis tego, co się przenosi na Łódź |
| 2b | **zawrotki na początku i końcu trasy** | ✅ D29, baza **R9.1** (kierunek linku wg trasy, 2026-10-25): zawrotki 35% → 12% podróży; zostaje jedna przy pracy (jedna aktywność pracy), do rozdzielenia razem z krokiem 4 ([zawrotki.md](../../reports/etap3/g_zawrotki/zawrotki.md)) |
| ewent. | sygnalizacja świetlna | po skrzyżowaniach |

**Plan dalszych prac etapu 3 (2026-10-25).** Zasada: runy MATSim tylko na GitHub Actions, 25%, maks. 50 iteracji; każdy krok z decyzją w DECISIONS i porównaniem z rozrzutem seedów planów.

| krok | zawartość | zależność |
|---|---|---|
| 0 | ✅ **Estymacja O-D na GitHub Actions** (2026-10-25, workflow `matsim-od`, [krok0.md](../../reports/etap3/krok0_od_gha/krok0.md)) (warunek wstępny dla kroków 3 i 4): workflow „runy bez tła × 3 seedy → artefakty z eventami → `background_od.py` → macierze”. Dziś ta część idzie lokalnie (ERRORS 34), a artefakty GHA nie zawierają eventów | blokuje każdą zmianę planów, bo zmiana planów wymaga nowej estymacji O-D |
| 3 | ✅ **Atrybuty osób** (D30, baza R9.2, [atrybuty.md](../../reports/etap3/g_atrybuty/atrybuty.md)) (research, potem wdrożenie): wiek z NSP 2021 (BREC), prawo jazdy i dostęp do auta z GUS (łódzkie). Zasięg: atrybuty w `plans.xml` i `car_share` zależne od wieku zamiast jednego 0,64. Sam zapis atrybutów nie zmienia ruchu; zmienia go tylko użycie (wybór, kto jedzie autem), więc to krok danych przed krokami 4 i 6 | po 0 |
| 4A | ✅ **Praca = przyjazd + odjazd** (D31, [praca_split.md](../../reports/etap3/g_praca_split/praca_split.md)): zawrotki 12,4% → 1,1%, ruch bez zmian; użytkownik wybrał `work_split = off`, baza zostaje R9.2, wariant w kodzie | po 3 |
| 4B | 🔶 **Dodatkowe aktywności** (szkoła, zakupy, sprawy) razem z **rozdzieleniem aktywności pracy na przyjazd i odjazd** (usuwa ostatnie zawrotki, D29). **Research gotowy** ([G_aktywnosci_dodatkowe.md](../research/G_aktywnosci_dodatkowe.md)), czeka na odpowiedzi użytkownika (zakres A–D, tryb, bilans tła, godziny, uczniowie spoza Kutna, łańcuchy); potem D31 | po 3 (potrzebny wiek: dzieci, emeryci) |
| 5–6 | GTFS i PT, wybór trybu i kalibracja ASC | po 4 |
| 7–8 | pomiary miejskie, odtworzenie od zera | na końcu |

Poza kolejką, do decyzji użytkownika: ponowna walidacja czasów (TomTom, D22: nowe requesty wymagają zgody), DK 91878 (ciężkie −21%, poza ±15% od R7b).

Zasada: dane tylko z ogólnodostępnych źródeł, bez mocno blokowanych. REGON (rozkład miejsc pracy w gminie) poza zakresem, zostaje znanym ograniczeniem G2.

### Łódź

Nie planujemy. **Dopóki Kutno nie jest skończone (etapy 2 i 3), do Łodzi nie przechodzimy.** Najpierw przećwiczyć w Kutnie, co działa, a co nie.

## 3a. Etap 2: kolejność do zamknięcia

| krok | zadanie | stan |
|---|---|---|
| 1 | Ścieżka prędkości (D23): kroki 1–5 ✅, R7b nową bazą (D25); `f` „na dziś”, obserwacje do dopracowania w [obserwacje_f.md](../../reports/etap2/g5_predkosci_d23/obserwacje_f.md) | ✅ |
| 2 | G3: dwie wersje domów (OSM zawsze; BDOT10k polska); wymaga decyzji w DECISIONS | ✅ zrobione w etapie 3 (D28, R9, 2026-10-23) |
| 3 | Potwierdzenie, że G5 jest zamknięte | ✅ D25 (znane ograniczenia w §3) |
| 4 | Zamknięcie etapu 2 i przejście do etapu 3 | ✅ 2026-10-23 (decyzja użytkownika: G3 do etapu 3). Równolegle: run 25% × 100 i 400 it. na GitHub Actions ([GH_ACTIONS_run.md](../../docs/research/GH_ACTIONS_run.md)) |

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

Baza: **R7b** (D25; A1 98% / 101%, 14/15 odcinków w ±15% dla lekkich i ciężkich; R6: 12/15). Odcinki 91124 i 91866 są kontrolne (użyte w wyborze wariantów), nie walidacja niezależna. Znane ograniczenia po zamknięciu G5: bilans stref DK91/DK92 wsch. (odcinki GPR poza siecią), liczniki lokalne 10045 / 91892 / 91119 (36 / 60 / 55%), podział Objazdowa/Bitwy (K5), brak pomiarów miejskich, TAG 58% (wymagane > 85%), `f` w mieście zawiera opóźnienia węzłów do G1, `f_D` do przeglądu (`podsumowanie.md`, [obserwacje_f.md](../../reports/etap2/g5_predkosci_d23/obserwacje_f.md)).

## 4. Dalsze plany (po zamknięciu G5)

| pomysł | stan | uwagi |
|---|---|---|
| **Prędkości sieci (cruise speeds) + ponowna walidacja TomTom** | ✅ **D23 wdrożone** (D25): sieć R7, baza R7b; MAPE czasu tras 20,5 → 18,2% (walidacja), 18,3 → 14,7% (analiza), segmenty swobodne 0,86 → 0,99 | [d23_podsumowanie.md](../../reports/etap2/g5_predkosci_d23/d23_podsumowanie.md), [plan](../../reports/etap2/g5_predkosci_d23/plan.md). `f` do dopracowania po G1 i kolejnych sprawdzeniach |
| Walidacja czasów TomTom (D22) | ✅ zrobiona dla R6; HERE przygotowane (brak klucza) | [g5_czasy_tomtom.md](../../reports/etap2/g5_czasy_tomtom/g5_czasy_tomtom.md) |
| Geometria linków z OSM | 💡 propozycja | potrzebna do zgodności tras i walidacji dróg tertiary/unclassified; przyda się w G6 |
| Lokalny wizualizer runu | ▶ **D24, kroki 1–3 kod ✅, oś harmonogramu ✅, łamane OSM w oknie ✅, spike ✅** (WebView2 + Leaflet). Dalej: plan poprawek okna zaakceptowany, kod jeszcze nie. Podkład, drugi run i bake odłożone. Łódź poza tym krokiem | faza po zamkniętym MVP; nie zastępuje G5 ani D23. Kod: `pipeline/viz_index.py`, `pipeline/viz_engine.py`, `viz_player/`. Plan: `docs/research/wizualizer_plan.md` |
| Skrzyżowania, aktywności, GTFS i PT, wybór trybu | etap 3 | kolejność w §2 |
| Łódź | bez fazy | dopiero po zamknięciu całego Kutna |

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
