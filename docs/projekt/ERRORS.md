# ERRORS

Format: data · faza · polecenie · pierwszy błąd (cytat) · przyczyna · obejście/status.

## Błędy agenta (2026-10-16, sesja F0–R3): lekcje, żeby się nie powtórzyły

Każdy wpis: co się stało → koszt → reguła na przyszłość. Najważniejsze reguły są też w lokalnych zasadach projektu (Workflow i Gotchas).

**Długie runy i zasoby**
1. **Odpaliłem długie runy, zanim sprawdziłem dane wejściowe.** Błąd `building=no` (plac komisu `shop=car`, 3,6 ha jako największe miejsce pracy) wyszedł dopiero w select-link po pierwszym runie 25%. Trzeba było przerwać i powtórzyć wszystkie runy. → **Przed każdym długim runem:** top-10 celów i źródeł (budynki, gminy, linki) i spojrzenie, czy to realne obiekty. Dopiero potem run.
2. **Zaplanowałem za ciężkie obliczenia** (200 iteracji, 100% × 3 seedy, ok. 2 h). Użytkownik musiał to dwa razy ograniczać. → **Domyślnie maks. 100 iteracji i próbka 25%.** 100% tylko na wyraźną prośbę. Przed startem podaj szacowany czas i zapytaj, jeśli przekracza ok. 30 min.
3. **Zmieniłem plany (start z wjazdu później o 4 h), nie sprawdzając `qsim.endTime`.** Agent z Krakowa dostał `stuckAndAbort`, run 100% trzeba było powtórzyć. → **Po każdej zmianie godzin:** max(start) + praca + dojazd < `endTime`.
4. **Zabijając run, zabijałem tylko `java`, a pętla w skrypcie startowała następny seed** (dwa razy). → **Najpierw zatrzymaj skrypt-rodzica (TaskStop), potem `java`.** Sprawdź listą procesów, że nic nie zostało.

**Weryfikacja zamiast pamięci i literatury**
5. **Rekomendację z literatury (storage = flow^0,75) wpisałem jako „błąd” bez sprawdzenia w MATSim 2026.** Wersja 2026 odrzuca storage ≠ flow. → **Każdą zmianę configu z literatury testuj runem na 2 iteracjach, zanim nazwiesz coś błędem.**
6. **Przesadzone wnioski:** „score stabilizuje się” (artefakt wyłączenia innowacji), „10% ≈ 100%” (tylko mediany), „1 500 poj./h jest typowe” (bez źródła). → **Wnioski formułuj na poziomie, który dane faktycznie pokazują.** Każda liczba „typowa” wymaga źródła.

**Walidatory i testy**
7. **`check_events.py` nie liczył `stuckAndAbort`** (MATSim 2026 ma inną nazwę eventu). Test „0 stuck” byłby fałszywie zielony. → Liczy teraz każdy typ zawierający „stuck”. **Po aktualizacji MATSim sprawdź nazwy eventów.**
8. **Regresja smoke dała „ok” ze starego outputu,** bo run się nie wykonał: niezacytowana ścieżka „Program Files” dała kod 127. → **Przed testem regresyjnym usuń stary output.** Zmienne ze ścieżką zawsze w cudzysłowie.
9. **Analiza opóźnień liczyła 8 h postoju w pracy jako opóźnienie,** bo stan nie był czyszczony na `vehicle leaves traffic`. → **Wyniki agregatów sprawdzaj na zdrowy rozsądek** (8 h średniego opóźnienia = błąd analizy, nie kongestia).

**Środowisko i narzędzia**
10. **`controller.outputDirectory` jest względny do katalogu roboczego,** więc pierwszy run F5 trafił do `<katalog użytkownika>\output`. → Uruchamiaj z katalogu projektu, ścieżki `output/...`.
11. **`cat > plik;` bez heredoca zawiesił polecenie** (czekał na stdin). Heredoc w bashu rozwinął `\n` wewnątrz kodu Pythona. → Pliki pisz narzędziem Write. W heredocach unikaj sekwencji `\n` w stringach.
12. **Brak danych o `building=no` w regułach klasyfikacji OSM.** → **Każdy filtr „klucz istnieje” (`building`, `shop`) sprawdź pod kątem wartości negatywnych** (`no`, `disused`, `construction`).

