# Krok 4B etapu 3: szkoła, plan wdrożenia (bez wdrożenia, do decyzji)

Data: 2026-10-26. Stan: **plan i pytania**, nic w modelu nie zmieniono. Kontekst i źródła: [G_aktywnosci_dodatkowe.md](G_aktywnosci_dodatkowe.md). Decyzje użytkownika (2026-10-25): wariant D (A potem B), tryby dopiero w kroku 5–6, tło zmniejszamy ponowną estymacją O-D, godziny z GBR Gdańsk jako ZAŁOŻENIE, uczniowie spoza Kutna pomijani, łańcuchy to osobny krok. A (D31) zrobione, `work_split = off`.

## 1. Kluczowy problem: w modelu tylko-auto dzieci nie jeżdżą autem
Uczniowie 6–19 lat to 5 029 osób w Kutnie (NSP 2021; 3 728 w wieku 6–15, 1 301 w wieku 16–19). Do szkoły chodzą pieszo, jeżdżą autobusem i rowerem; autem są **wożeni**. Dane (GBR 2022, rys. 39–40, sprawdzone na wykresie): dom–szkoła pieszo 47,5%, samochód osobowy 17,3%, transport zbiorowy 26,2%, rower/hulajnoga 9,0%; szkoła–dom samochód 15,6%. Uczniowie ogółem: pieszo 46,5%, auto 19,1%. To Gdańsk, więc ZAŁOŻENIE.
Dla ruchu drogowego w modelu tylko-auto liczy się więc **rodzic wożący dziecko**, nie sam uczeń. GUS (Łódzkie): podwożenie/odprowadzanie to 4,7% podróży, dom–podwożenie 146 725 na dobę.

## 2. Skala (szacunek, wszystkie liczby z ZAŁOŻENIEM struktury łódzkiej/gdańskiej)
- Podróże dom–szkoła w łódzkim: 263 688 na dobę (GUS tabl. 10) wobec 324 738 osób w wieku 6–19 (NSP 2021) = ok. 0,81 na osobę. Dla Kutna: 5 029 × 0,81 ≈ **4 100 podróży dom–szkoła na dobę, wszystkimi środkami**.
- Wożonych autem (17,3%): ok. **700 dzieci**. Podróż rodzica: dom → szkoła → dom (2 przejazdy autem) rano i podobnie po południu przy odbiorze (15,6%): ok. **2 700 przejazdów autem na dobę**, czyli ok. 6% szacowanych 44,6 tys. podróży autem mieszkańców Kutna i ok. 13% tego, co model ma dziś od mieszkańców (20,5 tys.).
- Dla porównania zakupy i usługi (GUS: 3,8% + 7,4% + 0,9% podróży, auto ok. 60% w Gdańsku): ok. **5 400 przejazdów autem na dobę**, czyli około dwa razy więcej niż szkoła.
Wniosek: szkoła daje **najmniejszy ruch drogowy na jednostkę pracy** (małe i skoncentrowane w czasie, ale w szczycie 7–8). Zakupy/usługi i „inne” mają większy efekt.

## 3. Proponowana konstrukcja (jeśli wdrażamy 4B w trybie tylko-auto)
1. **Agent „rodzic wożący" (`e`)**, osobny od pracujących (łańcuchy to osobny krok): `home → school_drop (kilka minut) → home`, dwa razy w ciągu dnia (poranek i odbiór) albo jako dwa niezależne wyjścia. Atrybuty: dorosły z `license=yes`, `carAvail=always`, wiek z populacji osób 25–55.
2. **Liczba:** dzieci 6–19 lat z `population_kutno.csv` × P(podróż do szkoły) 0,81 (GUS/NSP) × P(auto) 17,3% (rano) i 15,6% (po południu) (GBR). Rodzic dostaje dom w tym samym budynku co dziecko (**bez odtwarzania gospodarstw**: osoba-rodzic nie jest dopasowana do konkretnego dorosłego z populacji, to anonimowy agent w tym budynku; patrz pytanie 2).
3. **Cel:** budynek szkoły z BDOT10k (`OT_BUBD_A`, gm. Kutno: 43 budynki „szkoła podstawowa", 20 „szkoła ponadpodstawowa", 14 przedszkoli, bursa; budynek ≠ placówka, więc trzeba je zgrupować w placówki). Wybór szkoły: dzieci 6–15 lat do **najbliższej szkoły podstawowej** (ZAŁOŻENIE, rejony szkolne to ogólna zasada, brak danych o obwodach), 16–19 lat do szkoły ponadpodstawowej z wagą powierzchni. Liczbę uczniów na placówkę można pobrać z rejestru RSPO (gov.pl, dane publiczne), jeśli się zgodzisz (pytanie 5).
4. **Godziny:** GBR rys. 46: dom–szkoła szczyt 7:00–7:59 (ok. 60% wyjazdów) i 8:00–8:59; szkoła–dom 13:00–14:59 (szczyty 13:00–13:59 i 14:00–14:59, ok. 36% w 14:00–14:59). Digitalizacja jak w D10 (`pipeline/digitize_gbr.py`); rozkład w obrębie godziny jednostajny (ZAŁOŻENIE). Aktywność szkoły z `end_time` (nie `max_dur`), godzina odbioru z rozkładu szkoła–dom.
5. **Config scoringu:** nowy typ aktywności `school` w `config_*pct.xml` (`typicalDuration`, `scoringThisActivityAtAll=false` jak `tlo_*`), bo MATSim bez parametrów nowego typu przerywa run.
6. **Walidacja planów:** `validate_plans.py` rozszerzyć o łańcuch `home-car-school-car-home`, liczby agentów (largest remainder), współrzędne, godziny.
7. **Atrybuty (D30):** uczniowie nie są agentami w modelu tylko-auto, ale populacja Kutna (`population_kutno.csv`) ma wiek 6–19, więc liczba dzieci pochodzi z tego pliku.

