# Zawrotki na początku i końcu trasy (D29): R9.1 vs R9

Data: 2026-10-23. Decyzja: [D29](../../../docs/projekt/DECISIONS.md). Runy: GitHub Actions, run `39986337733` (R9.1 i kontrolne R9 na tej samej platformie, 5 + 5 jobów, 25%, 50 iteracji). Liczby: [zawrotki_porownanie.json](zawrotki_porownanie.json), wykres [zawrotki_porownanie.png](zawrotki_porownanie.png), skrypty `zawrotki_pomiar.py`, `zawrotki_porownanie.py`.

## 1. Co to jest i skąd się bierze

Zawrotka = kolejne linki A (u→v) i B (v→u) w pierwszych lub ostatnich 3 linkach trasy. Aktywność (dom, praca) ma w MATSim jeden link, agent rusza z jego końca i nie może zawrócić w pół ulicy. Przypięcie szło do najbliższego linku, a na ulicy dwukierunkowej oba kierunki są jednakowo blisko, więc kierunek był praktycznie losowy (53% `f` wśród dwukierunkowych domów). W połowie przypadków kierunek był przeciwny do celu. Tylko ok. 30% zawrotek wypada w ślepym końcu (G1), reszta na zwykłych węzłach i skrzyżowaniach. W środku trasy zawrotek prawie nie ma (0,3%).

## 2. Poprawka

`plans.py`, `snap_mode = "route"`: kandydaci to najbliższy link i jego link odwrotny, wybór po czasie trasy swobodnej (length/freespeed, graf bez zakazów skrętu) od końca linku odjazdu do początku linku przyjazdu z jego przejechaniem. Dom na starcie i na końcu dnia mają osobne linki (`home_link`, `home_link_end`). Praca ma jeden link (suma czasów tam i z powrotem). Dojeżdżający spoza powiatu kończą dzień na linku wyjazdowym tej samej drogi. `snap_mode=nearest` odtwarza R9 bajt w bajt (sha256 `c06e715e…`). Kontrola platformy: R9 na GitHub Actions daje identyczne natężenia i opóźnienia jak lokalnie (różnica 0,0%).

## 3. Wyniki (mediana 5 runów; rozrzut referencyjny = seedy planów R9)

| | R9 | R9.1 |
|---|---|---|
| podróże z zawrotką na starcie lub końcu | **35,1%** (start 21,6, koniec 18,4) | **12,4%** (start 8,3, koniec 4,1) |
| dodatkowy czas w zawrotkach | 161 poj.-h, 1,99% czasu | 39 poj.-h, 0,49% |
| średnio na podróż z zawrotką | +68 s | +47 s |
| mieszkańcy `r` (start / koniec / % czasu) | 41,2 / 31,1 / 6,3% | 27,0 / 13,8 / 3,6% |
| dojeżdżający `c` | 36,7 / 40,5 / 4,5% | 25,1 / 13,1 / 1,7% |
| wyjeżdżający `o` | 46,6 / 22,0 / 2,1% | 29,8 / 7,9 / 1,1% |
| tło lekkie `t` | 12,9 / 12,7 / 1,5% | 0,13 / 0,12 / 0,01% |
| tło ciężkie `h` | 14,2 / 9,4 / 0,7% | 0,21 / 0,27 / 0,01% |
| pracujący „tam”: start / koniec | 31,5 / 30,4% | **1,0** / 25,0% |
| pracujący „z powrotem”: start / koniec | 49,1 / 36,2% | 52,3 / **0,9%** |
| 5 runów: nogi car = plany, stuck | 5/5, 0 | 5/5, 0 |
| przepełnione linki > 2× | 0 | 1 w jednym runie (p1), 0 w pozostałych |
| GPR lekkie w ±15% (15 odcinków) | 14/15 (poza DW 10043) | **14/15** (poza DW 10043, +18,9%) |
| GPR ciężkie w ±15% | 14/15 (poza DK 91878) | **13/15** (poza DK 91878 −21,3% i DK 10044 −16,3%) |
| zmiana natężenia wobec R9 | | lekkie: mediana 0,43%, maks. 2,2%; ciężkie: mediana 1,2%, maks. 9,7% |
| opóźnienie dobowe [poj.-h próbki] | 226,8 / 233,4 / 231,5 / 247,7 / 222,6, mediana 231,5 | 224,2 / 224,3 / 228,6 / 248,6 / 217,5, mediana 224,3 |
| przyczyny opóźnienia (pojemność / węzeł / spillback) | 19 / 47 / 32% | 19 / 44 / 37% |
| podróż car pracujących | 17,40 min, 11,27 km | 17,11 min, 11,10 km (rozrzut planów R9: 0,32 min) |

## 4. Wnioski

1. **Zawrotek jest trzy razy mniej** (35,1% → 12,4% podróży), a ich koszt spadł z 2,0% do 0,5% czasu pojazdów. W tle prawie zniknęły (z ok. 13% do 0,1–0,3%), przy domu pracujących też (start „tam” 1,0%, koniec „z powrotem” 0,9%).
2. **Jedna zawrotka na podróż w obie strony przy pracy zostaje** (odjazd z pracy 52%, przyjazd do pracy 25%). Praca ma w planie jeden link na przyjazd i odjazd. Usunięcie wymaga rozdzielenia aktywności pracy na dwie (krótka noga piesza między nimi) i parametrów scoringu dla nowego typu; to zmiana struktury planu, poza D29.
3. **Ruch w modelu prawie się nie zmienił.** Opóźnienie 224,3 wobec 231,5 poj.-h przy rozrzucie planów 25, czas podróży pracujących −0,3 min przy rozrzucie 0,32 min. Zysk to poprawny model (mniej sztucznych przejazdów), nie widoczna poprawa natężeń.
4. **Kryterium bazy z D29 nie jest spełnione w całości:** GPR ciężkie 13/15 zamiast ≥ 14/15. Winna jest jedna granicznie położona sekcja: DK 10044 (R9 87,4% GPR, R9.1 83,7%), przy rozrzucie seedów planów tej sekcji 12–14%, czyli zmiana 3,7 pp mieści się w szumie, ale przekracza próg 15%. 91878 jest poza ±15% w obu (77–79%, rozrzut planów 43–44%). Lekkie: 14/15, bez zmiany.
5. R9 zostaje bazą do decyzji użytkownika; plany, macierze O-D i scenariusz R9.1 są gotowe (`scenarios/kutno_r91/`, `background_od_r91_*`, `plans_g3r91_25pct*`).

## 5. Ograniczenia

- Plany R9.1 bez tła (R1) i estymacja O-D szły lokalnie (przed ustaleniem, że runy mają iść na GHA, ERRORS 34).
- Czas trasy z TomTom nie był liczony (D22).
- Odległość swobodna w wyborze kierunku pomija zakazy skrętu i opóźnienia; MATSim liczy trasę dynamicznie, więc część zawrotek mogła wynikać z ruchu (2 punkty procentowe na starcie przy domu to granica pomiaru).
- Sekcja DK 10044 i DK 91878 (ciężkie) mają dużą wariancję planów; ocena 14/15 jest na progu.
- Przypięcie do jednego linku jest nadal uproszczeniem (F1): dla linków jednokierunkowych kandydat jest jeden.
