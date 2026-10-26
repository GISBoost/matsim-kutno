# Krok 4 etapu 3: dodatkowe aktywności (research, bez wdrożenia)

Data: 2026-10-25. Stan: **sam research i pytania do użytkownika**, nic nie zmieniono w modelu ani w configu. Wdrożenie dopiero po decyzji (D31).

## 1. Co jest dziś w modelu
- Pracujący jadą autem `home → work → home`; reszta mieszkańców nie podróżuje. Szkoła, zakupy, sprawy, odprowadzanie dzieci, rekreacja: brak.
- Ruch „tła" (lekkie, ciężkie) jest estymowany z odczytów GPR tak, żeby suma modelu zgadzała się z licznikami (D19, D21). Czyli tło już dziś zawiera w sobie część ruchu, który w rzeczywistości robią mieszkańcy w celach innych niż praca.
- Aktywność pracy ma jeden link przypięcia (D29), stąd ostatnie zawrotki przy pracy.

## 2. Co mówią dane (GUS Mobilność 2024, łódzkie, typowy dzień roboczy, 6+)
Plik: `data/raw/gus_transport/…_tablice.xlsx`, tabl. 4, 8, 9, 10, 11 (liczby sprawdzone w arkuszach). Tylko województwa, bez wielkości miejscowości, bez płci i wieku, bez godzin.

| wielkość | łódzkie | uwaga |
|---|---|---|
| osoby 6+ (tabl. 4) | 2 146 153 | 572 511 (26,7%) nie robi podróży |
| podróże/dzień (tabl. 8) | 3 958 088 | 1,84 na osobę 6+, 2,52 na podróżującego |
| podróżujący wg liczby podróży | 1: 25 897, **2: 1 111 713 (70,6%)**, 3: 148 824, 4: 225 265, 5: 31 469, 6+: 30 475 | dzień to najczęściej dom–cel–dom |
| podróże wg celu końcowego (tabl. 9) | dom 46,0%, praca 19,7%, szkoła 6,7%, zakupy w centrach 3,8%, inne zakupy 7,4%, usługi 0,9%, odwiedziny 2,4%, rekreacja 2,9%, podwożenie 4,7%, medyczne 2,1%, służbowe 1,0%, reszta 2,3% | „szkoła" = kol. szkoła; uczelnia i inne w pozostałych |
| pary dom–praca + praca–dom (tabl. 10) | 730 740 + 661 460 = 35,2% podróży | dom–szkoła 263 688 (6,7%), dom–inne zakupy 229 380 (5,8%), dom–podwożenie 146 725 (3,7%) |
| środek transportu, wszystkie cele (tabl. 13) | auto 60,1% (kierowca 47,9%), pieszo 20,5%, rower 5,2%, autobus miejski 7,2% | kategorie nie rozłączne |
| czas trwania podróży (tabl. 11) | do 10 min: 24,5%; 11–20: 31,9%; 21–30: 18,0%; 31–60: 18,6%; ponad 60: 7,1% | |