## 2026-10-17
13. **GEH między seedami liczyłem na natężeniach próbki 25%,** co zaniża GEH o połowę (pierwszy wynik: max 5,1 zamiast 10,2). → `convergence.py` skaluje teraz × 1/sampleSize z `output_config.xml`. **Każdą miarę zależną od wartości bezwzględnych (GEH, poj.-h) liczyć lub opisywać w skali 100%.**
14. **G2/D17: nowy rodzaj agenta (wyjeżdżający) trafił do gałęzi przyjeżdżających spoza powiatu** w pętli `plans.py` (warunek `kind == "outbound"` stał za `else: ... continue`). Skutek: 168 osób z domem na wjeździe i 79 zduplikowanych id. Walidator złapał to przez `work_outside_gmina = 168`. → Gałąź nowego rodzaju na początku pętli, `assert meta.person.is_unique` w `plans.py`. **Przy dodawaniu rodzaju agenta: osobne testy per rodzaj w walidatorze** (dom/praca w lub poza gminą).
15. **`sed` z `"\n"` w zamianie wstawił prawdziwy znak nowej linii do kodu Pythona** (SyntaxError w `demand.py`). → Zmiany z `\n` w stringach rób narzędziem Edit (jak lekcja 11).
16. **`A && (B) & (C) & wait` uruchomiło walidację C równolegle z generowaniem planów** (`&` wiąże słabiej niż `&&`), więc walidator porównał stary plik z nowym i zgłosił brak determinizmu. → Sekwencję grupuj nawiasami: `A && { (B) & (C) & wait; }`.
17. **Od F5 runy miały domyślne `qsim.stuckTime` = 10 s przy `removeStuckVehicles=false`.** Nikt tego nie sprawdził, bo testy liczyły tylko eventy `stuck`, a tych było 0. QSim po 10 s wpychał pojazd na pełny link (82 pojazdy na linku o pojemności 1,2 pojazdu), więc kolejki kompresowały się zamiast cofać. Wyłapała to wizualizacja G6. → D18: 30 s. **Przy każdym runie sprawdzaj przepełnienie linków (`pipeline/queues.py`, `overfilled_links_gt2x`)**, a nie tylko liczbę stuck. Domyślne parametry QSim porównuj z referencyjnymi scenariuszami VSP.

## 2026-10-18 (poprawki po audycie G5, D21)
18. **Najbliższy punkt GPR nie zawsze leży na odcinku, na którym jest obiekt.** Kontrola wag stref (I4) wzięła dla A1 płd. punkt 91822 z pełnego wykazu, a ten leży za węzłem Piątek; strefa jest na odcinku 91821. → **Odcinek GPR przypisuj po opisie „od – do” i pikietażu, a regułę „najbliższy punkt” sprawdzaj na mapie odcinków (`dk_odcpom_web.zip`).**
19. **Dwa cele GPR na tym samym odcinku mogą być sprzeczne.** Cel na strefie granicznej DK60 płd. i licznik 91115 na tym samym odcinku (między nimi zjazdy do wsi) dały w estymacji fantomową parę gmin 6 370 podróży/dobę i RMSE 187. → **Po każdej estymacji `pipeline/od_warnings.py`; nowy typ celu dodawaj tylko tam, gdzie odcinek nie ma licznika w sieci, i sprawdź RMSE celów.**
20. **sha256 pliku eventów nie jest testem regresji runu przy wielu wątkach.** Dwa runy z tym samym configiem (4 wątki) dały różne pliki eventów (kolejność w obrębie sekundy), przy identycznych natężeniach i opóźnieniach. → **Regresję runu sprawdzaj na wynikach (`vol_car`, opóźnienia, liczniki), a sha256 tylko dla plików z pipeline'u (plany, macierze, `gpr_linki.csv`).**
21. **Rozrzut „3 seedy MATSim” nie jest niepewnością wyniku.** Seedy planów i punktów estymacji dają 20–100× większy rozrzut (mediana 9–12% na odcinek). → **Wariant uznawaj za lepszy tylko, gdy różnica przekracza rozrzut seedów planów (`g5_r6_ref.md`).**

