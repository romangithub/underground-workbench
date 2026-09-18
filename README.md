# UNDERGROUND Workbench

**Local hydrogeology workbench on top of USGS MODFLOW 6**

Import a site package → build a grid → run **native** `mf6` → calibrate heads → Plan / Section / 3D → engineering report.

> This is **not** a new solver. The engine is official [USGS MODFLOW 6](https://github.com/MODFLOW-ORG/modflow6) (free / public). Workbench is the workflow shell around it.

**Project page:** [GitHub Pages](https://romangithub.github.io/underground-workbench/) · **Contact:** [kovalevrm@gmail.com](mailto:kovalevrm@gmail.com)

---

## Why it exists

Hydrogeologists often repeat the same loop:

1. Take GIS / field inputs for a site  
2. Run MODFLOW 6  
3. Compare computed heads to observations  
4. Show map / section / 3D  
5. Hand over a short engineering report  

| Approach | What you get |
| --- | --- |
| **Free** — mf6 + ModelMuse / FloPy | Full maths, you glue the workflow yourself |
| **Paid** — Visual MODFLOW Flex, GMS, FEFLOW… | Mature all-in-one GUI, high seat cost |
| **Workbench** | One **local** UI loop on **native mf6**, without an enterprise license |

---

## Features

| Step | What happens |
| --- | --- |
| **Import** | Site package: boundary & wells (GeoJSON / shapefile), observations CSV, surface grid, optional rivers, `project_meta.json` |
| **Build** | Structured DIS grid from extents / spacing; layer bottoms + per-cell top surface |
| **Run** | Calls **native USGS mf6** (no prebaked fake heads) |
| **Calibrate** | Observed vs computed heads · MAE / improvement · residuals |
| **View** | Plan · Section · WebGL 3D (surfaces + well screens) |
| **Report** | Engineering report with maps, residuals, input provenance |
| **Verify** | `npm run verify:stage` acceptance gates |

---

## What it is not

- Not a FloPy / PEST / PyEMU replacement  
- Not FEFLOW-class transport or FE meshes  
- Not an enterprise geodatabase product  
- Bundled demo sites (`client_site_alpha` / `beta`) are **synthetic** — not a live client project  

Real value shows up when you run **your** data through Import → Report.

---

## Quick start (Mac, Apple Silicon)

```bash
chmod +x start.sh apps/underground_workbench/start.sh
./start.sh
```

Open **http://127.0.0.1:18888**

First launch downloads official USGS **mf6 6.7.0** for macOS ARM64 (~120 MB). Needs Python 3.9+ and a one-time network connection.

Demo package:

```text
apps/underground_workbench/fixtures/site_packages/client_site_alpha.zip
```

---

## Site package format

| File | Role |
| --- | --- |
| `project_meta.json` | CRS, spacing, layers, K, CHD, initial head |
| `boundary.*` | Model polygon (GeoJSON and/or shapefile) |
| `wells.*` | Wells / screens / pumping rates |
| `observations.csv` | Observed heads |
| `surface_top.csv` | Top elevation grid (`row,col,x,y,z`) |
| `rivers.geojson` | Optional river lines |

Demo fixtures contain **no personal data** and **no real client site** — see [`docs/SITE_PACKAGES_FILE_AUDIT.md`](docs/SITE_PACKAGES_FILE_AUDIT.md).

---

## Free vs paid vs Workbench

| | Free | Paid | Workbench |
| --- | --- | --- | --- |
| Solver | USGS mf6 | Often mf6 / own FE | **Native USGS mf6 only** |
| Workflow | You assemble | Full commercial GUI | Import → run → calibrate → 3D → report |
| Cost | $0 | High / seat / year | Local app |
| Strength | Scriptability | Maturity & support | One local loop + verify |
| Weakness | Manual glue | Vendor lock | Custom package format; prove on your live jobs |

---

## Status

MARKET / FIELD finished builds with operator `verify:stage` PASS on disk.  
Treat as a **working local prototype** — not a claim that it already beats FloPy or Flex on every real project.

---

## Credits & license

- Groundwater engine: [USGS MODFLOW 6](https://github.com/MODFLOW-ORG/modflow6) — free public software; respect USGS terms for redistributed binaries  
- Workbench UI / pipeline: © Roman K — add your chosen OSS license before wide redistribution  

---

## Author

**Roman K** — hydrogeology consulting · Lisbon  
Email: [kovalevrm@gmail.com](mailto:kovalevrm@gmail.com)
