# Odległość celu wypraw zakupy/usługi: parametr funkcji oporu (research)

Cel: znaleźć w źródłach parametr (β lub krzywą) do wyboru celu wypraw `errands` wg odległości lub czasu. Stan: D32/D34 losują cel bez odległości; przegląd 2026-10-29: mediana dom–cel 1,6 km, 24–32% wypraw autem < 1 km. Pliki lokalne w `data/raw/` (poza gitem). PDF-y czytane przez `pdftotext`; wzory (równania) w PDF-ach nie dają się wyciągnąć jako tekst, to zaznaczono.

## 1. Co znalazłem

| # | Źródło | Gdzie | Liczba | Dla kogo | Ograniczenia |
|---|---|---|---|---|---|
| 1 | KBR Szczecin 2016, etap 4 | `data/raw/badania_ruchu/szczecin_kbr2016_etap4.pdf`, s. 14–16 z 40, tab. 3–5 | funkcja oporu zależna od **czasu przejazdu**, parametr „c”: dom–inne–dom **−0,08**, inne–inne −0,08, dom–praca −0,015, dom–szkoła −0,23, dom–uczelnia −0,15; strefa metropolitalna: dom–inne −0,15 (tab. 5, z modelu SOM); Szczecin↔strefa −0,04 (tab. 4) | Szczecin (ok. 400 tys.), kalibracja do ankiet KBR 2016 i histogramów odległości | Wzór na s. 15 to obiekt-równanie, **nie wyciągnął się z PDF**; jednostka czasu niepodana w tekście. Interpretacja exp(c·t), t w minutach, jest **ZAŁOŻENIEM** (sprawdzenie: dom–praca −0,015 daje płaską krzywą, szkoła −0,23 stromą, kolejność zgodna z intuicją). Zweryfikować na rysunku PDF (render stron niedostępny w tej sesji) |
| 2 | Model ruchu Subregionu Zachodniego woj. śląskiego 2023 (Rybnik, Żory, Jastrzębie, Wodzisław) | `data/raw/badania_ruchu/slaskie_subregion_zachodni_model_ruchu_2023.pdf`, s. 23–25, tab. 4.9–4.12 | funkcja oporu od **odległości U [km]**, ogólny wzór z a, b, c; **dom–inne: a=1, b=−0,40667527, c=−0,13341041** (dom–praca b=−0,11718, c=−0,14716; dom–szkoła b=1,33855, c=−0,62356) | miasta 30–140 tys. i otoczenie (parametry z Modelu Ruchu Woj. Śląskiego, bez własnej estymacji) | Postać wzoru niewyciągnięta; hipoteza f=a·U^b·exp(c·U) (zgodna z dodatnim b dla szkoły = garb). Przy b<0 krzywa **rośnie ku zeru**, czyli faworyzuje bliskie cele. Parametry przejęte, nie kalibrowane lokalnie; rys. 5.3 (rozkład długości dom–inne, s. 29–30) to wykres bez liczb |
| 3 | OMGGS/Trójmiasto, zał. 1 (2023) | `data/raw/badania_ruchu/sump/omggs_sump_model_zalacznik1_2023.pdf`, s. 23–25, tab. 4 | funkcja „Combined” (potęgowo-wykładnicza) od DIS; dom–inne b=−1,528, c=−0,012; inne–dom b=−1,302, c=−0,061; niezwiązane z domem b=−1,081, c=−0,09 | Trójmiasto i region, kalibracja do dzienniczków GBR 2022 w jednominutowych przedziałach | Rozsypana ekstrakcja tabeli: przypisanie wierszy do grup (Gdańsk/Gdynia/region) niepewne. **Nie używać** bez obejrzenia tabeli. Pokazuje tylko typ funkcji |
| 4 | Gdańskie Badania Ruchu 2022, raport 3a | `data/raw/gbr/GBR2022_raport3a.pdf`, rys. 53 (PDF s. 39), rys. 49 (s. 37), rys. 54 (s. 40) | **Rozkład czasu podróży wg motywacji**, dom–inne: ≤5 min **10,9%**; 6–15 **51,6%**; 16–30 **26,1%**; 31–45 7,1%; >45 4,3%. inne–dom: 10,4 / 45,2 / 31,1 / 8,4 / 4,9%. Średni czas dom–inne **18 min**, inne–dom **21 min** (kolejność wartości w strumieniu PDF, zgodna z tekstem s. 36 dla pozostałych motywacji). Samochód (wszystkie cele): ≤5 min 6,1%, 6–15 30,2%, 16–30 41,9%, 31–45 15,2%, >45 6,7%; średnio 25 min | Gdańsk i gminy ościenne (Pruszcz Gd., Żukowo, Kolbudy), wszystkie tryby, podróże ≥250 m | Obszar metropolitalny, nie małe miasto; „inne” to nie tylko zakupy; tryby zmieszane (w ≤5 min są piesi). Czasy rzeczywiste, nie swobodne |
| 5 | GUS Mobilność 2024, łódzkie, tabl. 11 | `data/raw/gus_transport/mobilnosc_transportowa_ludnosci_w_polsce_w_2024_r._tablice.xlsx`, arkusz „Tabl. 11” | podróże wg czasu (łódzkie, 3 958 088): 1–5 min 157 821; 6–10 809 750; 11–15 760 665; 16–20 501 111; 21–25 271 786; 26–30 441 673; 31–40 347 355; 41–50 226 213… → ≤10 min 24,5%, ≤15 min 43,7%, ≤20 min 56,3%, **mediana ok. 17–18 min** (liczone z komórek) | województwo, wszystkie cele i tryby | Brak podziału wg celu i wielkości miejscowości, brak odległości; praca i dojazdy międzygminne zawyżają czas. Nie nadaje się jako cel dla zakupów, tylko jako górne ograniczenie |
| 6 | Toruń/MOFT 2022, Olsztyn 2018, KBR Warszawa/Kraków | patrz `badania_ruchu_PL.md` | średni czas samochodem: Toruń 21 min (miasto 19 wszystkie tryby), Olsztyn 27 min, Gdańsk 25 min; Kraków 2018 odległość samochodem prawie 7 km | miasta 170–800 tys. | Wszystkie cele, nie zakupy; dużo większe od Kutna. Tylko dla porządku wielkości |
| 7 | SUMP ŁOM 2024, zał. 2, s. 21, wykres 19 (wg `sump_lodzkie.md`, nie otwierany ponownie) | `data/raw/badania_ruchu/sump_lodzkie/sump_lom_zal2_badania_spoleczne.pdf` | zakupy „w bezpośredniej bliskości domu” (ta sama gmina/dzielnica) **88,3%** respondentów; praca 62,2% | ŁOM (Łódź + 29 gmin) | Deklaracja, ankieta uproszczona; wskazuje, że zakupy są lokalne, bez liczby km |
| 8 | Horni, Nagel, Axhausen (red.), literatura MATSim (Horni i Axhausen, STRC 2012; praca doktorska Horni, ETH) | https://strc.ch/2012/Horni_Axhausen.pdf (PDF tylko przeglądowy), https://research-collection.ethz.ch/handle/20.500.11850/9465 | **brak wartości β** w pobranym tekście (przegląd, bez tabel) | Szwajcaria | Wartości z Zurychu i tak nie przenosiłbym na Kutno; pełna dysertacja nie pobrana |