## 2026-10-18 (walidacja czasów TomTom, D22)
22. **149 requestów TomTom z odpowiedzią 401 w jednym przebiegu.** Klucz w `.env` był w cudzysłowie, a skrypt wysyłał go razem z cudzysłowami i nie przerwał po pierwszym błędzie uwierzytelnienia. Zjadło to 149 z 400 requestów budżetu. → `api_key` zdejmuje cudzysłowy, a `fetch` przerywa przy pierwszym 401/403. **Przed pełnym przebiegiem płatnego albo limitowanego API uruchom mały test (`--test`) na tej samej ścieżce kodu.**
23. **Wskaźnik zgodności tras (bufor 25 m) i kontrola punktu segmentu zakładały, że link ma geometrię drogi.** W sieci MATSim każdy link to prosta między węzłami (2 punkty, linki A1 do 6,7 km), więc trasa po rzeczywistej drodze wychodzi poza bufor na łukach: mediana 0,56, A1 < 70%. Selftest tego nie wykrył, bo syntetyczny dostawca używał tej samej prostej geometrii. → **Test syntetyczny nie może dziedziczyć założenia, które ma sprawdzać.** Przed metryką geometryczną sprawdź liczbę punktów geometrii linków. Zamiennik: stosunek długości tras.

## 2026-10-20 (wizualizer D24, krok 1)
24. **Self-test skleił eventy w jedną linię XML.** `"".join` bez znaku nowej linii dało jeden wiersz. Parser linii zobaczył tylko pierwszy `type="`, wyszedł 1 przejazd i 1 węzeł, a test „więcej niż 8 węzłów” padł (`za mało przejazdów dłuższych niż 8 węzłów: 0`). → Syntetyczny plik eventów składać z nową linią na event, tak jak wyjście MATSim.
25. **`np.load` na Windows trzyma plik.** Po zielonym teście kasowanie `index.npz` i sprzątanie `TemporaryDirectory` rzuciły `PermissionError` (WinError 32). → Zamykać `NpzFile` w `finally`, zanim cokolwiek usuwa plik.
26. **Węzły dopisywane w kolejności pliku nie tworzą ciągłego bloku jednego przejazdu.** Eventy pojazdów się przeplatają, a indeks chce jeden wycinek CSR na przejazd. → Bufor otwartego przejazdu i zrzut przy `vehicle leaves traffic`, nowym wjeździe tego samego pojazdu albo końcu pliku. Wyłapane przed runem R6. Self-test sortuje eventy po czasie, żeby przeplot był w teście.
27. **Brak `x`/`y` przy czynności stawiał ją na węźle from linku.** Gałąź nie odpaliła się na R6 (każda czynność ma współrzędne), więc indeks był dobry, a błąd cichy. → Budowa przerywa się (`czynność bez x/y`). Nie wymyślać punktu.

## 2026-10-20 (okno D24, krok 3)
28. **Po krzyżyku kolejne okno było puste, a ukryty panel nie miał powrotu.** Dwie osobne przyczyny. Panel: `display:none` wyjmował go z siatki, a pasek (z przyciskiem) wpadał w kolumnę o szerokości 0. Pusta mapa: pywebview wstrzykuje mostek w dwóch skryptach. Między nimi `window.pywebview.api` już jest, ale bez `frame`. `pull` ustawiał `busy` i wywoływał `api.frame`, które jeszcze nie istniało. Wyjątek zostawiał `busy` na zawsze, więc auta i linki nie przychodziły. Pierwsze otwarcie czasem wygrywało ten wyścig, kolejne nie. → Pasek ma stałe miejsce w siatce (`grid-column: 1 / -1`, `grid-row: 2`). `pull` woła `frame` dopiero, gdy funkcja jest, a wyjątek zdejmuje `busy`. Smoke czeka na zegar `06:00:00` z samego odtwarzania i sprawdza, że przycisk panelu zostaje na ekranie.

## 2026-10-21 (łamane OSM w oknie)
29. **Wklejenie łamanych w HTML okna wywaliło WebView2.** `NavigateToString` na stronie 1,7 MB: `Wartość jest spoza oczekiwanego zakresu`. Same cięciwy mieszczą się w 659 KB. 50 196 punktów OSM to za dużo na ten jeden string. → Współrzędne idą po starcie okna, kawałkami po 2000, a check odrzuca stronę większą niż 1,2 MB. **Nie doklejać geometrii do `__BOOT__`.**

