# VERIFY MARKET FINISHED

Required command:

```bash
npm run verify:stage
```

Verifier gates:
- no fallback/synthetic/prebaked/numpy runner tokens;
- bundled `./bin/mf6`;
- GeoJSON/CSV/surface packages for alpha/beta;
- shapefile-only package import;
- per-cell top surface grid and non-flat top-array;
- dynamic grid not FIELD toy grid;
- native MF6/HDS SHA distinct, MAE <= 5 and improvement >= 0.5;
- WebGL TRIANGLES + LINES with `surface_top_grid`, `screen_top`, `screen_bottom`;
- report maps/residuals/provenance/evidence.
