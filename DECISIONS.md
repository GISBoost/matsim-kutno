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

## Otwarte

- Reprezentacja przyjeżdżających (punkt wjazdu na granicy bufora / centroid gminy źródłowej / losowy punkt w gminie źródłowej).
- Rozkład godzin wyjazdu i czasu pracy (źródło).
- Lokalizacja domów (obwód/rejon BREC + budynki OSM/BDOT10k).