## 2026-10-23 (G3 i zawrotki R9.1, D28/D29)
30. **Zbyt szeroki filtr przy zatrzymywaniu procesów.** `Get-CimInstance Win32_Process` z dopasowaniem fragmentu wiersza poleceń (`background_od.py|run_od.sh`) trafił też w powłoki tej sesji (16 procesów, w tym `bash.exe` z własnymi poleceniami), bo ich wiersze poleceń zawierały te nazwy. → Filtrować po nazwie procesu (`java.exe`, `python.exe`) i unikalnym argumencie, wykluczyć własny PID, najpierw skrypt-rodzic przez TaskStop (CLAUDE.md, pkt 10).
31. **Przypadkowe ponowne uruchomienie `run_od.sh` w poleceniu, które miało tylko czytać wyniki.** Estymacja O-D wystartowała drugi raz i mogła nadpisać macierze `background_od_r9_*`. Zatrzymana przed zapisem, pliki bez zmian (sprawdzone porównaniem z R7b i datą). → Skrypty zapisujące dane uruchamiać osobnym poleceniem, z jasnym celem; nie doklejać ich do poleceń odczytu.
32. **Literówki w nazwach plików przy kopiowaniu do scenariusza** (`plans_r9_pp1`, `meta_r9_pp2`): `${p:-0}` z prefiksem `p` dawało `pp1`. Wykryte przy `ls`, poprawione. → Nazwy z jawnej listy (`p0 p1 p2`), nie z przetworzonego parametru; po kopiowaniu sprawdzić komplet plików pętlą `test -f`.
33. **Krok analizy na GitHub Actions czytał plik, którego nie ma na runnerze.** `zawrotki_pomiar.py` miał na sztywno `scenarios/kutno/network.xml.gz`, a scenariusz GHA ma sieć w `scenarios/kutno_r91/`. Krok miał `|| true`, więc job wyszedł „success” bez `zawrotki.json`, a zdarzeń nie ma w artefaktach, więc pomiaru nie dało się powtórzyć. → Skrypty analizy dla GHA biorą ścieżkę sieci z argumentu; przed wysłaniem workflow uruchomić kroki analizy na próbnym katalogu; po runie sprawdzić, czy artefakt zawiera każdy oczekiwany plik (`|| true` maskuje błędy). Jeśli analiza wymaga zdarzeń, liczyć ją na runnerze, nie po pobraniu.
34. **Runy MATSim puszczone lokalnie wbrew preferencji użytkownika (2026-10-23: runy na GitHub Actions).** Po utracie pomiaru z p. 33 uruchomiłem lokalnie 5 runów R9.1. Zatrzymane, katalogi `output/g3r91_*` usunięte. → Wszystkie runy MATSim (także runy bez tła do estymacji O-D i testy porównawcze) idą na GitHub Actions; lokalnie tylko test 2 iteracji i pomiary na plikach, które już są lokalnie.
35. **Błędnie przypisany błąd względny i nieoznaczony iloraz (krok 3, research).** Napisałem, że dane GUS Mobilność o autach i prawie jazdy mają błąd względny >20%; to dotyczy dostawczych i motocykli (Tabl. 21, 24 pokazują dla łódzkiego 2,5% auta i 1,9% prawo jazdy). Liczba 0,44 auta na osobę była moim ilorazem dwóch tablic, a podałem ją jak wynik GUS. → Przy cytowaniu tablic GUS sprawdzać kolumnę błędów dla konkretnej pozycji i oznaczać wartości policzone przez nas jako „iloraz/obliczenie”.

## 2026-10-30 (test D34 na GHA)

35. **Job GHA padł na pobraniu DTD z matsim.org** (run 41093715027, job r93 s4711: `Unrecognized DTD directive '<!DOCTYPE >'` przy wczytaniu XML, MATSim nie zapisał outputu, analiza padła na brakujących plikach). Błąd sieci, nie danych: ten sam plik działał w runie 40871126965. → Po porażce jobu w pierwszej minucie sprawdź log kroku MATSim, nie analizy; ponów tylko ten job (`gh run rerun <id> --failed`). Jeśli się powtórzy: lokalne kopie DTD w configach.
