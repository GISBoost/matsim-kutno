# SUMP / PZMM jako źródło parametrów popytu (Polska)

Data: 2026-10-29. Uzupełnienie [badania_ruchu_PL.md](badania_ruchu_PL.md). Cel: sprawdzić, co da się wyciągnąć z Planów Zrównoważonej Mobilności Miejskiej (SUMP/PZMM) poza tym, co już mamy z KBR.
Zasada jak poprzednio: tylko liczby widoczne w tekście dokumentu (strona/tabela). Pliki w `data/raw/badania_ruchu/sump/` (wpisy w `data/manifest.csv`, wiersze w `docs/ZRODLA.md`). Numery stron to numery drukowane w dokumencie.

## 1. Wynik testu

**Pozytywny, ale selektywnie.** SUMP sam w sobie rzadko jest źródłem; wartość ma, gdy diagnoza przytacza wyniki własnych badań ruchu (wywiady/dzienniczki) lub gdy do planu dołączono raport modelu ruchu. Z 9 otwartych dokumentów:

| Dokument | Użyteczny? | Co daje |
|---|---|---|
| Rzeszów ROF, raport diagnostyczny 2025 | **tak** | Wyniki Rzeszowskich Badań Ruchu 2022/23 (wywiady PAPI): podział modalny miasta i gmin, ruchliwość, łańcuchy powrotne, cele |
| Śląskie, Subregion Zachodni, raport modelu ruchu 2023 | **tak** | Ruchliwość per powiat, udział samochód/TZ per motywacja, liczba podróży w modelu |
| Bydgoski OF, SUMP (pełny) | **częściowo** | Dzienniczek w 6 małych gminach: 1,73 podróży/os., >67% samochodem, godziny szczytu |
| OMGGS (Trójmiasto), załącznik 1 modelu 2023 | metoda | Jak z GBR 2022 zrobiono funkcje udziału pieszych i rozkład godzinowy; liczb nie wyciągnąłem (tabele rozsypane przy ekstrakcji) |
| GZM / Subregion Centralny „Dobra Mobilność 30/50" | marginalnie | Jeden wskaźnik bazowy: 44% podróży samochodem, 58% do pracy (2018) |
| Wrocław, diagnoza PZMM | nie | Podział modalny tylko jako rysunek (KBR 2010/11, WDS 2017), nieczytelny z tekstu |
| Lublin: SUMP MOF Ryki (`sump_mofr`) | nie | Mała gmina, ankieta opinii, brak danych o podróżach |
| Grudziądź MOF, diagnoza | nie | Tabela celów × środek z ankiety opinii; wartości są wielokrotnościami 0,88% = 1/113, więc n≈113. Odrzucone |
| Bydgoszcz, slajdy diagnozy | nie | Tylko wnioski jakościowe (szczyt 7–8 i 15–16 w pomiarach ruchu) |

Uwaga: wyszukiwarka nie znalazła raportów z liczbami dla SUMP Lublina (LOM), Białegostoku, Poznania, Łodzi (SŁOM: tylko prognoza środowiskowa z celami), Opola, Zielonej Góry i Gorzowa; samych tych dokumentów nie otwierałem. Radom, Toruń, Olsztyn, Kielce, Szczecin, Kraków: już w badania_ruchu_PL.md.

## 2. Rzeszów ROF (najlepszy nowy wynik)

Źródło: Raport diagnostyczno-strategiczny stanu istniejącego na potrzeby SUMP dla ROF, BRMR Rzeszów, luty 2025. https://brmr.erzeszow.pl/wp-content/uploads/2025/02/Raport_diagnostyczno_strategiczny_stanu_istniejacego_na_potrzeby_SUMP_dla_ROF.pdf (plik `rzeszow_rof_sump_diagnoza_2025.pdf`, 35 MB).

Metoda (s. 291): Rzeszowskie Badania Ruchu, część ankietowa „Raport cząstkowy 6 RBR", wykonana przez GUS (s. 93: „przeprowadzonych w 2023 r. przez GUS"), PAPI, 12.12.2022–28.02.2023, 15 gmin ROF. Wylosowano 48 tys. gospodarstw (24 tys. w Rzeszowie), wzięło udział 4 556 gospodarstw (12 898 osób); odpowiedzi 12 001 osób w wieku ≥6 lat. Rzeszów: 2 599 gospodarstw, 6 442 osoby, 6 000 odpowiedzi. Dni: wtorek–czwartek oraz weekend (s. 93, 101).

