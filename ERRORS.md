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
