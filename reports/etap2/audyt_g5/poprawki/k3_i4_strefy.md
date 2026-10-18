# Krok 3 (I4): strefy graniczne per droga i kierunek, waga a priori z GPR

Data: 2026-10-18. Ustalenie: `audyt_g5.md` I4. Decyzja: D21 (pkt I4). Przewidywanie przed zmianą: `k3_i4_przewidywanie.md`.

## Zmiany

- **`pipeline/border_zones.py` (nowy).** Linki graniczne jednego rodzaju połączone węzłami (koniec jednego = początek następnego) to jeden łańcuch, czyli jedna droga przecinająca granicę sieci. 33 + 33 linki dają **11 stref wjazdu i 11 wyjazdu**: A1 płn., A1 płd.-wsch., DK60 płd.-zach., DK60 płn., DK91 płn.-zach., DK91 płd.-zach., DK92 zach., DK92 wsch., DW573, DW583, DW702. Id strefy to link zewnętrzny łańcucha (wjazd: pierwszy od granicy, wyjazd: ostatni). Agent tła startuje na jego końcu albo na nim kończy i przejeżdża resztę łańcucha jak każdy pojazd. Dzięki temu `plans.py` zamienia id strefy na link bez zmian w kodzie (wybór linku jest jednoznaczny, losowanie nie jest potrzebne). Ref drogi pochodzi z OSM (po origid, PBF łódzkie). Wynik: `scenarios/kutno/demand/border_zones.csv`.
- **`pipeline/background_od.py`.** Strefa graniczna = droga i kierunek. Waga a priori = natężenie klasy CLS w dniu roboczym (SDRDR ze strukturą `*_dr`; DW: SDRR, ZAŁOŻENIE z K2) w najbliższym punkcie GPR tej samej drogi, podzielone przez średnią stref granicznych. Gminy bez zmian. Pary wjazd → wyjazd tej samej drogi (zawracanie) są pomijane. W macierzach przed I4 takich par było 623 lekkich i 494 ciężkich podróży/dobę (A1). Usunięty wariant `_cap` (waga = capacity linku).
- **`pipeline/g5_gpr.py`: nowy cel 11104** (DK60 „W. Kutno Płn. /A1/ – Gostynin”, SDRR 9 351, SDRDR 9 737). Punkt leży poza PBF (mazowieckie), ale sieć ma ten odcinek DK60 od węzła A1 do ślepego końca (K1). Cel jest przypisany jawnie do drugiego linku od ślepego końca (`2934227590005f` na południe, `…r` na północ). Na linku wjazdu estymacja nie liczy startującego pojazdu, więc go pomijamy. Udział kierunku 0,5, jak na innych DK jednojezdniowych (D2 w kroku 9). `gpr_linki.csv`: 38 starych wierszy bez zmian bit w bit, 2 nowe; `gpr_punkty.csv` bez zmian.
- **SCPR.** Punkt GPR 11104 to stacja SCPR 14005 Lisica (kolumna `miejsc` = LISICA, ta sama SDRR 9 351), więc karta Lisicy nie daje nowego pomiaru. SCPR 30025 Dzięgielewo (DK92, pikieta 332,310, wielkopolskie, SDRR 2025 = 4 618, ciężkie 1 441) leży poza siecią, za Kłodawą. Odcinek DK92 W w sieci ma już licznik GPR 91121 (SDRDR 4 739, ten sam rząd wielkości), więc nie dodaję go jako celu. Karta służy jako kontrola zgodności rzędu wielkości.
- **`pipeline/g5_baseline.py`**: grupy DK/DW po kolumnie `klasa` zamiast po numerze odcinka. Stara reguła `nr < 20000` zaliczyłaby 11104 do DW. Regresja na R4 (`cls=lcv`): A1, DK w Kutnie, DW i odcinki kontrolne bez zmian co do liczby, a w DK_pozostale doszedł tylko 11104 (model R4 = 0, bo R4 nie miał strefy DK60 N).

## Wagi a priori wjazdów (udział w %)

Przeliczone niezależnie (`skrypty/c3_border_weights.py`): inne grupowanie (klastry 3 km po ref) i natężenia prosto z tabel GDDKiA. Udziały zgodne z `border_weights` estymacji do 0,1 pp dla obu klas (`c3_border_weights.log`).

| droga (wjazd) | linki | przed: capacity linków | **po: lekkie + dostawcze** | **po: ciężkie** | punkt GPR |
|---|---|---|---|---|---|
| DK60 płd.-zach. (Łęczyca) | 9 | **29,1** (audyt: 28,2) | 5,9 | 0,8 | 91115 |
| A1 płd.-wsch. | 3 | 22,2 (23,1) | 32,4 | 32,3 | 91821 |
| DK91 płd.-zach. | 6 | 18,7 (19,5) | 6,2 | 3,6 | 91103 |
| DK92 wsch. (Łowicz) | 3 | 8,3 | 6,5 | 10,2 | 91126 |
| DW702 | 6 | 7,8 | 4,6 | 1,3 | 10049 |
| A1 płn. | 1 | **5,5** (5,8) | 24,5 | 34,6 | 71410 |
| DK60 płn. (Gostynin, K1) | 1 | 2,1 | 10,3 | 7,5 | 11104 |
| DK91 płn.-zach. | 1 | 2,1 | 2,8 | 3,9 | 71306 |
| DK92 zach. (Kłodawa, K1) | 1 | 2,1 | 4,3 | 5,4 | 91121 |
| DW583 | 1 | 1,1 | 0,5 | 0,2 | 14067 |
| DW573 | 1 | 1,1 | 1,9 | 0,3 | 14044 |