Nie znalazłem: rozkładu długości w km dla zakupów/usług autem w mieście ok. 40 tys.; udziału podróży < 1 km wg celu i trybu (d); GUS Mobilność 2024 nie podaje odległości ani czasu wg celu (sprawdzone: tabl. 11 tylko czas łącznie; wyszukiwanie w sieci nic więcej nie dało). Żadne źródło nie dotyczy Kutna ani miasta tej wielkości w zakupach.

## 2. Wnioski z liczb

- Z GBR 2022 dom–inne: 62,5% podróży trwa ≤15 min, 88,6% ≤30 min, 10,9% ≤5 min (wszystkie tryby, w tym pieszo). Model Kutna ma 24–32% wypraw autem < 1 km (ok. 2 min jazdy), więc krótkie podróże są prawdopodobnie przeszacowane względem ≤5 min = 10,9% w Gdańsku. Zastrzeżenie: Gdańsk to duża aglomeracja, w Kutnie (gm. 33 km², czasy w mieście rzadko > 10 min) krótkich jest z natury więcej.
- Gdyby cele leżały w gęstości równomiernej na płaszczyźnie, gęstość czasu podróży to t·exp(−βt) (rozkład Gamma, średnia 2/β). Dopasowanie do GBR dom–inne (≤15 min = 62,5%) daje **β ≈ 0,14/min** (średnia 14 min; ≤5 min 15,8%, ≤30 min 92,4%, GBR 10,9% i 88,6%). Szczecin c=−0,08 daje średnio 25 min i ≤15 min tylko 34%, bo to parametr modelu grawitacyjnego z atrakcjami rejonów i granicami miasta, nie rozkładu gołej płaszczyzny. Obliczenie własne, nie ze źródła; uproszczone (bez granic miasta).
- Dotychczasowe tło (τ = 30 min, czyli β ≈ 0,033/min) jest ok. 2,4× słabsze niż Szczecin i 4× słabsze niż dopasowanie do GBR; dla wypraw lokalnych byłoby prawie bez efektu.
- Kutno jest małe: przy t ≤ 10 min waga exp(−β·t) spada najwyżej do 0,45 (β = 0,08) lub 0,25 (β = 0,14). Efekt będzie umiarkowany; największa zmiana to odcięcie cieni skrajnych celów (strefa przemysłowa, obrzeża), nie ucięcie bliskich.