## 4. Kroki techniczne i testy
1. Pobranie RSPO (jeśli zgoda) → `data/raw/g_szkola/`, `data/manifest.csv`, `docs/ZRODLA.md`.
2. Grupowanie budynków szkolnych BDOT w placówki; kontrola wizualna w QGIS (kontroluje człowiek).
3. `plans.py`: opcja `school = on|off` (`off` odtwarza R9.2 bajt w bajt), `plans_*` z agentami `e`.
4. Test 2 iteracji lokalnie (nogi car = plany, 0 stuck).
5. Estymacja O-D na GHA (`matsim-od`, plany bez tła z agentami `e`), tło się zmniejsza zgodnie z decyzją; `od_warnings.py`.
6. Porównanie 5 runów (nowy workflow, wzór `matsim-r92`) z R9.2: natężenia GPR vs rozrzut seedów planów, opóźnienia, godziny szczytu 7–8.
7. D32, raport z sekcją „Jak czytać wykres", ROADMAP/PROGRESS.

## 5. Pytania do użytkownika
1. **Czy 4B (szkoła) ma być pierwsze, skoro daje najmniejszy efekt drogowy (ok. 2 700 przejazdów autem na dobę, vs ok. 5 400 dla zakupów i usług)?** Alternatywa: zacząć od zakupów i usług (większy efekt), a szkołę zrobić razem z trybami (kroki 5–6), gdy piesi, rowerzyści i autobus też trafią do modelu i dzieci staną się pełnymi agentami. Moja rekomendacja: **zakupy/usługi najpierw**, szkoła razem z trybami; jeśli chcesz szkołę teraz, to w wersji „rodzic wożący".
2. **Rodzic wożący jako anonimowy agent w budynku dziecka** (bez dopasowania do konkretnej osoby, żeby nie odtwarzać gospodarstw) czy dorosły wybrany z populacji Kutna z mieszkania w tym samym obwodzie? Rekomendacja: anonimowy w budynku, osobne wyjście z domu.
3. **P(auto) dla szkoły 17,3% / 15,6%** z Gdańska (rys. 40) jako jawne ZAŁOŻENIE z wariantem (np. 10% i 25%)? Dla Kutna (mniejsze miasto, dłuższe dojazdy) udział auta jest zwykle wyższy.
4. **Zakres wiekowy:** 6–19 lat (szkoła podstawowa i ponadpodstawowa), przedszkola (3–5 lat) pomijamy, bo GUS Mobilność liczy osoby 6+? Studenci (20–24 lata, Kutno bez własnej uczelni) pomijamy.
5. **Czy mogę pobrać z RSPO (rejestr szkół, gov.pl) listę szkół z adresami i liczbą uczniów** (mały plik, dane publiczne), żeby przypisać wagi placówek zamiast powierzchni budynków?
6. **Przedszkola i żłobki** (dowożenie dzieci 0–5) poza zakresem 4B?
7. **Godzina 8:00–8:59:** GBR podaje szczyt 7:00–7:59; Kutno ma lekcje od 8:00 (typowo), więc przesunięcie rozkładu o 0 min zakładam bez zmian. Zgoda?

## 6. Ograniczenia planu
- Wszystkie udziały środków i godziny są z Gdańska (duże miasto), nie z Kutna.
- Podróże dom–szkoła na osobę 6–19 (0,81) to iloraz GUS (2024, osoby 6+ z ankiety) i NSP 2021; różne roczniki, więc rząd wielkości.
- Uczniowie spoza Kutna pomijani (zgodnie z decyzją), co zaniża ruch do szkół (Kutno to ośrodek powiatu).
- Szacunek ok. 2 700 przejazdów to rząd wielkości: nie uwzględnia łączenia z pracą (łańcuchy, następny krok), więc przy łańcuchach część tego ruchu już istnieje w modelu.
