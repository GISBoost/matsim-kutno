# Krok 3 etapu 3: atrybuty osób (research)

Data: 2026-10-25. Zakres wg ROADMAP: wiek z NSP 2021, prawo jazdy i dostęp do auta z ogólnych statystyk GUS (łódzkie). Nic nie wdrożone, to tylko research i pytania.

## 1. Stan modelu (z kodu i planów)

- Agent to dziś **tylko pracujący dojeżdżający autem**: `pracujący obwodu × car_share 0,64 × (1 − praca z domu 0,073)`, próbka 25% (`config/kutno.toml`, `pipeline/plans.py`). Atrybuty osoby w `plans.xml`: `subpopulation=person`, `kind` (resident/commuter/outbound), `vehicles`. Brak wieku, `carAvail`, prawa jazdy.
- Każdy agent jedzie autem z założenia (wybór trybu jest w `car_share`, poza symulacją). Dlatego `carAvail=always` dla wszystkich obecnych agentów byłby tautologią i **nie zmieni ruchu**. Atrybuty zaczynają działać dopiero, gdy w modelu są osoby niejeżdżące autem lub niepracujące (krok 4 i 6).

## 2. Co mamy w `data/raw/` (sprawdzone w plikach)

| dane | zawartość | ograniczenie |
|---|---|---|
| `gus/ludnosc_rejony_obwody_nsp2021.xlsx` | per obwód spisowy: ogółem, płeć, grupy ekonomiczne (0–17 / 15–59·64 / 60·65+, z podziałem produkcyjny mobilny i niemobilny), **10-letnie grupy wieku** (0–9 … 80+). Gm. m. Kutno: 42 255 os., 0–9: 3 510, 10–19: 3 572, 20–29: 3 821, 30–39: 5 987, 40–49: 6 234, 50–59: 5 510, 60–69: 7 136, 70–79: 4 485, 80+: 2 000 | płeć i wiek **nie są skrzyżowane** (brak mężczyzn 30–39 itp.); grupy 10-letnie, nie 5-letnie |
| `gus/rynek_pracy_nsp2021_tablice.xlsx` | aktywność ekonomiczna wg grup wieku i płci, wykształcenia; TABL. 5 (miasta łódzkie) już użyta w `demand.py` do wskaźników zatrudnienia | poziom miasta/województwa, nie obwodu |
| `gus_transport/mobilnosc_..._2024_tablice.xlsx` | Tabl. 5: członkowie gospodarstw (6+) z prawem jazdy A lub B wg województwa: **łódzkie 1 314 406 z 2 168 761 (60,6%)**, Polska 21,32 mln; Tabl. 2: samochody osobowe do dyspozycji gospodarstw, łódzkie 958 925 (0,44 na osobę 6+); Tabl. 6: podróżujący z prawem jazdy | tylko województwo (i klasy lokalizacji w tabelach 13+), **bez wieku i bez gminy**; prawo jazdy A lub B razem (nie samo B); badanie próbkowe, błąd względny bywa >20% |

NSP 2021 nie pytał o samochód ani prawo jazdy (nie znalazłem takiej zmiennej w publikowanych tablicach; to wniosek z braku, nie dowód). Gminnych danych o posiadaniu auta z GUS nie ma.

## 3. Czego brakuje i skąd można to wziąć