## 3. Rekomendacja

**Funkcja:** waga celu = W_j · exp(−β · t_ij), t_ij = czas swobodny autem dom→cel w minutach (z sieci), W_j = dotychczasowa waga (obrys budynku lub liczba sklepów OSM). To ta sama postać co tło, tylko τ → 1/β, więc kod tła można ponownie użyć.

**Parametr (źródło):** β = **0,08/min** (KBR Szczecin 2016, tab. 3, dom–inne–dom, c = −0,08). Warunek: potwierdzić jednostkę (min) i postać exp(c·t) na rysunku wzoru w PDF s. 15 (render stron nie był dostępny w tej sesji). Do czasu potwierdzenia to ZAŁOŻENIE.

**Kalibracja:** nie dopasowywać do średniej km ze źródła (brak jej dla Kutna), tylko do **rozkładu czasu** z GBR 2022 rys. 53 (dom–inne), traktowanego jako kontrola górna:
- po zmianie udział wypraw autem z t ≤ 5 min nie powinien przekraczać ok. 11–16%, a t ≤ 15 min powinien wynosić ok. 60–90% (Kutno jest mniejsze, więc więcej niż w Gdańsku jest dopuszczalne);
- udział < 1 km (D34) powinien wyraźnie spaść z 24–32% (cel: do czasu ≤ ok. 15% = ZAŁOŻENIE, bez źródła).

**Warianty (do porównania w przeglądzie, 2 iteracje wystarczą do wygenerowania planów):**
| Wariant | β [1/min] | Źródło |
|---|---|---|
| A (baza) | 0,08 | Szczecin KBR 2016, tab. 3 (jednostka do potwierdzenia) |
| B (silniejszy) | 0,14 | własne dopasowanie do GBR 2022 rys. 53, dom–inne (§2) |
| C (słabszy) | 0,033 | obecne τ = 30 min z tła (referencja, brak źródła dla wypraw) |