| Parametr | Wartość | Gdzie |
|---|---|---|
| Podział modalny Rzeszowa, dzień roboczy (wszystkie podróże, główny środek) | kierowca 43,3%, pieszo 28,0%, autobus miejski/podmiejski 15,7%, pasażer 10,2%, rower prywatny 1,3%, taksówka/Uber 0,6%, dostawczy 0,3% | s. 93, wykres 5.1 |
| Pieszo w weekend (Rzeszów) | 36,3% | s. 293, s. 101 |
| Gminy ROF poza Rzeszowem: kierowca | najwięcej Lubenia i Łańcut ok. 64%, najmniej Tyczyn 36,9% | s. 96 |
| Pieszo, gminy | Boguchwała 31,3%, Łańcut 27,2%, Trzebownisko 6,4% (rower tam 6,1%) | s. 96, 101 |
| ROF łącznie: kierowca / pasażer | 48,4% / 13% badanych w dzień roboczy (udział osób, nie podróży) | s. 292 |
| Średnia liczba podróży doby roboczej **na podróżującego** | 2,4 (ROF); to nie jest ruchliwość na mieszkańca | s. 292 |
| Podróże ≤15 min / 16–30 min | 45,5% / 35,8% | s. 292 |
| Osoby zaczynające dzień z domu, które kończą powrotem do domu | ROF 67,9% (podróże pośrednie 27,6%); Rzeszów 63,6% (pośrednie 31,9%) | s. 292–293 |
| Cel podróży Rzeszowian, dzień roboczy | dom 44,4%, praca 20,3% | s. 294 |
| Gospodarstwa z samochodem / samochodów na gospodarstwo | ROF 72,8% / 1,2 (1,6 wśród zmotoryzowanych); Rzeszów 65,6% / 1,0; obłożenie samochodu 1,6 | s. 292–293 |
| Pracujący poza domem wśród badanych | ROF 39,5%, Rzeszów 38,6%; praca mieszana 3,5% / 4,2% | s. 291, 293 |
| Szczyt ruchu pieszego | 7:30–8:30 i 15:00–16:00 | s. 101 |

Dla Kutna: to najlepszy dostępny przykład badania GUS-owego **z gminami wiejskimi i podmiejskimi obok miasta**, z udziałem samochodu 37–64% zależnie od gminy. Rozstęp między gminami pokazuje, że jednego „udziału samochodu dla małego miasta" nie ma. Bez mikrodanych raport nie daje godzin ani łańcuchów poza udziałem powrotów do domu (ok. 64–68% dni z jednym powrotem).

## 3. Śląskie, Subregion Zachodni (model ruchu SUMP, 2023)

Źródło: SUMP Subregionu Zachodniego, Raport – model ruchu, 23.10.2023. https://subregion.pl/wp-content/uploads/2023/12/SUMP-SZ_Raport-model-ruchu_2023-10-23.pdf (`slaskie_subregion_zachodni_model_ruchu_2023.pdf`).

Metoda (s. 7–9): ruchliwość z badań CATI wykonanych na potrzeby SUMP, korygowana wynikami KBR 2021 (podróże niewykonywane i piesze); podział modalny z ankiet KBR 2021. **CATI, więc wartości wyższe niż w wywiadach domowych** (zob. badania_ruchu_PL.md).

| Parametr | Wartość | Gdzie |
|---|---|---|
| Wskaźniki ruchliwości per powiat (8 wartości na wykresie) | od 1,99 do 2,56; najwyższy Żory, najniższy Wodzisław Śląski (wg tekstu); przypisania pozostałych słupków do powiatów nie da się odczytać z tekstu | s. 9, wykres 2.1 |
| Podział samochód / transport publiczny w modelu, dom–praca | 84,0% / 16,0% | s. 30, tab. 5.2 |
| praca–dom | 83,8% / 16,2% | j.w. |
| dom–szkoła | 36,1% / 63,9% | j.w. |
| szkoła–dom | 36,5% / 63,5% | j.w. |
| dom–inne | 85,2% / 14,8% | j.w. |
| inne–dom | 85,3% / 14,7% | j.w. |
| Podróże mieszkańców w modelu na dobę | dom–praca 247 007; praca–dom 230 535; dom–szkoła 53 055; szkoła–dom 49 348; dom–inne 200 629; inne–dom 182 534 | s. 29, tab. 5.1 |
| Udział transportu publicznego (bez pieszych), 2022 | 20,7% | s. 44, tab. 8.8 |