| potrzeba | źródło | stan |
|---|---|---|
| prawo jazdy wg **wieku** | CEPiK (gov.pl) „Prawa jazdy i uprawnienia w 2019 roku”: prawa jazdy wg stanu 31.12.2019 z podziałem na płeć i wiek, 3 pliki xlsx po ok. 0,01 MB ([strona](https://www.gov.pl/web/cepik/prawa-jazdy-i-uprawnienia-w-2019-roku)) | nie pobrane, nie otwarte (struktura plików niezweryfikowana); dane krajowe z 2019 r.; nie wiem, czy są nowsze roczniki |
| populacja wg wieku (mianownik gradientu) | GUS BDL / NSP 2021, Polska i łódzkie | nie pobrane |
| liczba aut w gminie | CEPiK/BDL: samochody osobowe na 1000 mieszk. wg powiatu (kutnowski: 631 w 2017, 686 w 2019 wg [portretu powiatu GUS Łódź](https://lodz.stat.gov.pl/vademecum/vademecum_lodzkie/portrety_powiatow/powiat_KUTNOWSKI.pdf)) | rejestr zawyżony (czyszczenie rejestru w 2024 usunęło ok. 4,8 mln aut krajowo, [Demagog](https://demagog.org.pl/analizy_i_raporty/samochody-w-polsce-mit-obsesji-czy-zmiana-w-statystykach/)); wartość 2023–2024 dla powiatu niezweryfikowana |
| powiązanie auto–osoba | nie istnieje w danych publicznych | model musi to założyć |

Szukanie w sieci nie dało innych zestawów (odsetek posiadaczy prawa jazdy wg wieku z GUS lub ITS nie wyszedł w wyszukiwaniu; nie znaczy, że nie istnieje).

## 4. Opcje modelu (do decyzji)

1. **Minimum:** wiek (losowany z rozkładu 10-letnich grup obwodu, warunkowo na statusie pracującego) i `carAvail` jako atrybuty obecnych agentów. Ruch bez zmian; to tylko przygotowanie pod krok 4 i 6.
2. **Pełna populacja syntetyczna:** wszyscy 42 255 mieszkańców Kutna z wiekiem, statusem (pracujący / uczeń / emeryt / inny), prawem jazdy i dostępem do auta; symulowani są dalej tylko pracujący autem, reszta czeka na krok 4 i 6. Wymaga założeń o powiązaniu wiek–status–licencja–auto (brak danych skrzyżowanych).
3. **Atrybuty dopiero przy kroku 4:** wiek tylko tam, gdzie jest potrzebny (uczniowie, emeryci), bez osobnego kroku 3.

Uwaga metodologiczna: skrzyżowania (wiek × licencja × auto × status) trzeba by zbudować z marginesów (np. IPF/losowanie warunkowe), czyli estymacji, a nie obserwacji (zasada „nie udawaj obserwacji”, jak D5).

## 5. Wynik po decyzjach użytkownika (2026-10-25) i pobraniu CEPiK

Decyzje: zakres = **pełna populacja** (wszyscy mieszkańcy Kutna; symulowani dalej tylko pracujący autem), `carAvail` = licencja + auto w gospodarstwie (jawne ZAŁOŻENIE z wariantami), pobranie CEPiK 2019 zatwierdzone.

Pobrane do `data/raw/g_atrybuty/` (3 pliki, 9,8 / 14,8 / 14,3 KB, wpisy w `data/manifest.csv`): `Prawa_jazdy_wg_stanu_na_31122019.xlsx`, `Uprawnienia_wg_stanu_na_31122019.xlsx`, `Uprawnienia_wydane_w_2019.xlsx`. Otwarty tylko pierwszy: **krajowa liczba praw jazdy (wszystkie kategorie) wg płci i grup wieku 18–24, 25–34, 35–44, 45–54, 55–64, 65+** (np. kobiety 18–24: 857 489, mężczyźni 65+: 2 951 870; suma ok. 21,6 mln). Pozostałe dwa pliki nie sprawdzone.

Ograniczenia: liczba dokumentów, nie osób z kategorią B; stan 2019 (nie 2021); grupy wieku nie pokrywają się z 10-letnimi grupami NSP (20–29, 30–39…), więc trzeba je przeliczyć albo wziąć 5-letnie dane NSP; kobiety i mężczyźni w NSP nie są skrzyżowani z wiekiem. Aby z liczby praw jazdy zrobić **udział** w wieku, potrzebna jest populacja Polski 2019 wg płci i tych samych grup wieku (GUS BDL; API BDL działa, nie ma jeszcze wybranej zmiennej). Dalej skala gradientu wiek → licencja trzeba skalibrować do 60,6% łódzkiego (GUS Mobilność 2024), bo CEPiK jest krajowy.

## 6. Plan wdrożenia (po akceptacji)

1. Pobrać z BDL populację Polski 2019 wg płci i grup wieku (mała tabela), policzyć udział praw jazdy wg wieku, przeskalować do 60,6% (łódzkie, A lub B, 6+).
2. `pipeline/population.py`: pełna populacja Kutna per obwód (wiek z 10-letnich grup, status pracujący/niepracujący z istniejącego `demand.py`, licencja z gradientu, auto w gosp. z 0,44 auta na osobę 6+; warianty jawne).
3. Obecni agenci (pracujący autem) dostają atrybuty `age`, `licence`, `carAvail`; plany i ruch bez zmian (test: sha256 planów poza atrybutami, GPR, opóźnienia na GHA nie powinny się zmienić ponad szum).
4. Decyzja D30 w DECISIONS, raport `reports/etap3/g_atrybuty/`.
