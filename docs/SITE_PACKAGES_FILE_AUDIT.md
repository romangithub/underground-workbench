# Аудит site-пакетов UNDERGROUND Workbench

Дата: 2026-09-18  
Путь: `~/Documents/UndergroundWorkbench/apps/underground_workbench/fixtures/site_packages/`

## Краткий вывод

| Вопрос | Ответ |
| --- | --- |
| Есть ли персональные данные (ФИО, email, телефон, адрес, паспорт)? | **Нет** |
| Есть ли данные о реальном клиентском объекте? | **Нет** — только синтетика |
| Что это? | Учебные / тестовые пакеты для Import → mf6 → Report |

---

## Состав каталога

| Пакет | Назначение |
| --- | --- |
| `client_site_alpha` (+ `.zip`) | Демо-сайт A (GeoJSON + shapefile) |
| `client_site_alpha_shp` (+ `.zip`) | Тот же A, в основном shapefile (без wells/boundary GeoJSON) |
| `client_site_beta` (+ `.zip`) | Демо-сайт B, другой CRS/origin |
| `bad_market_crs` (+ `.zip`) | Негатив: битый CRS / spacing |
| `bad_market_no_layers` (+ `.zip`) | Негатив: нет `layers` в meta |

---

## Разбор файлов (по типам)

Одинаковый набор типов у alpha / beta (и почти у bad_*).

### `project_meta.json`
Метаданные модели: `site_id`, `site_name`, CRS, units, spacing, слои (`layers` + bottoms), `k_by_layer`, CHD west/east, `initial_head`, `origin_tag`.  
Имена: «Client Site Alpha / Beta» — выдуманные. Персоналки нет.

### `boundary.geojson` (+ `boundary.shp` / `.shx` / `.dbf`)
Полигон границы модели. Alpha: прямоугольник ~500000–501400 / 4640000–4641000 (EPSG:32637). Beta: ~392000–393800 / 5120000–5121500 (EPSG:32633). Не адрес объекта.

### `wells.csv` + `wells.geojson` (+ `wells.shp` / `.shx` / `.dbf`)
Скважины: id, x, y, layer, screen_top/bottom, Q.  
Примеры id: `MW-01`, `PW-02`, `IW-03` — не ФИО.

### `observations.csv`
Точки наблюдения: id (`OBS-A`…), x, y, layer, `observed_head`, `survey_source` = `independent_level_survey_2026Q3` (фейковая метка источника).

### `rivers.geojson`
Одна линия `RIV-01` + cond / rbot_offset.

### `surface_top.csv`
Сетка поверхности: `row,col,x,y,z` (у alpha ~141 строк включая заголовок). DEM-заглушка, не реальное поле.

---

## Пакет за пакетом

### client_site_alpha
- CRS: **EPSG:32637**, spacing 100 m, 6 слоёв L1–L6  
- 3 скважины, 7 наблюдений, 1 река  
- `origin_tag`: `alpha_real_extents` (тег демо, не «реальный клиент»)

### client_site_alpha_shp
- Те же цифры, что alpha  
- Без `boundary.geojson` / `wells.geojson` — упор на shapefile

### client_site_beta
- CRS: **EPSG:32633**, spacing 150 m, 5 слоёв  
- Другой origin; тот же паттерн 3 wells / 7 obs  
- `origin_tag`: `beta_shifted_origin`

### bad_market_crs
- CRS **EPSG:4326**, spacing `0.01`, coords ~30/60 — намеренно некорректный пакет для отказа импорта  
- `origin_tag`: `bad_crs`

### bad_market_no_layers
- Похож на beta, но в `project_meta.json` **нет** массива `layers` — негатив на валидацию

---

## Скан на персональные данные

Просмотрены текстовые файлы пакетов (json/csv/geojson).  
Совпадений по email, телефонам, ФИО, адресам, паспортным/ИНН-полям, именам вроде Roman/Kovalev — **не найдено**.

---

## Итог для продукта

В fixtures лежит только синтетика для прогона Workbench.  
Боевой site-пакет = данные, которые пользователь соберёт сам и положит в тот же формат файлов.
