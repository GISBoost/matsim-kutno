# F3 — popyt z GUS (2026-10-16)

**Status: ZALICZONA**

Skrypt: `pipeline/demand.py` (wskaźniki liczone wprost z XLSX, bez liczb wpisanych w kod). Wyjścia: `scenarios/kutno/demand/workers_by_obwod.csv`, `inbound_by_gmina.csv`, `reports/f3_demand/f3_demand.json`, `.png`.

| Test | Wynik |
|---|---|
| Suma ludności 232 obwodów = wiersz gminy | 42 255 = 42 255 |
| Złączenie tabela ↔ geometria | reguła `obwod_id = rejon_id × 10 + nr`, **232/232**; nadmiarowy w geometrii: `6509213` (0,15 km², brak wiersza w tabeli, traktowany jako niezamieszkany) |
| Przyjeżdżający | 8 186 (134 gminy) = FACT_CHECK #14 |
| Grupy wieku per obwód | przed. + prod. + poprod. = ogółem dla każdego obwodu |

## Pracujący (D5): estymacja, nie obserwacja

Wskaźniki: NSP 2021 „Ludność na rynku pracy”, TABL. 5, **Miasta ogółem, łódzkie**.

| grupa | niski (nieustalony status = niepracujący) | bazowy (metoda GUS: bez nieustalonych) |
|---|---|---|
| produkcyjny | 72,3% | 78,0% |
| poprodukcyjny | 13,6% | 13,7% |
| przedprodukcyjny* | 0,9% | 0,9% |

\* TABL. 5 podaje przedprodukcyjnych tylko w wieku 15–17 lat, a tabela BREC liczy grupę 0–17. Wskaźnik = pracujący 15–17 / ludność 0–17 w całym woj. łódzkim.

| | niski | bazowy |
|---|---|---|
| pracujący mieszkańcy Kutna | 18 836 | 20 215 |
| − wyjeżdżający (macierz, pracownicy najemni) | 2 669 | 2 669 |
| **mieszkańcy pracujący w Kutnie** | **16 167** | **17 546** |
| + przyjeżdżający | 8 186 | 8 186 |
| **agenci przy 100%** | **24 353** | **25 732** |

ZAŁOŻENIA: (1) wyjeżdżających odejmujemy proporcjonalnie we wszystkich obwodach; (2) macierz obejmuje tylko pracowników najemnych, więc odpływ jest dolną granicą; (3) wskaźniki wojewódzkie dla miast przenosimy na każdy obwód bez różnicowania płci.

## Przyjeżdżający wg obszaru (dla F4, D9)

| skąd | osoby |
|---|---|
| gminy powiatu kutnowskiego (dom w budynku OSM gminy) | 6 050 |
| reszta woj. łódzkiego (np. Łódź 201, Witonia 172) | 979 |
| spoza łódzkiego (np. Gostynin 188, Szczawin Kościelny 109, Płock) | 1 157 |

**Do rozwiązania w F4:** 2 136 przyjeżdżających spoza powiatu startuje na wjeździe na granicy sieci. Kierunek wjazdu wymaga położenia gminy źródłowej. Dla łódzkiego mamy geometrię BREC, dla 1 157 osób spoza województwa trzeba dobrać geometrię (BREC GML mazowieckie 40 MB, kujawsko-pomorskie 14 MB, w limicie D12) albo przypisać kierunek po kodzie województwa.

Mapa: `reports/f3_demand/f3_demand.png`.
