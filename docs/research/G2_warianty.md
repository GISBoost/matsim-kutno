# G2: warianty liczby miejsc pracy i wyjeżdżających

Data: 2026-10-17. Do decyzji użytkownika (przyszły wpis D17). Liczby są w skali 100%.

## Bilans źródeł (gm. miejska Kutno, 1002011)

| wielkość | wartość | źródło |
|---|---|---|
| pracujący mieszkańcy, estymacja D5 (bazowy / niski) | 20 215 / 18 836 | `reports/f3_demand/f3_demand.md`, wskaźniki NSP 2021 łódzkie × struktura wieku obwodów |
| pracujący mieszkańcy, rejestry ZUS/KRUS (P4507 „ogółem”, 2024) | 17 255 | BDL API, zmienna 1735394 (sprawdzone 2026-10-17) |
| miejsca pracy wg siedziby płatnika (P4508, 2024) | 17 486 | BDL API, zmienna 1735396 (sprawdzone) |
| wyjeżdżający z Kutna (najemni, przepływy ≥ 3) | 2 669 w 83 relacjach | macierz NSP 2021, arkusz „Macierz przepływów” |
| przyjeżdżający do Kutna (po odcięciu D16 > 100 km) | 8 139 | macierz NSP 2021 i D16 |
| model dziś: mieszkańcy pracujący w Kutnie + przyjeżdżający | 17 546 + 8 139 = 25 685 | plany 100% |

Wyjeżdżający według czasu dojazdu autem do gminy pracy (macierz dostępności GUS):
- 0–30 min: 976, w tym 814 do gmin powiatu (gm. wiejska Kutno 256, Krzyżanów 111, Strzelce 99);
- 30–60 min: 916, w tym Łódź 374 i Płock 93;
- 60–100 min: 129;
- ponad 100 min: 648, w tym Warszawa 457 (103 min).

**Źródeł nie da się domknąć.** Tożsamość to: miejsca pracy w Kutnie = mieszkańcy zostający + przyjeżdżający.
- Rejestry (P4507) minus wyjeżdżający z NSP plus przyjeżdżający z NSP dają 17 255 − 2 669 + 8 139 = **22 725**, czyli o 30% więcej niż P4508 (17 486).
- Luka 5 239 nie ma wyjaśnienia w danych. Możliwe przyczyny: inne lata (NSP 2021 vs rejestry 2024), inne definicje (spis vs rejestr ZUS/KRUS, praca główna), przepływy < 3 osób i konwencja siedziby płatnika.
- Estymacja D5 (20 215) jest o 17% wyższa od rejestru P4507 (17 255).

## Warianty liczby miejsc pracy

| wariant | mieszkańcy pracujący w Kutnie | przyjeżdżający | razem | vs dziś | ocena |
|---|---|---|---|---|---|
| **A**: bez zmian (D5 − wyjeżdżający) | 17 546 | 8 139 | 25 685 | 0 | Górna granica. Estymacja D5 jest wyższa od rejestru. |
| **B**: rejestr P4507 zamiast D5 | 17 255 − 2 669 = **14 586** | 8 139 | **22 725** | −11,5% | Zastępuje estymację danymi rejestrowymi tej samej wielkości i nie zmienia przepływów NSP. Rozkład na obwody: D5 przeskalowane proporcjonalnie (P4507 jest tylko dla gminy). |
| **C**: B przeskalowane do P4508 | 11 223 | 6 263 | **17 486** | −32% | Suma zgodna z miejscami pracy z BDL. Zakłada, że luka 30% rozkłada się równo na obie grupy, czego dane nie pokazują. |
| D: P4508, przyjeżdżający bez zmian | 9 347 | 8 139 | 17 486 | −32% | **Odradzam.** Wymaga 7 908 wyjeżdżających, a NSP pokazuje 2 669. Wariant jest wewnętrznie sprzeczny. |

Rekomendacja: **B jako baza, C jako wariant wrażliwości** (jeden dodatkowy zestaw 3 seedów, ok. 14 min). Różnica B vs C pokaże, ile wniosków zależy od nierozwiązanej luki.

Liczba miejsc pracy to nie to samo co liczba podróży danego dnia. Obecność w pracy (urlop, choroba, praca z domu: łódzkie 7,3% z domu i 5,5% w trybie mieszanym wg GUS Mobilność 2024) i udział auta to osobne czynniki (D6, G4). Nie mieszam ich z G2.

## Warianty dla wyjeżdżających

| wariant | co robi | ruch w sieci |
|---|---|---|
| **O0**: bez zmian | Wyjeżdżający są tylko odjęci od popytu, a ich ruchu nie ma w modelu. | 0 |
| **O1**: lustro D9/D16 | Dom w budynku obwodu w Kutnie (D11). Praca: dla 814 osób w gminach powiatu budynek w gminie docelowej (jak dom przyjeżdżającego z powiatu); dla pozostałych link wyjazdowy najbliższy centroidowi gminy docelowej, z odcięciem D16 > 100 km. Godzina wyjazdu z profilu GBR (D14), praca 8 h. | ok. 2 670 aut rano z miasta (wjazdy na A1, DK92 w stronę Łodzi i Płocka), w próbce 25% ok. 667 agentów |

Rekomendacja: **O1**. Ten ruch istnieje i obciąża te same wloty co przyjeżdżający, tyle że w przeciwnym kierunku. Dla G5 (porównanie z GPR) jego brak zaniżałby natężenia wylotowe. Kod wjazdów i odcięcia z D16 można użyć ponownie.

## Do decyzji

1. Wariant liczby miejsc pracy: A / **B** / C (oraz czy C liczymy jako wariant wrażliwości).
2. Wyjeżdżający: O0 / **O1**.
3. Rok kotwicy: 2024 (rekomendacja, zgodny z P4508) czy 2025 (17 251 / P4507 16 853).
4. Czy do odcięcia > 100 km (D16) dla wyjeżdżających stosować ten sam próg. Warszawa leży ok. 89 km od wjazdu, więc 457 osób zostaje.
