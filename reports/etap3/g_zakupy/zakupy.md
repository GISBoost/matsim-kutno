# Krok 4C etapu 3: zakupy i usługi (D32, baza R9.3 do potwierdzenia)

Data: 2026-10-29. Kod: `pipeline/errands.py`, `pipeline/plans.py` (`errands = on|off`), config `[plans]`. Research: [G_aktywnosci_dodatkowe.md](../../../docs/research/G_aktywnosci_dodatkowe.md), [badania_ruchu_PL.md](../../../docs/research/badania_ruchu_PL.md). Wykres: [zakupy_porownanie.png](zakupy_porownanie.png). Liczby: [zakupy_porownanie.json](zakupy_porownanie.json). Logi walidacji planów: `validate_p{0,1,2}.log`.

## Co zrobiono
- Osobne wyjścia `home → shop|service → home`, tylko kierowca samochodu. Częstość na osobę: GUS Mobilność 2024 (Łódzkie, tabl. 10) dom–zakupy + dom–inne zakupy + dom–usługi = 357 974 podróży / 2 146 153 osób 6+, × 40 232 osób 6+ w Kutnie × udział auta jako kierowca 0,424 (ZAŁOŻENIE: Radom fakultatywne 53,2% × 0,797 kierowców; warianty 0,304 Gdańsk, 0,479 GUS) × próbka.
- Uczestnicy: wiek ≥ 18, `license=yes`, `carAvail≠never`, waga wg wieku z BCL 2023. Cele: budynki BDOT10k w gm. Kutno (centrum handlowe/hipermarket, dom towarowy/obiekt handlowo-usługowy, bank/urząd/poczta/starostwo), waga = obrys. Godziny wyjścia z wykresu GBR 2022 „dom–inne” (Gdańsk, przedział 5–20 h, ZAŁOŻENIE), pobyt 57 min (BCL 2023, dolna granica).
- Osobny generator losowy (`errand_seed`), więc `errands = off` odtwarza R9.2 bajt w bajt.
- Przy 25%: 711 agentów-wypraw (456 zakupy, 204 centra handlowe, 51 usługi), ok. 5 700 podróży autem na dobę w 100%.

## Test (GHA run 40871126965, 25% × 50 it., 5 runów na wariant: seedy 4711/1/2 na planach p0 oraz p1, p2)
| miara | R9.2 (kontrola) | z zakupami i usługami | rozrzut / próg |
|---|---|---|---|
| nogi car = oczekiwane z planów | 24 299 | 25 703 (+1 404) | zgodne we wszystkich 10 runach |
| stuck, linki przepełnione > 2× | 0 (jeden link w p1) | 0 | – |
| opóźnienie mediana [poj.-h] | 224,3 | 237,4 (+5,8%) | rozrzut planów 31,1 |
| czas dojazdu do pracy [min] | 17,11 | 17,13 | rozrzut 0,36 |
| GPR lekkie w ±15% | 14/15 | 15/15 | – |
| GPR ciężkie w ±15% | 13/15 | 13/15 | – |
| zmiana natężeń GPR mediana / maks. | – | 0,67% / 4,7% lekkie, 0,76% / 16,1% ciężkie | rozrzut planów 4,2% / 6,5% |
| wypady: czas / dystans | – | 7,05 min / 2,96 km | – |

Wnioski liczbami:
- Spójność i stabilność bez zmian: zero stuck, nogi zgodne z planami.
- Natężenia na przekrojach GPR bez zmian ponad rozrzut planów, poza jednym odcinkiem ciężkich (sekcja 10043, +16,1% przy rozrzucie 6,5%, ciężkie w modelu nie mają zakupów, więc to efekt dojazdu i sąsiedztwa; pojedynczy przekrój, do obserwacji).
- Opóźnienie rośnie o 13 poj.-h (+5,8%), poniżej rozrzutu planów (31). Struktura przyczyn bez zmian (węzły 0,45, spillback 0,33 vs 0,37).
- Zawrotki na starcie i końcu 12,4% → 13,5% podróży, bo wypady mają krótkie trasy start i koniec w tym samym budynku/obszarze (rodzaj `e`: 21% start, 12% koniec, 4,1% czasu). Koszt łączny 0,54% czasu.
- Wypady prawie nie zmniejszają tła (O-D r93: −0,13% lekkie, −0,03% ciężkie), bo przekroje GPR leżą na drogach tranzytowych, nie na ulicach miasta. Wzrost ruchu w mieście nie jest sprawdzony licznikami (TomTom zablokowany przez D22).

## Znane ograniczenia
Udział auta (0,424) i godziny (Gdańsk) to ZAŁOŻENIA; pobyt 57 min to dolna granica; ta sama osoba może być pracującym i agentem-wyprawy (łańcuchy dopiero w osobnym kroku); brak uczniów spoza Kutna, odwiedzających i pasażerów; wypady tylko dorośli z prawem jazdy.

## Jak czytać wykres ([zakupy_porownanie.png](zakupy_porownanie.png))
**Lewy panel: zawrotka na starcie i końcu trasy [% podróży].** Słupki wg rodzaju agenta (c = dojeżdżający spoza Kutna, e = wypady, h = ciężkie, o = mieszkańcy pracujący, r = przyjeżdżający, t = tło lekkie; skróty wg prefiksu id). Szary/pierwszy = R9.2, drugi = z zakupami i usługami. Wartość = udział podróży, w których pierwszy lub ostatni link trasy wymusza zawrócenie.
**Dwa prawe panele: zmiana natężenia na przekroju GPR [%], osobno lekkie i ciężkie.** Niebieskie słupki = zmiana mediany z 5 runów (r93 względem r91) na kolejnych przekrojach GPR. Szary pas = ± rozrzut między seedami planów w r91 (miara szumu): słupek w pasie = brak zmiany ponad szum. Źródło liczb: `zakupy_porownanie.json`, linki z `output_links.csv.zst` pomnożone przez 1/próbkę, przekroje GPR z `config/`.

## Odtworzenie
```
gh run download 40871126965 -n r93-<r93|r91>-<s4711|s1|s2|p1|p2> -D output/r93_gha/r93-<v>-<id>
uv run python -W ignore reports/etap3/g_zakupy/zakupy_porownanie.py
```
