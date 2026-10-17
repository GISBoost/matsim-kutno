# ERRORS

Format: data · faza · polecenie · pierwszy błąd (cytat) · przyczyna · obejście/status.

## Błędy agenta (2026-10-16, sesja F0–R3): lekcje, żeby się nie powtórzyły

Każdy wpis: co się stało → koszt → reguła na przyszłość. Najważniejsze reguły są też w `CLAUDE.md` (Workflow i Gotchas).

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
10. **`controller.outputDirectory` jest względny do katalogu roboczego,** więc pierwszy run F5 trafił do `C:\Users\Michal\output`. → Uruchamiaj z katalogu projektu, ścieżki `output/...`.
11. **`cat > plik;` bez heredoca zawiesił polecenie** (czekał na stdin). Heredoc w bashu rozwinął `\n` wewnątrz kodu Pythona. → Pliki pisz narzędziem Write. W heredocach unikaj sekwencji `\n` w stringach.
12. **Brak danych o `building=no` w regułach klasyfikacji OSM.** → **Każdy filtr „klucz istnieje” (`building`, `shop`) sprawdź pod kątem wartości negatywnych** (`no`, `disused`, `construction`).

## 2026-10-17
13. **GEH między seedami liczyłem na natężeniach próbki 25%,** co zaniża GEH o połowę (pierwszy wynik: max 5,1 zamiast 10,2). → `convergence.py` skaluje teraz × 1/sampleSize z `output_config.xml`. **Każdą miarę zależną od wartości bezwzględnych (GEH, poj.-h) liczyć lub opisywać w skali 100%.**
14. **G2/D17: nowy rodzaj agenta (wyjeżdżający) trafił do gałęzi przyjeżdżających spoza powiatu** w pętli `plans.py` (warunek `kind == "outbound"` stał za `else: ... continue`). Skutek: 168 osób z domem na wjeździe i 79 zduplikowanych id. Walidator złapał to przez `work_outside_gmina = 168`. → Gałąź nowego rodzaju na początku pętli, `assert meta.person.is_unique` w `plans.py`. **Przy dodawaniu rodzaju agenta: osobne testy per rodzaj w walidatorze** (dom/praca w lub poza gminą).
15. **`sed` z `"\n"` w zamianie wstawił prawdziwy znak nowej linii do kodu Pythona** (SyntaxError w `demand.py`). → Zmiany z `\n` w stringach rób narzędziem Edit (jak lekcja 11).
16. **`A && (B) & (C) & wait` uruchomiło walidację C równolegle z generowaniem planów** (`&` wiąże słabiej niż `&&`), więc walidator porównał stary plik z nowym i zgłosił brak determinizmu. → Sekwencję grupuj nawiasami: `A && { (B) & (C) & wait; }`.
