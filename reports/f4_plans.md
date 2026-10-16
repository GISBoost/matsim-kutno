# F4 — lokalizacje i plans 10% (2026-10-16)

**Status: ZALICZONA** (test automatyczny). Czeka na kontrolę człowieka w QGIS (próbka domów i miejsc pracy).

Skrypty: `pipeline/osm_features.py` (budynki + landuse z PBF), `pipeline/plans.py` (lokalizacje + `plans.xml.gz`), `pipeline/validate_plans.py` (test + mapa). Parametry i ZAŁOŻENIA: `config/kutno.toml` `[plans]`. Log: `reports/f4_plans.log`, wynik: `reports/f4_plans.json`, `.png`.

| Test | Wynik |
|---|---|
| osoby = round(0,1 × 25 732) | 2 573 = 2 573 (largest remainder po 232 obwodach i 134 gminach) |
| łańcuch `home-car-work-car-home`, `end_time` XOR `max_dur` | 2 573/2 573 |
| domy w obszarze sieci | 0 poza |
| praca w gminie Kutno | 0 poza |
| powrót do tego samego domu | 2 573/2 573 |
| sha256 przy ponownym uruchomieniu | identyczny (`525ed292…9538` po D14; gzip z `mtime=0`) |

## Jak powstały lokalizacje

- **Domy mieszkańców (D11):** 1 762 osoby. Budynek mieszkalny OSM w obwodzie, losowany z wagą powierzchni obrysu. Mieszkalny = typ z listy w configu albo `building=yes` w `landuse=residential` bez tagów amenity/shop/office.
  - 26 611 budynków mieszkalnych w obszarze sieci.
  - 1 obwód bez budynków: `6509902` (6 osób, losowy punkt w obwodzie wg D11). Nie wiem, czy to obszar bez zabudowy mieszkalnej, czy brak budynków w OSM. Do sprawdzenia w QGIS.
- **Domy przyjeżdżających z powiatu (D9):** 605 osób. Budynek mieszkalny w gminie źródłowej, geometria gminy z krajowych rejonów BREC 2021 (`SU_BREC_2021_REJ.zip`, nowe pobranie 124 MB, w manifeście). Gminy miejsko-wiejskie mają osobne kody 4/5 także w BREC.
- **Przyjeżdżający spoza powiatu (D9):** 206 osób. Start na linku wjazdowym (motorway/trunk/primary/secondary), który zaczyna się w 1 km strefie granicy sieci i jest skierowany do centrum Kutna. Wybierany jest link najbliższy centroidowi gminy źródłowej.
  - Dotyczy też gmin spoza łódzkiego. Ich geometria pochodzi z tego samego krajowego pliku BREC, więc otwarte pytanie z F3 jest zamknięte.
  - Miasta na prawach powiatu (Łódź, Warszawa, Poznań, Kraków, Wrocław) mają w BREC kody dzielnic, dlatego łączymy je po kodzie powiatu.
  - Użyto 11 z 31 linków wjazdowych. Najwięcej osób trafia na N i NW (Gostynin, Kłodawa/Koło) oraz SE (Łódź).
- **Praca (D7):** wszyscy w gminie Kutno. Budynek niemieszkalny z wagą powierzchni obrysu: typ z listy w configu, tag amenity/shop/office albo `building=yes` w landuse industrial/commercial/retail.
  - 1 103 kandydatów, wylosowano 473 budynki.
  - Top 5 budynków skupia 13% agentów (duże hale w strefie wschodniej).
- **Godziny (D14, aktualizacja po F4):** wyjazd z rozkładu GBR Gdańsk 2022 Rys. 46 „dom - praca”, jednostajnie w godzinie (`config/departure_home_work_gbr2022.csv`); praca 8 h (`max_dur`, ZAŁOŻENIE). Pierwotnie 07:00 dla wszystkich.

## Liczby kontrolne

- Mediana odległości dom → praca w linii prostej: mieszkańcy 3,8 km, przyjeżdżający 13,0 km.
- Strefa wschodnia Kutna (hale) przyciąga dużą część pracy. Przy wadze „powierzchnia obrysu” magazyn ma więcej pracowników na m² niż w rzeczywistości. To znane ograniczenie D7 (REGON jako przyszła podmiana).

## Ograniczenia (świadome)

- Wagi powierzchnią: magazyny i hale są przeszacowane jako miejsca pracy, a bloki niedoszacowane względem domów jednorodzinnych (piętra nieuwzględnione).
- Przyjeżdżający spoza powiatu nie mają odcinka poza siecią. Ich czas podróży jest zaniżony o dojazd do granicy.