„Przed” różni się od audytu o ≤ 0,9 pp, bo K1 dodał 2 strefy. Po zmianie udziały są z definicji równe udziałom natężeń GPR tych dróg. To spełnia zamiar z docstringu („A1 >> DW”), który dotąd był złamany.

**Przewidywanie vs wynik.** Przewidywałem 11 dróg (jest 11), DK60 płd. ok. 5% (jest 5,9%), A1 płn. ok. 23% (jest 24,5%), A1 razem ok. 50% lekkich (jest 57%) i 75–80% ciężkich (jest 67%). Ciężkie są niżej, niż przewidywałem, bo DK92 wsch. i DK60 płn. mają dużo ciężkich (10% i 7,5%). Kierunek i rząd wielkości się zgadzają.

**Pomyłka wyłapana kontrolą.** W pierwszej wersji kontroli brałem najbliższy punkt z pełnego wykazu GDDKiA. Dla A1 płd. to 91822, leżący za węzłem Piątek (ok. 467 km N), podczas gdy wjazd jest na 471,7 km N, czyli na odcinku 91821 „W. Kutno Wsch. – W. Piątek”. Pipeline wybiera 91821, bo `gpr_punkty.csv` obejmuje obszar sieci + 5 km. Kontrola ma teraz jawną tabelę odcinków sprawdzonych z opisu „od–do”, a `border_zones.py` opisuje tę zależność w docstringu.

## Test diagnostyczny estymacji (stary R1, bez runu MATSim)

Te same parametry co R4 (τ 30, drop 10045/91892/91119), model pracujących ze starego R1. Pozwala to rozdzielić efekty: A = stary kod (link = strefa, waga capacity) z celem K2; B = A + cel 11104; C = B + I4. To nie jest nowa baza (R1 trzeba odtworzyć po K1, krok 4).

| | A lekkie | B lekkie | **C lekkie** | A ciężkie | B ciężkie | **C ciężkie** |
|---|---|---|---|---|---|---|
| podróże/dobę | 61 189 | 63 675 | 65 899 | 23 472 | 24 127 | 24 007 |
| tranzyt granica–granica | 22 714 | 24 269 | **14 844** | 10 825 | 11 098 | **8 071** |
| granica–gmina | 31 898 | 32 881 | 42 725 | 11 359 | 11 757 | 13 770 |
| gmina–gmina | 6 577 | 6 525 | 8 330 | 1 289 | 1 272 | 2 167 |
| Objazdowa 91124 (kontrolny) | 139% | 138% | **121%** | 77% | 77% | 72% |
| Bitwy pod Kutnem 91866 (kontrolny) | 92% | 92% | **75%** | 72% | 73% | 61% |
| suma obu | 117% | 117% | **99%** | 75% | 75% | 68% |
| 11104 (nowy cel) | – | 100% | 100% | – | 100% | 100% |
| lokalne 91892 / 91119 / 10045 | 40/43/24% | 40/43/24% | 42/42/21% | 25/34/29% | 25/33/29% | 25/33/28% |

Wnioski:
1. Główny skutek I4: mniej tranzytu granica–granica (lekkie −39%, ciężkie −27%), więcej relacji granica–gmina. Zawyżona waga DK60 płd. i DK91 płd.-zach. tworzyła tranzyt przez Kutno, a przy wagach z GPR jedzie on po A1.
2. Suma odcinków kontrolnych w Kutnie z celem K2: lekkie 117% → 99%. Podział Objazdowa / Bitwy (121% / 75%) to nadal znana rozbieżność K5 (struktura skrętów na węźle). I4 jej nie usuwa, tylko przesuwa obie wartości w dół.
3. Cel 11104 sam niewiele zmienia na innych odcinkach (B ≈ A), ale wiąże ruch nowej strefy DK60 N z pomiarem.
4. Największa para po I4: gm. wiejska Kutno (1002062) ↔ DK60 płd., ok. 4 000 podróży/dobę w każdą stronę, przez Objazdową. Kandydat do kontroli sygnałów ostrzegawczych (krok 4).

## Spójność `background_od.py` ↔ `plans.py`

Plany 25% z diagnostycznymi macierzami C (`k3_plans/validate.log`): walidator ok, sha256 powtarzalny, tło 16 475 = round(Σ × 0,25), ciężkie 6 002. Tło używa 22 linków granicznych i wszystkie są linkami stref (`border_zones.zone`). `border_links.csv` po `plans.py` ma ten sam sha256. Ponowny run estymacji daje ten sam plik macierzy (cmp).

## ZAŁOŻENIA i odrzucone warianty

- ZAŁOŻENIE: waga strefy = natężenie klasy w najbliższym punkcie GPR tej samej drogi (promień 15 km), oba kierunki razem. Wariant z udziałem kierunkowym odłożony do D1/D2 (krok 9). Przy wagach ze średnią 1 stała 0,5 i tak nic nie zmienia.
- ZAŁOŻENIE: strefa = jeden link zewnętrzny łańcucha. Odrzucony wariant: losowanie linku z łańcucha seedem. Zmieniałby on tylko miejsce startu wzdłuż tej samej drogi, a kosztem byłoby dodatkowe losowanie w `plans.py`.
- Odrzucony: waga z sumy capacity drogi. Wszystkie 11 dróg ma punkt GPR, więc ten wariant nie jest potrzebny (kod zatrzymuje się, gdyby punktu zabrakło).
- Odrzucony: SCPR 30025 jako cel. Stacja leży poza siecią, a odcinek w sieci ma licznik 91121.
- Przegląd kodu (skill `code-review`, low, na 4 plikach): 0 ustaleń. Diff przeczytany ręcznie: poprawiony zapis warunku pominięcia pary (zawinięcie linii), wynik estymacji identyczny (cmp).
