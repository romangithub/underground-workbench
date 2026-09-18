# UNDERGROUND Workbench

**Local hydrogeology workbench on USGS MODFLOW 6**

Import a site package → build a grid → run **native** `mf6` → calibrate heads → Plan / Section / 3D → engineering report.

This is **not** a new solver. The engine is official free [USGS MODFLOW 6](https://github.com/MODFLOW-ORG/modflow6). Workbench is the workflow shell around it.

**Pages:** https://romangithub.github.io/underground-workbench/  
**Author:** Roman K — hydrogeology · [kovalevrm@gmail.com](mailto:kovalevrm@gmail.com)

---

## How to use

### Requirements

- Python 3.9+
- Internet on **first** run (downloads official USGS mf6 ~100–120 MB)
- Browser for the UI

### macOS (Apple Silicon)

```bash
git clone https://github.com/romangithub/underground-workbench.git
cd underground-workbench
chmod +x start.sh apps/underground_workbench/start.sh
./start.sh
```

Open http://127.0.0.1:18888

First launch downloads `mf6.7.0_macarm.zip` into `apps/underground_workbench/bin/`.

### Windows (x64)

```bat
git clone https://github.com/romangithub/underground-workbench.git
cd underground-workbench\apps\underground_workbench
start.bat
```

Open http://127.0.0.1:18888

Needs Python (`py -3` or `python`) and PowerShell for the first mf6 download (`mf6.7.0_win64.zip`).  
See [apps/underground_workbench/WINDOWS.md](apps/underground_workbench/WINDOWS.md).

### Linux (x86_64)

```bash
git clone https://github.com/romangithub/underground-workbench.git
cd underground-workbench
chmod +x start.sh apps/underground_workbench/start.sh
./start.sh
```

Downloads `mf6.7.0_linux.zip` on first run.

### Optional overrides

```bash
export MF6_BIN=/path/to/mf6   # use your own binary
export PORT=19000             # change HTTP port
./start.sh
```

Windows:

```bat
set "MF6_BIN=C:\path\to\mf6.exe"
set "PORT=19000"
start.bat
```

---

## Demo workflow (in the UI)

1. **Import** a site package zip (demo included):
   `apps/underground_workbench/fixtures/site_packages/client_site_alpha.zip`
2. **Build** grid / layers from the package
3. **Run** native mf6
4. **Calibrate** — observed vs computed heads (MAE / residuals)
5. **View** Plan / Section / 3D
6. **Report** — engineering report with maps and provenance

Verify gates (optional):

```bash
cd apps/underground_workbench
npm run verify:stage
```

---

## Site package format

| File | Role |
| --- | --- |
| `project_meta.json` | CRS, spacing, layers, K, CHD, initial head |
| `boundary.*` | Model polygon (GeoJSON and/or shapefile) |
| `wells.*` | Wells / screens / Q |
| `observations.csv` | Observed heads |
| `surface_top.csv` | Top elevation grid |
| `rivers.geojson` | Optional rivers |

Demo fixtures are **synthetic** (no personal data, no live client site). Audit notes: [docs/SITE_PACKAGES_FILE_AUDIT.md](docs/SITE_PACKAGES_FILE_AUDIT.md).

---

## What it is / is not

| Is | Is not |
| --- | --- |
| Local UI loop on native USGS mf6 | New numerical engine |
| Import → calibrate → 3D → report | FloPy / PEST / FEFLOW replacement |
| Free mf6 download per OS | Enterprise GIS / geodatabase |

---

## Free vs paid vs Workbench

| | Free | Paid | Workbench |
| --- | --- | --- | --- |
| Solver | USGS mf6 | Often mf6 / FE | Native USGS mf6 only |
| Workflow | You assemble | Commercial GUI | Import → report in one app |
| Cost | $0 | High / seat | Local app |

More detail: [docs/COMPARE_FREE_PAID_OURS.md](docs/COMPARE_FREE_PAID_OURS.md).

---

## Repository layout

```
start.sh                          # Mac/Linux entry
apps/underground_workbench/
  start.sh / start.bat / WINDOWS.md
  api_server.py
  src/ frontend/ fixtures/ scripts/
docs/                             # GitHub Pages landing
```

mf6 binaries are **not** committed; they download on first start.

---

## License

- USGS MODFLOW 6: follow USGS terms for redistributed binaries
- Workbench UI / pipeline: see [LICENSE](LICENSE)
