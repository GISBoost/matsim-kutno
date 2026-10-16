# DECISIONS — decyzje projektowe

Format: data · decyzja · uzasadnienie · konsekwencje. Zmiana decyzji = nowy wpis, a stary dostaje dopisek „zastąpione przez #N”.

## Podjęte

| # | Data | Decyzja | Uzasadnienie | Konsekwencje |
|---|---|---|---|---|
| D1 | 2026-10-16 | **Miasto: Kutno** (gm. miejska, TERC 1002011). Linia Łowicz tylko w archiwum. | Najnowsza decyzja; dane GUS dla Kutna sprawdzone (FACT_CHECK #7–9). | Z Łowicza bierzemy wyłącznie zweryfikowane pomysły, nie jego zakres ani stary `CLAUDE.md`. |
| D2 | 2026-10-16 | **Cel: najpierw test techniczny, potem prototyp przestrzenny.** | Diagnostyka etapami; brak danych do kalibracji. | Żadnych wniosków o kongestii ani porównań z pomiarami w MVP. Wynik = poprawność pipeline’u + sensowna geografia. |
| D3 | 2026-10-16 | **Popyt MVP: mieszkańcy Kutna pracujący w Kutnie + przyjeżdżający do pracy w Kutnie** (macierz GUS NSP 2021). Wyjeżdżający poza zakresem. | Do Kutna przyjeżdża 8 186 osób, wyjeżdża 2 669 (FACT_CHECK #14); bez przyjeżdżających brakuje głównego strumienia porannego. | Sieć musi mieć bufor obejmujący drogi wjazdowe. Trzeba zdecydować, jak reprezentować źródło dojazdu (D-otwarte). |
| D4 | 2026-10-16 | **Nowy `CLAUDE.md` od zera**, bez treści z wersji Łowicz. | Stary dotyczył innego zakresu. | — |

## Otwarte

- Liczba pracujących mieszkańców Kutna i jej źródło.
- Reprezentacja przyjeżdżających (punkt wjazdu na granicy bufora / centroid gminy źródłowej / losowy punkt w gminie źródłowej).
- Źródło miejsc pracy (POI OSM / REGON / landuse OSM / BDOT10k).
- Wielkość próbki i skalowanie przepustowości.
- Rozkład godzin wyjazdu i czasu pracy (źródło).
- Lokalizacja domów (obwód/rejon BREC + budynki OSM/BDOT10k).