Podział dotyczy samochód vs TZ **bez pieszych i roweru** (s. 10: „bardzo wysoki udział samochodu w podróżach niepieszych"). Nie sumuje się z podziałami z Rzeszowa czy Torunia bez doliczenia pieszych.

Dla Kutna: dobry wzorzec **podziału samochód/TZ per cel** dla małych i średnich miast (Żory, Wodzisław, Rybnik, Jastrzębie) oraz relacja liczby podróży dom–praca do dom–szkoła/inne (około 5:1:4, wartość liczona z tab. 5.1).

## 4. Bydgoski OF (małe gminy wokół miasta)

Źródło: Plan Zrównoważonej Mobilności Miejskiej dla BydOF, wersja konsultacyjna. https://www.bydgoszcz.pl/fileadmin/multimedia/WSPOLNE/ZIT_BydOF_Materialy_robocze/Konsultacje_SUMP/Plan_Zrownowazonej_Mobilnosci_dla_Bydgoskiego_Obszaru_Funkcjonalnego.pdf (`bydgoszcz_bydof_sump.pdf`).

- Badanie PAPI w gospodarstwach domowych, losowanie random route, gminy Rojewo, Kcynia, Mrocza, Pruszcz, Barcin, Żnin; **n = 2 284 osoby** (s. 33).
- Z dzienniczka podróży (s. 34): szczyt poranny 7:00–8:00, popołudniowy 14:00–15:00; średnio **1,73 podróży/dzień na ankietowanego**, **ponad 67% samochodem**, transport zbiorowy poniżej 3%; najczęstsze motywacje praca i zakupy.
- Ankieta internetowa n = 688 (s. 34) – nie do parametrów.
- Podsumowanie diagnozy (s. 48): podział zadań dla całego BydOF (średnia za 2020 dla miasta i pozostałych gmin): samochód 65%, TZ 25%, rower 5%, pieszo 5%. Przypis 6 nie wskazuje metody, a 5% pieszo wygląda na zaniżone; traktować jako orientacyjne.

Dla Kutna: najbliższy odpowiednik **małych gmin bez dobrego TZ** (Żnin, Kcynia): 1,73 podróży i >2/3 samochodem. Mniejszy zakres niż Rzeszów (brak rozbicia na gminy w tekście).

## 5. Pozostałe

- **GZM, „Dobra Mobilność 30/50" (2023), tab. 4 wskaźników rezultatu:** udział podróży wyłącznie samochodem (2018): **44% ogółem, 58% do pracy**; cel 2050: 22% i 29%. Źródło bazy: Studium Transportowe Subregionu Centralnego (nie otwarte). Plik 57 MB nie pobrany do repo.
- **OMGGS, załącznik 1 (2023):** model podziału: najpierw udział pieszych jako funkcja potęgowa odległości, osobno dla motywacji (R² 0,91–0,96 w Trójmieście), potem logit samochód/TZ/rower; podstawa to dzienniczki GBR 2022, podróże ≥250 m (s. 27). Tabele współczynników i rozkład godzinowy motywacji (tab. 3, s. 23) są w PDF, ale ekstrakcja tekstu je rozsypała. To ta sama baza co GBR, więc nie rozszerza naszej bazy źródłowej.
- **Wrocław, diagnoza PZMM (2018), s. 78–79:** gospodarstwa z samochodem 60% (2010), 65% (2014); udziały podziału zadań tylko jako rysunki.
- **Repozytorium SUMP** (gov.pl, 30.09.2026, `repozytorium_sump_30092026.pdf`): lista 53 obszarów funkcjonalnych z ocenionymi SUMP (ok. 22,9 mln osób, 61,2% ludności), z wykazem gmin każdego MOF. Bez linków do planów, ale daje komplet do wyboru wzorca po regionie.

## 6. Wnioski

**Najlepsze dla Kutna (z SUMP):** (1) Rzeszów ROF, jedyny z podziałem modalnym i powrotami do domu **per gmina** wg metodyki GUS; (2) Subregion Zachodni śląskie, podział samochód/TZ per cel dla miast 20–100 tys.; (3) BydOF, ruchliwość i udział samochodu w małych gminach wiejsko-miejskich.

**Co SUMP daje, a czego nie:** daje gotowe agregaty (podział modalny, ruchliwość, godziny szczytu, czasem % powrotów do domu). Nie daje rozkładów godzin wyjazdu, łańcuchów ani wag mikro. Te są tylko w raportach KBR/RBR lub mikrodanych (GUS BMTL 2024 ma dzienniczki: prośba do GUS/ZIT, wcześniej niż dalsze szukanie).

**Powtarzalny workflow dla nowego miasta:**
1. W repozytorium SUMP znaleźć MOF miasta i sąsiednie MOF tej samej wielkości w tym samym regionie.
2. Pobrać „raport diagnostyczny" i szukać: `podział zadań`, `modal split`, `ruchliwość`, `podróży na`, `dzienniczek`, `PAPI|CATI|wywiad`, `próba|n=`, `godzina szczytu`. Zawsze notować metodę, rok, wielkość próby, dni tygodnia i próg długości podróży.
3. Nie mieszać CATI (1,99–2,74) z wywiadami domowymi (1,7–1,9); podział samochód/TZ z modelu (bez pieszych) osobno od podziału wszystkich podróży.
4. Wybierać wzorzec: pierwsza kolejność = ta sama klasa wielkości i rola (miasto-rdzeń vs gmina podmiejska), druga = region, trzecia = metoda (wywiady GUS > CATI).
5. Brak własnych danych dla miasta (np. Kutno) → parametry z 2–3 najbliższych wzorców jako przedział, nie jedna liczba.

## 7. Ograniczenia

Nie otwarto raportów SUMP dla Lublina, Białegostoku, Poznania, Łodzi, Opola, Zielonej Góry, Gorzowa, Częstochowy (Subregion Północny) i Subregionu Południowego. Poradnik GUS do ankietowego badania mobilności (pois.gov.pl, medium 72914) wskazano w wyszukiwaniu, ale nie udało się go pobrać, więc o metodzie GUS wiem tylko z raportów Rzeszowa i Torunia. Liczby z wykresów bez etykiet nie są użyte.
