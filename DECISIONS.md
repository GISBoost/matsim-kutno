# DECISIONS — decyzje projektowe

Format: data · decyzja · uzasadnienie · konsekwencje. Zmiana decyzji = nowy wpis, a stary dostaje dopisek „zastąpione przez #N”.

## Podjęte

| # | Data | Decyzja | Uzasadnienie | Konsekwencje |
|---|---|---|---|---|
| D1 | 2026-10-16 | **Miasto: Kutno** (gm. miejska, TERC 1002011). Linia Łowicz tylko w archiwum. | Najnowsza decyzja; dane GUS dla Kutna sprawdzone (FACT_CHECK #7–9). | Z Łowicza bierzemy wyłącznie zweryfikowane pomysły, nie jego zakres ani stary `CLAUDE.md`. |
| D2 | 2026-10-16 | **Cel: najpierw test techniczny, potem prototyp przestrzenny.** | Diagnostyka etapami; brak danych do kalibracji. | Żadnych wniosków o kongestii ani porównań z pomiarami w MVP. Wynik = poprawność pipeline’u + sensowna geografia. |
| D3 | 2026-10-16 | **Popyt MVP: mieszkańcy Kutna pracujący w Kutnie + przyjeżdżający do pracy w Kutnie** (macierz GUS NSP 2021). Wyjeżdżający poza zakresem. | Do Kutna przyjeżdża 8 186 osób, wyjeżdża 2 669 (FACT_CHECK #14); bez przyjeżdżających brakuje głównego strumienia porannego. | Sieć musi mieć bufor obejmujący drogi wjazdowe. Trzeba zdecydować, jak reprezentować źródło dojazdu (D-otwarte). |
| D4 | 2026-10-16 | **Nowy `CLAUDE.md` od zera**, bez treści z wersji Łowicz. | Stary dotyczył innego zakresu. | — |
| D5 | 2026-10-16 | **Pracujący mieszkańcy = wskaźniki zatrudnienia NSP 2021 (łódzkie, ekonomiczne grupy wieku) × struktura wieku każdego obwodu.** Warianty niski/bazowy/wysoki. | Brak danych o zatrudnieniu na poziomie gminy/obwodu (FACT_CHECK #10–11). | Wynik ok. 19 tys. to **estymacja**, nie obserwacja. Wskaźniki w configu, nie w kodzie. |
| D6 | 2026-10-16 | **Wszyscy pracujący z zakresu D3 jadą samochodem** (brak współczynnika car share). | Świadome uproszczenie MVP. | **Ruch jest zawyżony** o pieszych, rowerzystów i PT. Wyników nie interpretujemy jako natężeń. Mechanizm car share do dodania później. |
| D7 | 2026-10-16 | **Miejsca pracy: OSM landuse (industrial/commercial/retail) + budynki niemieszkalne, ważone powierzchnią.** | Bez kluczy API, ten sam PBF co sieć. | Przybliżenie rozkładu zatrudnienia. REGON jako przyszła podmiana. |
| D8 | 2026-10-16 | **Skala: 10 agentów (sieć syntetyczna) → 10% Kutna → 100%.** | Ok. 24 tys. agentów to mały scenariusz; przy 100% nie ma skalowania przepustowości. | `flow/storageCapacityFactor` = frakcja próbki (0,1, potem 1,0). Wnioski tylko z 100%. |
| D9 | 2026-10-16 | **Przyjeżdżający: sieć obejmuje powiat kutnowski (+ bufor); dom = losowy budynek mieszkalny OSM w gminie źródłowej. Gminy spoza powiatu startują na najbliższym wjeździe na granicy sieci.** | Większość dojazdów pochodzi z gmin powiatu (FACT_CHECK #14). | Zasięg sieci = powiat kutnowski. Gminę miejsko-wiejską trzeba złożyć z kodów 4/5 (np. Krośniewice, Żychlin). |
| D10 | 2026-10-16 | **Godziny: smoke test stałe (07:00, 8 h); prototyp = rozkład ze źródła do znalezienia, do tego czasu jawne ZAŁOŻENIE w configu.** | Brak danych lokalnych. | Zadanie researchowe w TASKS. |
| D11 | 2026-10-16 | **Domy mieszkańców: liczba pracujących per obwód BREC (232) → losowy budynek mieszkalny OSM w obwodzie, ważony powierzchnią.** Obwód bez budynków → losowy punkt + wpis do raportu. | Najdrobniejsza dostępna geografia + realna zabudowa. | Wymaga złączenia obwodów tabela ↔ geometria (232 vs 233, FACT_CHECK #13). |
| D12 | 2026-10-16 | **Uprawnienia agenta bez pytania:** lokalny venv `uv` w projekcie, pobieranie danych < 500 MB, lokalny commit po zaliczonej fazie (bez push), build `mvnw` i runy MATSim (`-Xmx10g`). | Zgoda użytkownika. | Wszystko inne (push, instalacje globalne, > 500 MB, usuwanie danych) wymaga pytania. |
| D13 | 2026-10-16 | **Prędkości sieci: tag OSM `maxspeed` > limity ustawowe (PoRD art. 20: miasto 50, poza 90, residential 50, living_street 20, motorway 140, trunk 100) × factor 0,8.** Miasta = gm. miejska / miasto gm. miejsko-wiejskiej z BREC. | Domyślne Supersonic (VSP, Niemcy) dawały 15–25 km/h na ok. 3 000 km dróg wiejskich (F2). | Parametry w `config/network.properties`. Factor 0,8 i „wsie jak drogi zamiejskie” to ZAŁOŻENIA. Capacity zostaje domyślne Supersonic. |
| D14 | 2026-10-16 | **Godziny wyjazdu do pracy: GBR Gdańsk 2022, Raport 3a, Rys. 46, seria „dom - praca” (godzinowa), jednostajnie w godzinie. Czas pracy 8 h (`max_dur`). F5 bez TimeAllocationMutator.** | Decyzja użytkownika po R1: jedyne sprawdzone źródło pierwotne z rozkładem godzinowym. | Rozwiązuje D10. Profil w `config/departure_home_work_gbr2022.csv` (z wektorów PDF). Przeniesienie z metropolii na Kutno i 8 h to ZAŁOŻENIA. |

## Otwarte

- Rozkład czasu pracy (teraz stałe 8 h, D14).
- Szerokość bufora sieci poza powiatem (dobór w Fazie 2 na podstawie dróg wjazdowych).
- Parametry scoringu (domyślne MATSim do czasu decyzji; kalibracja poza MVP).
- Car share (D6), REGON (D7), wyjeżdżający (D3): poza MVP.
