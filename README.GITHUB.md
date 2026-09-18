# UNDERGROUND Workbench

Local hydrogeology workbench around **USGS MODFLOW 6**: import a site package → build a grid → run native `mf6` → calibrate against observations → view Plan / Section / 3D → export an engineering report.

It is **not** a new groundwater solver. The engine is official USGS MODFLOW 6. This project is the workflow shell around it.

---

## What it is for

For hydrogeologists and engineers who repeatedly do the same loop:

1. take field / GIS inputs for a site  
2. run a MODFLOW 6 flow model  
3. compare heads to observations  
4. look at map / section / 3D  
5. hand over a short engineering-style report  

**Free stack** (mf6 + ModelMuse / FloPy) already does the maths — but you stitch import, run, plots, and report yourself.  
**Paid tools** (Visual MODFLOW Flex, GMS, FEFLOW, …) wrap that loop in a commercial GUI.  

Workbench aims at a **local, open-ish middle path**: one UI and one verifyable pipeline on top of native mf6, without buying an enterprise seat.

---

## What it does

| Step | Function |
| --- | --- |
| **Import** | Site package: boundary + wells (GeoJSON / shapefile), observations CSV, surface/DEM grid, optional rivers, `project_meta.json` |
| **Build** | Structured DIS grid from package extents / spacing; layer tops & bottoms (including per-cell top surface) |
| **Run** | Calls bundled / downloaded **native USGS mf6** (no fake prebaked heads) |
| **Calibrate** | Observed vs computed heads, MAE / improvement, residuals |
| **View** | Plan, section, WebGL 3D (surfaces + well screens) |
| **Report** | Engineering report with maps, residuals, input provenance / hashes |
| **Verify** | `npm run verify:stage` gates (native mf6, no fallback runner, import packages, MAE bounds, etc.) |

---

## What it is *not*

- Not a replacement for full FloPy / PEST / PyEMU automation  
- Not FEFLOW-class transport / heat / unstructured FE  
- Not an enterprise geodatabase / ArcGIS product  
- Demo fixtures (`client_site_alpha`, `client_site_beta`) are **synthetic** — not a live client project  

Real value appears only when you run **your** site data through the same Import → Report path.

---

## Quick start (Mac Apple Silicon)

```bash
cd UndergroundWorkbench   # or your clone root
chmod +x start.sh apps/underground_workbench/start.sh
./start.sh
```

Open http://127.0.0.1:18888  

First launch downloads official USGS mf6 for macOS ARM64 (~120 MB). Needs Python 3.9+ and a one-time network connection.

Try the bundled demo package:

`apps/underground_workbench/fixtures/site_packages/client_site_alpha.zip`

---

## Site package (input format)

Zip (or folder) typically includes:

| File | Role |
| --- | --- |
| `project_meta.json` | CRS, spacing, layers, K, CHD, initial head |
| `boundary.*` | Model polygon (GeoJSON and/or shapefile) |
| `wells.*` | Wells / screens / Q |
| `observations.csv` | Observed heads |
| `surface_top.csv` | Top elevation grid (`row,col,x,y,z`) |
| `rivers.geojson` | Optional river lines |

See also `SITE_PACKAGES_FILE_AUDIT.md` for a file-by-file audit of the demo fixtures (no personal data; synthetic sites only).

---

## Free vs paid vs this

| | Free (mf6 + ModelMuse/FloPy) | Paid (Flex / GMS / FEFLOW) | Workbench |
| --- | --- | --- | --- |
| Solver | USGS mf6 | Often mf6 / own FE | **Native USGS mf6 only** |
| Workflow | You assemble | Full commercial GUI | Import → run → calibrate → 3D → report |
| Cost | $0 | High seat / year | Local app (your distribution) |
| Strength | Full scriptability | Mature conceptual model + support | One local loop + verify |
| Weakness | Manual glue | Expensive / vendor lock | Custom package format; not proven on your live jobs until you try |

---

## Status

MARKET / FIELD finished builds exist with operator `verify:stage` PASS on disk.  
Treat this as a **working prototype / local product candidate**, not a claim that it already beats FloPy or Flex on every real project.

---

## License / credits

- Groundwater engine: [USGS MODFLOW 6](https://github.com/MODFLOW-ORG/modflow6) (follow USGS terms for the binary you ship or download)  
- Workbench UI / pipeline: © project author — add your license here before publish  

---

## Contact

Roman K — hydrogeology  
Email: kovalevrm@gmail.com
