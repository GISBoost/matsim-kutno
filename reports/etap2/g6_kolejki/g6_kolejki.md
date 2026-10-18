# Kolejki z wizualizacji G6: diagnoza i poprawka D18

Data: 2026-10-17. Pytanie z G6 (`docs/research/G6_kolejki_do_sprawdzenia.md`): ok. 26% klatek ma pojazdy wolniejsze niż 1,5 m/s, a pojedyncze auta stoją do 6 min. Czy to błąd?
Narzędzie: `pipeline/queues.py`. Liczy przejazdy pośrednich linków z eventów (bez linku startu i końca podróży), opóźnienie względem czasu swobodnego, przepływ wylotowy w najgorszych 15 min (× 1/sampleSize) względem capacity, zapełnienie linku następnego i przepełnienie linków.

## 1. Obserwacja G6 jest prawdziwa (run referencyjny B 25%, s4711, 06–09)

- 26% czasu pojazdów na linkach pośrednich to opóźnienie, a 18% czasu to jazda < 1,5 m/s. To zgadza się z 26% klatek z G6, więc Blender pokazuje wiernie to, co liczy model.
- Opóźnienie > 60 s ma tylko 2,2% przejazdów linków. Kolejki są skupione: 20 linków daje 80% opóźnień.
- Przyczyny opóźnień:
  - **51% „capacity”**: link sam jest wąskim gardłem, przepływ wylotowy ≥ 90% capacity. Prawie zawsze to ulice `tertiary` z 1 pasem i **600 poj./h** (domyślne wartości Supersonic), m.in. Wodna, Oporowska, Grunwaldzka i Łęczycka.
  - **44% „spillback”**: kolejka z linku następnego. Głównie Sklęczkowska (DK92): 2 pasy przechodzą w 1 pas o capacity 1 500 poj./h (link `2001576790001r`, wylot 1 504 poj./h = capacity), a kolejka cofa się na krótkie odcinki przed zwężeniem.
  - 6% „node”: konkurencja na węzłach.
- Natężenie dobowe modelu na Sklęczkowskiej przy GPR 91869 to 53–63% SDRR (2 604–3 092 vs 4 936 na kierunek). Model zawiera tylko dojazdy do pracy samochodem, więc nie ma sygnału, że przeszacowuje dobę. Kolejka bierze się ze skupienia popytu w szczycie (profil GBR), nie z nadmiaru ruchu w ciągu dnia.

## 2. Artefakt: `stuckTime` 10 s

- Na 18-metrowym linku Sklęczkowskiej (`5452223090000r`, pojemność składowania w próbce 1,2 pojazdu) stało naraz **82 pojazdy**. W sumie 13 linków było przepełnionych ponad 2 × (pojemność + bufor).
- Przyczyna: od F5 configi miały domyślne `qsim.stuckTime = 10 s` przy `removeStuckVehicles = false`. Po 10 s QSim wpycha pierwszy pojazd na pełny link. Kolejka spod zwężenia zamiast cofać się w górę ulicy kompresuje się na krótkim odcinku. To właśnie wyglądało w filmie jak „auta stojące w miejscu”.
- Na 10% to samo: 40 pojazdów na `2001576790001r` (pojemność 1,1).

## 3. Test wrażliwości (te same trasy z runu B 25% s4711, sam mobsim, `stuck_test/`)

| dynamika, stuckTime | opóźnienie / dzień [poj.-h próbki] | opóźnienie 06–09 | przepełnione linki | stuck |
|---|---|---|---|---|
| queue, 10 (dotychczas) | 752 | 318 | 13 | 0 |
| **queue, 30** | 776 (+3%) | 329 | 6 | 0 |
| queue, 60 | 817 | 329 | 2 | 0 |
| queue, 300 | 806 | 331 | 0 | 0 |
| kinematicWaves, 30 | 1 177 (+56%) | 391 | 12 | 0 |
| kinematicWaves, 300 | 35 757 | 1 694 | 63 | **350 (gridlock)** |

- Przy dynamice `queue` stuckTime zmienia głównie to, **gdzie** stoi kolejka, a nie **ile** jest opóźnienia (±7%).
- kinematicWaves (dynamika ze scenariuszy VSP) zmienia opóźnienia o +56%. To decyzja kalibracyjna, a nie poprawka.

## 4. Poprawka D18 i run 25% × 3 seedy (`d18_25pct/`)

`stuckTime = 30 s` we wszystkich configach Kutna, jak w matsim-berlin v6.3 i matsim-kelheim v3.1 (próbka 25%). Plany te same co w B (D17).

| | B, stuckTime 10 | **D18, stuckTime 30** |
|---|---|---|
| nogi car, stuck | 12 604, 0 | 12 604, 0 (3 seedy) |
| opóźnienie razem, 3 seedy [poj.-h próbki] | 754–777 | 735–854 |
| przepełnione linki (06–09) | 13 | 4–7 |
| maks. pojazdów na linku | 82 (pojemność 1,2) | 18–34 |
| mediana czasu: mieszkańcy / przyjeżdżający / wyjeżdżający [min] (s4711) | 15,0 / 23,4 / 24,0 | 15,0 / 23,5 / 24,1 |
| GEH < 5 w szczycie 7–8 między seedami | 99,4–99,9% | 98,8–100% |

- Wskaźniki zbiorcze bez zmian. Seed 2 ma większe opóźnienie (854), bo kolejka na Bitwy pod Kutnem (DK60) narosła mocniej. Rozrzut seedów jest większy niż przy 10 s.
- Kolejki na Sklęczkowskiej są teraz rozłożone na kolejnych linkach przed zwężeniem (`2446692260002r`, `2446692220000f`), zamiast stać na jednym 18-metrowym odcinku.
- Zostało 4–7 linków przepełnionych ok. 5 ×: krótkie linki z pojemnością 1–2 pojazdów w próbce. Całkiem znika to dopiero przy 300 s, ale tej wartości nie ma w żadnym źródle, a w kinematicWaves daje gridlock.

## 5. Co dalej (G5, kalibracja)

Kolejki to w większości **realne wąskie gardła modelu**, ale ich wielkość zależy od parametrów bez lokalnego źródła:
1. Capacity według klasy drogi: domyślne Supersonic, tertiary 600 i primary 1 500 poj./h/pas. Połowa opóźnień siedzi na ulicach tertiary, a GPR nie mierzy ulic miejskich.
2. Dynamika: queue vs kinematicWaves (+56% opóźnień).
3. Skupienie popytu w szczycie: profil GBR Gdańsk (D14) i brak innych celów podróży niż praca.

Pomiary GPR (doba, kierunki) pozwolą skalibrować natężenia na DK/DW. O capacity ulic miejskich nie powiedzą nic, do tego potrzebne są pomiary miejskie albo godzinowe (SCPR Lisica).