Dobrać wariant po rozkładzie t_ij wypraw w planach (przed uruchomieniem MATSim), nie po wynikach symulacji. Nie używać funkcji z Śląska (b<0 faworyzuje cele tuż obok, czyli pogłębia obecny problem) ani z Trójmiasta (tabela nieczytelna).

## 4. Założenia i luki
- ZAŁOŻENIE: wzór Szczecina to exp(c·t), t w minutach (§1 poz. 1). Wariant: gdyby t było w innej jednostce, β skaluje się odpowiednio; wtedy użyć wariantu B.
- ZAŁOŻENIE: czas swobodny autem aproksymuje czas z sieci przy zatorach (w Kutnie małe różnice).
- ZAŁOŻENIE: „inne” (GBR, Szczecin) przybliża zakupy i usługi (razem ok. połowy wypraw wg `G_aktywnosci_dodatkowe.md`).
- Luka: brak rozkładu km/min dla zakupów w mieście < 100 tys.; propozycja: zapytać ZIT Olsztyna o surowe dane SUMBA lub MZK/UM Kutno o ewentualny pomiar; po 2027 sprawdzić Łódzkie Badanie Ruchu.
- Luka: udział podróży < 1 km wg celu i trybu (d): brak w źródłach.
- Nie sprawdziłem: Kalisz 2013, Bochnia, Radom (tylko wyszukiwanie tekstu po „zakup”/„czas”: brak rozkładów wg celu).

## 5. Do ZRODLA.md (wiersze dla sesji głównej)

| Parametr | Wartość | Źródło | Uwagi |
|---|---|---|---|
| β wyboru celu zakupy/usługi (wariant A) | 0,08 /min, f = exp(−β·t) | KBR Szczecin 2016 etap 4, `data/raw/badania_ruchu/szczecin_kbr2016_etap4.pdf`, s. 15–16, tab. 3 (dom–inne–dom, c = −0,08) | jednostka i postać wzoru do potwierdzenia na rysunku PDF; ZAŁOŻENIE do tego czasu |
| Rozkład czasu podróży dom–inne (kontrola) | ≤5: 10,9%; 6–15: 51,6%; 16–30: 26,1%; 31–45: 7,1%; >45: 4,3% | GBR 2022 raport 3a, `data/raw/gbr/GBR2022_raport3a.pdf`, rys. 53 (PDF s. 39) | Gdańsk i gminy, wszystkie tryby; kontrola, nie kalibracja |
| Średni czas podróży dom–inne / inne–dom | 18 / 21 min | GBR 2022 raport 3a, rys. 49 (PDF s. 37) | odczyt wg kolejności wartości w PDF |
| Czas podróży wg przedziałów, łódzkie | ≤10 min 24,5%; ≤15 43,7%; ≤20 56,3% | GUS Mobilność 2024, tablice, tabl. 11, wiersz łódzkie | wszystkie cele i tryby; górne ograniczenie |
| Zakupy w pobliżu domu | 88,3% (ta sama gmina/dzielnica) | SUMP ŁOM 2024, zał. 2, s. 21, wykres 19 | deklaracje; za `sump_lodzkie.md` |
| Funkcja oporu dom–inne, Śląsk (odrzucona) | a=1, b=−0,40667527, c=−0,13341041 (U w km) | Model ruchu Subregionu Zachodniego woj. śląskiego 2023, `slaskie_subregion_zachodni_model_ruchu_2023.pdf`, s. 24, tab. 4.9–4.12 | postać wzoru niepotwierdzona; b<0 nie nadaje się |
| β ≈ 0,14 /min (wariant B) | wyliczone | własne dopasowanie rozkładu Gamma do GBR 2022 rys. 53 (≤15 min = 62,5%) | uproszczenie: płaszczyzna bez granic miasta |
