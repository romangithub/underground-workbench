# MODFLOW ecosystem: Free vs Paid vs UNDERGROUND Workbench

Каркас сравнения. Когда придут файлы с описаниями MODFLOW — класть в `incoming/`, этот документ допишем по ним.

## Три класса

| Класс | Что это | Примеры |
| --- | --- | --- |
| **Free** | Официальный солвер + бесплатные GUI/скрипты | USGS **MODFLOW 6** + **ModelMuse**, **FloPy**, ZONEBUDGET/MODPATH |
| **Paid** | Коммерческие интегрированные среды | **Visual MODFLOW Flex**, **GMS** (Aquaveo), **FEFLOW** (DHI), иногда Processing Modflow / Groundwater Vistas |
| **Ours** | **UNDERGROUND Workbench** (MARKET finished) | Локальный продукт: site-пакет → native mf6 → калибровка → Plan/Section/3D → Engineering Report |

---

## Сравнение по осям

### 1. Солвер
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| Ядро | USGS mf6 (эталон) | Часто mf6 / mf2005 внутри **или** свой FE (FEFLOW) | **Только native USGS mf6** (subprocess), без fallback heads |
| Прозрачность | Полная (публичные release) | Зависит от вендора | Полная: HDS/CBC SHA, stdout MODFLOW 6 |

### 2. Вход данных / GIS
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| Импорт | ModelMuse: свой UI; FloPy: shapefile/raster через Python | Сильный GIS/conceptual model builder | **Боевой site-пакет**: GeoJSON/shp + CSV obs/wells + DEM/surface → сетка из extents; negatives на CRS/слои |
| CRS / provenance | Вручную / скриптами | Обычно сильно | Provenance SHA каждого входного файла в отчёте |

### 3. Построение модели
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| Сетка | DIS / частично DISV (ModelMuse); FloPy — и DISU | Гибко, incl. FE mesh (FEFLOW) | Structured DIS из импорта; **TOP + BOTM cell-by-cell** |
| UX | Научный GUI или код | «Всё в одном» для инженера | Web UI: Import → Plan/Section/3D → Run calibrate → Report |

### 4. Калибровка
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| Уровень | PEST/PyEMU снаружи; ModelMuse ограниченно | Часто встроенные PEST-like / parameter estimation | Встроенный baseline vs variants: **MAE / RMSE / improvement**, residuals; anti obs-paint |
| Автоматизация | Скрипты | Мастера | Один workflow + verify |

### 5. 3D / визуализация
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| | ModelMuse 2D/3D базово; FloPy → VTK/внешние | Сильный 3D | WebGL: **TRIANGLES по поверхности**, wells **LINES**, sync Plan/Section |

### 6. Отчёт / сдача
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| | Сам собираешь | Шаблоны/экспорт | **Engineering Report**: карты из данных, residuals, provenance, evidence hashes |

### 7. Цена / доступ
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| Лицензия | $0 (USGS / open tools) | Тысячи–десятки тысяч $ / seat / год | Свой продукт (локальный app; не SaaS-обёртка) |
| Кому | Исследователи, кто пишет код | Консалтинг, регуляторика «из коробки» | Гидрогеолог: быстрый путь site→mf6→отчёт без тяжёлого enterprise |

### 8. Ограничения (честно)
| | Free | Paid | Ours |
| --- | --- | --- | --- |
| | Крутая кривая FloPy; ModelMuse не закрывает весь mf6 (нет полного DISU и т.д.) | Дорого; vendor lock; иногда «чёрный ящик» | Пока **не** enterprise GIS/геобаза; **не** PEST-grade; демо-площадки ≠ живой клиент; structured grid focus |

---

## Где наш продукт выигрывает (коротко)

1. **Native mf6 only** + verify EXIT=0 as-shipped — не картинка вместо расчёта.  
2. **Site-package workflow** (shp/GeoJSON/CSV/DEM) → модель → калибровка → отчёт в одном контуре.  
3. **Инженерный отчёт с provenance** из коробки.  
4. Локальный запуск без обязательной покупки Flex/GMS/FEFLOW.

## Где free/paid всё ещё сильнее

- **Free/FloPy**: полная автоматизация, DISU, воспроизводимые пайплайны в Python.  
- **Paid**: зрелый conceptual modeling, транспорт/тепло (FEFLOW), тяжёлая калибровка, поддержка вендора, привычка заказчика «сделай в GMS/VM».

---

## Что сделать, когда придут файлы

1. Положить в `/workspace/modflow_compare/incoming/` (и/или `~/Documents/modflow_compare/incoming/`).  
2. Для каждого файла: выписать заявленные фичи / цены / ограничения.  
3. Обновить таблицу выше по фактам из документов (не по маркетингу).  
4. Отметить расхождения с **нашим** MARKET-каноном.

## Наш эталон (диск оператора)

- Zip: `underground_workbench_market_finished.zip` (SHA `657c6a6f…`)  
- Дерево: `/workspace/underground_workbench_market`  
- Mac app: `~/Documents/UndergroundWorkbench`  
- Канон: MAE≤5, improvement≥0.5, no FALLBACK, numpy-free, TOP+BOTM INTERNAL, shapefile+GeoJSON, report maps, verify×2.