**Błędy względne (tabl. 29, 30), łódzkie:** dom–praca 2,9%, dom–szkoła 4,0%, dom–inne zakupy 8,9%, dom–zakupy w centrach 12,3%, dom–odwiedziny 13,3%, dom–rekreacja 11,6%, dom–podwożenie 12,7%, dom–medyczne 13,3%, dom–usługi **22,5%** (>20%, według GUS wartość „obarczona znacznym błędem"), podwożenie–inne **20,3%**. Czas trwania: 1–5 min 16,2%, ponad 90 min 25–29%.

**Skala dla Kutna (szacunek, ZAŁOŻENIE: struktura jak w łódzkim, bez korekty na małe miasto):** mieszkańców 6+ w populacji Kutna 40 232, więc 74 tys. podróży na dobę, z tego 44,6 tys. autem (60,1%), 35,5 tys. jako kierowca (47,9%). Obecny model ma od mieszkańców 20,5 tys. podróży autem (17 255 pracujących × 0,593 × 2), czyli ok. połowy. Reszta (ok. 24 tys. podróży autem) to cele inne niż praca albo wyjazdy poza model.
Uwaga: to rząd wielkości; 74 tys. liczy też podróże piesze i rowerowe, które w modelu car-only nie występują.

## 3. Czego GUS nie daje
- **Godziny:** brak rozkładu godzin wyjazdu wg celu. Jedyne źródło liczbowo-graficzne w repo: **Gdańskie Badania Ruchu 2022, raport 3a, rys. 46** (`data/raw/gbr/GBR2022_raport3a.pdf`, s. 36, **sprawdzone, obejrzany wykres**): dom–szkoła ostry szczyt 7:00–7:59 (ok. 60% wyjazdów), szkoła–dom szczyt 14:00–14:59 (ok. 36%) i drugi 13:00–13:59, dom–inne szeroki szczyt 9:00–11:59 (ok. 17%), inne–dom rośnie od 13:00, dom–rekreacja i rekreacja–dom szczyty 16:00–18:59 i późny wieczór. Tylko wykres, przedziały 1 h, wartości do odczytu z rysunku (błąd ok. ±1–2 pp). Gdańsk jest dużym miastem; dla Kutna to ZAŁOŻENIE.
- **Czas pobytu** (jak długo trwają zakupy, usługi): nie ma w GUS Mobilność. GUS Budżet czasu 2023 (nowo pobrane, `data/raw/g_aktywnosci/`, tabl. 1–2, **format h.mm: 0.57 = 57 min**): *zakupy i korzystanie z usług* wykonuje dziennie **46,3%** osób 15+, średnio **57 min** na wykonującego (kobiety 50,4% / 57 min, mężczyźni 41,0% / 56 min; grupy wieku: 15–19 lat 21,7%, 25–34 42,96%, 65+ 49,96% / 60 min); *nauka* wykonuje 62,3% osób 15–19 lat, 4,19 h średnio ogółem. To czas wykonywania czynności, **bez** dojazdu, i wlicza zakupy online, więc to dolna granica dla pobytu poza domem.
- **Łańcuchy:** czy zakupy są po drodze z pracy (praca→zakupy→dom) czy osobnym wyjściem. Z GUS: 70,6% podróżujących robi 2 podróże (dom–cel–dom), 14,3% 4, 9,5% 3; a co to za cele, tabl. nie mówią. Para praca–dom jest 35% podróży, więc udział łańcuchów „praca–zakupy–dom" jest przynajmniej ograniczony od góry przez 3- i 4-podróżowych (24%).
- **Wiek × cel:** GUS łódzkie nie rozbija celu wg wieku. Gdańsk (rys. 23–26): ruchliwość 25–44 lata 2,0, 45–64 1,8, 65+ 1,1, uczniowie 1,8, pracujący poza domem 2,2, emeryci 1,1 (podróży/dzień na osobę). To jedyna zależność od wieku w repo, z miasta metropolitalnego.
- **Szkoły w Kutnie:** w BDOT10k (gm. Kutno, `OT_BUBD_A`) jest 43 budynków „szkoła podstawowa", 20 „szkoła ponadpodstawowa", 14 przedszkoli i bursa (budynek ≠ placówka: kilka budynków na jedną szkołę). Brak liczby uczniów na szkołę. Z OSM: tylko 5 `amenity=school` w budynkach regionu, więc BDOT jest lepszym źródłem. Handel: BDOT 232 „obiekty handlowo-usługowe" + 59 domów towarowych/handlowych w gminie; OSM 31 `shop=supermarket`, 2 `shop=mall`.
- **Uczniowie z innych gmin** (Kutno jest ośrodkiem powiatu): brak danych; analogicznie do przyjeżdżających do pracy.
- **Dane dla Kutna lub podobnego miasta:** szukałem SUMP/KBR dla Kutna: nie znalazłem (wyszukiwarka). Bochnia i Radom (`data/raw/g4/`) podają podział modalny, nie cele ani godziny (nie sprawdzałem ponownie całych PDF pod kątem celów podróży; do zrobienia w razie decyzji o ich użyciu).

## 4. Dlaczego to nie jest „dodanie trzech aktywności"
1. **Bilans ruchu.** Dodanie ok. 24 tys. podróży autem na dobę (szacunek wyżej) do modelu, którego tło jest dopasowane do liczników, **podwoi część ruchu**, jeśli tło nie zostanie zmniejszone. Trzeba ponownie estymować macierze O-D (workflow `matsim-od`, krok 0 gotowy), a w estymacji jako „znany popyt" użyć nowych planów. To wymaga decyzji, czy dopasowujemy tło do tych samych liczników GPR (wtedy tło się zmniejszy), czy zostawiamy tło i patrzymy, o ile model przekracza liczniki.
2. **Tryb.** Dziś wszyscy z `car_share` jadą autem, reszta nie występuje. Dla szkoły i zakupów wiele podróży jest pieszych (łódzkie: 20,5% wszystkich podróży, w krótkich podróżach znacznie więcej). Przy modelu car-only trzeba zdecydować, czy do planów trafia tylko część podróży (autowa), czy wszystkie z `walk` (teleportowane) i tryb pojawi się dopiero w kroku 5–6.
3. **Liczba osób.** Dziś są agenci tylko dla pracujących (3 739 przy 25%). Szkoła wymaga dzieci/uczniów, zakupy osób niepracujących. To wprost wynika z atrybutów kroku 3 (wiek, `license`, `carAvail`), ale populacja `population_kutno.csv` ma już 42 255 osób, więc dane do wylosowania są.
4. **Zawrotka przy pracy** (D29): rozdzielenie aktywności pracy na dwie (`work_arrival` / `work_departure`, osobne linki) rozwiązuje ją niezależnie od aktywności dodatkowych i jest tańsze (zmiana jednej funkcji, jak `home_link_end`). Można to zrobić osobno i wcześniej.

## 5. Warianty realizacji (do wyboru)
- **A. Najmniejszy krok:** tylko rozdzielenie aktywności pracy (usuwa zawrotki, D29), bez nowych celów. Zmienia dziś tylko linki. Estymacja O-D niepotrzebna (popyt ten sam), test jak w D29 (przepływ vs rozrzut planów).
- **B. Szkoła (obowiązkowa), reszta potem:** agenci uczniowie 6–19 lat (5 059 osób w populacji Kutna), łańcuch `home → school → home`, godziny z GBR rys. 46 (ZAŁOŻENIE), cel w BDOT „szkoła", tryb: odwożenie autem przez rodzica? (GUS: podwożenie 4,7% podróży). Wymaga ponownej estymacji O-D.
- **C. Pełny zestaw:** B plus zakupy/usługi, sprawy, rekreacja, odwiedziny dla osób nie jadących do pracy i jako łańcuchy po pracy. Największy wpływ i największa liczba założeń; kalibracja do liczników zmieni się.
- **D. Zestaw w dwóch krokach:** A najpierw (zmiana techniczna), potem B/C z decyzją o bilansie tła.

## 6. Co należałoby zrobić w każdym wariancie (jeśli B lub C)
1. Wygenerować osoby: cel i liczba podróży z tabl. 4 i 9–10 GUS (jako rozkłady, łódzkie), przypisać do osób wg atrybutów (wiek, praca, `license`).
2. Wybrać lokalizacje: szkoły (BDOT, waga: powierzchnia), handel (BDOT, waga: powierzchnia sprzedaży ≈ powierzchnia obrysu, ZAŁOŻENIE), usługi, zdrowie; rozkład odległości z czasu trwania podróży (tabl. 11) jako kontrola, nie jako kalibracja.
3. Godziny: GBR rys. 46 (digitalizacja słupków/krzywych), czas pobytu z BCL 2023 jako ograniczenie dolne.
4. Zmiana zachowania aktywności: `end_time` albo `max_dur`, nigdy oba (CLAUDE.md), typy aktywności z `scoring` w configu (dziś tylko `home`, `work`).
5. Nowa estymacja O-D (workflow `matsim-od`), potem runy 25% × 50 it. na GHA, porównanie z rozrzutem seedów planów i z licznikami GPR.
6. Test akceptacji: liczba podróży/dobę na osobę 6+ z modelu vs GUS (1,84, tabl. 4), rozkład celów vs tabl. 9, godzin vs GBR, wynik w raporcie z sekcją „Jak czytać wykres".

## 7. Pytania do użytkownika (bez nich nie zgaduję)
1. **Zakres:** wariant A, B, C czy D (kolejność)? Moja rekomendacja: **D**, A pierwszy (tani, usuwa ostatnie zawrotki), potem B (szkoła), C na końcu.
2. **Tryb:** czy w kroku 4 zostajemy w car-only (podróże piesze poza modelem, ruch autowy z nowych celów liczymy z udziału auta 60,1% jako ZAŁOŻENIE) czy dodajemy teleportowane `walk` i `bike` do planów już teraz? Tryby to krok 5–6.
3. **Bilans tła:** po dodaniu podróży mieszkańców tło ma się zmniejszyć (ponowna estymacja do tych samych liczników GPR), czy mam zostawić tło i pokazać, o ile model przekracza liczniki?
4. **Godziny:** czy mogę użyć Gdańska (GBR 2022, rys. 46) jako ZAŁOŻENIA, z oznaczeniem, że to duże miasto, tak jak w D10? Alternatywa: prosić UM Kutno o badanie (nie jest w zasięgu agenta).
5. **Uczniowie spoza Kutna** (liceum, technikum w ośrodku powiatu): pomijamy w kroku 4 (uczniowie tylko z Kutna do szkół w Kutnie), czy mam dodać przyjeżdżających uczniów jako ZAŁOŻENIE z proporcją zbliżoną do pracy (D16)?
6. **Czy łączyć łańcuchy** (praca → zakupy → dom) w pierwszej wersji, czy osobne wyjścia z domu (dom → cel → dom, 70,6% podróżujących wg GUS)? Rekomendacja: osobne wyjścia, bo to dominujący przypadek w danych, a łańcuchy to osobny krok.

## 8. Ograniczenia tego researchu
- Brak źródeł dla Kutna; łódzkie jako przybliżenie dla miasta 42 tys. (struktura celów w miastach tej wielkości może być inna: więcej samochodu, mniej pieszo).
- Digitalizacja GBR rys. 46 nie była wykonana (to implementacja); odczyt wartości ze szczytów jest tylko opisowy.
- Szacunek „24 tys. podróży autem" jest różnicą dwóch przybliżeń (łódzkie × populacja 6+ vs model); do weryfikacji w kroku wdrożenia.
- BCL 2023 liczy 15+; wartości w formacie `h.mm`, w niektórych komórkach przecinek zamiast kropki.

## 9. Korekta po przeglądzie badań ruchu (2026-10-26, [badania_ruchu_PL.md](badania_ruchu_PL.md)) i decyzje użytkownika
- **Kolejność:** użytkownik 2026-10-26: najpierw **zakupy i usługi** (krok 4C), szkoła i tryby później. Łańcuchy osobno. Tło zmniejszane ponowną estymacją O-D, godziny z GBR 2022 (ZAŁOŻENIE).
- **Ruchliwość, kontrola zewnętrzna:** GUS łódzkie 1,84 podróży/os. 6+ mieści się w przedziale badań dzienniczkowych miast 20–200 tys.: Toruń 1,7 (poza Toruniem 1,5), Olsztyn 1,77, Szczecin 1,90, Radom 2,74 (CATI, zawyżone). Parametry bierzemy z GUS dla łódzkiego, inne badania służą kontroli.
- **Podróże dom–„inne" na osobę:** GUS łódzkie (dom–zakupy CH, inne zakupy, usługi, odwiedziny, rekreacja, podwożenie, medyczne = 743 321 na 2 146 153 osób 6+) = **0,346**; Szczecin KBR 2016 (tab. 1, s. 12): dom–inne **0,343**. Zgodność potwierdza skalę. Zakupy i usługi to ok. połowa (0,167).
- **Udział samochodu poza pracą:** Radom (CATI, ośrodek centralny + gminy) podróże fakultatywne **53,2%** (samochód razem z pasażerami), obligatoryjne 67,3%; Toruń poza miastem 54,9%; Gdańsk dom–inne 38,2% (do) i 43,0% (z). GUS łódzkie wszystkie cele 60,1% (kierowca 47,9%, czyli 79,7% jazd autem to kierowcy). Baza 4C: 53,2% × 0,797 = **42,4% jako kierowca**; warianty 30,4% (Gdańsk) i 47,9% (GUS wszystkie cele).
- **Szkoła (4B, później):** do walidacji dom–szkoła na osobę: GUS 0,123, Szczecin 0,09, Radom 0,108 (3,95% × 2,74). Przedział 0,09–0,12.
- **Czego nie ma:** godzin wyjazdu wg celu poza GBR (Olsztyn ma wykres godzin dnia roboczego, Kraków 13% podróży w godzinie 7–8); to prośba do ZIT Olsztyn o bazę, nie do zrobienia automatycznie.
