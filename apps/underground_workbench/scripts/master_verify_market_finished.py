#!/usr/bin/env python3
from pathlib import Path
import sys, json, os, zipfile, socket, subprocess, time, urllib.request
from urllib.error import URLError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT))
from importer import import_project
from validation import validate_project, has_blocking
from workflow import run_field_workflow
errors=[]
# zero anti-goal grep
for p in list((ROOT/'src').glob('*.py'))+[ROOT/'frontend/public/app.js']:
    txt=p.read_text()
    for token in ['FALLBACK_'+'NUMERIC_'+'HEADS','synthetic'+'_heads','prebaked'+' heads','adult_'+'package_'+'sha_'+'placeholder','drawArrays(gl.'+'POINTS']:
        if token in txt:
            errors.append(f'forbidden token {token} in {p}')
# bundled mf6
if not (ROOT/'bin/mf6').exists(): errors.append('bundled bin/mf6 missing')
# market raw package import and dynamic grid
site_base=ROOT/'fixtures/site_packages'
site_results={}
for ds,expect_crs in [('client_site_alpha','EPSG:32637'),('client_site_beta','EPSG:32633')]:
    for src in [site_base/ds, site_base/(ds+'.zip')]:
        try:
            data=import_project(src)
            findings=validate_project(data)
            if has_blocking(findings): errors.append(f'{ds} blocking validation from {src}: {findings}')
            if data.get('crs')!=expect_crs: errors.append(f'{ds} CRS mismatch')
            if not data.get('market_site_package'): errors.append(f'{ds} not marked market package')
            raw=set(data.get('raw_formats',[]))
            needed={'boundary.geojson','wells.geojson','wells.csv','observations.csv','surface_top.csv'}
            if not needed.issubset(raw): errors.append(f'{ds} missing raw formats {needed-raw}')
            if 'boundary.shp' not in raw or 'wells.shp' not in raw: errors.append(f'{ds} lacks shapefile provenance')
            g=data['grid']
            tg=g.get('top_array') or []
            if len(data.get('surface_top_points',[])) < g['nrow']*g['ncol']: errors.append(f'{ds} surface_top.csv is not per-cell DEM/top grid')
            flat=[float(v) for row in tg for v in row]
            if not flat or max(flat)-min(flat) < 0.5: errors.append(f'{ds} surface top grid too flat/not used')
            botm_arr=g.get('botm_array') or []
            if len(botm_arr) != g['nlay']: errors.append(f'{ds} BOTM lacks cell-by-cell layer arrays')
            else:
                for li,arr in enumerate(botm_arr, start=1):
                    vals=[float(v) for row in arr for v in row]
                    if len(arr) != g['nrow'] or any(len(row)!=g['ncol'] for row in arr): errors.append(f'{ds} BOTM L{li} wrong shape')
                    if max(vals)-min(vals) < 0.05: errors.append(f'{ds} BOTM L{li} appears constant')
            if (g['nlay'],g['nrow'],g['ncol']) in [(6,16,12),(6,12,16)]: errors.append(f'{ds} uses old toy grid')
            if g['nrow']<6 or g['ncol']<6: errors.append(f'{ds} grid too small')
            if len(data.get('provenance',[]))<5: errors.append(f'{ds} lacks provenance')
            site_results[ds]=data
        except Exception as exc:
            errors.append(f'import failed for {src}: {exc!r}')
# shapefile-only package import
try:
    shp_data=import_project(site_base/'client_site_alpha_shp.zip')
    shp_raw=set(shp_data.get('raw_formats',[]))
    if 'boundary.geojson' in shp_raw or 'wells.geojson' in shp_raw: errors.append('shapefile-only package unexpectedly used geojson')
    if 'boundary.shp' not in shp_raw or 'wells.shp' not in shp_raw: errors.append('shapefile-only package did not import shapefile geometry')
    if shp_data['grid']['nrow'] != site_results['client_site_alpha']['grid']['nrow'] or shp_data['grid']['ncol'] != site_results['client_site_alpha']['grid']['ncol']:
        errors.append('shapefile-only grid differs from alpha')
except Exception as exc:
    errors.append('shapefile-only import failed '+repr(exc))
# negatives
for bad in ['bad_market_crs','bad_market_no_layers']:
    try:
        data=import_project(site_base/bad)
        if not has_blocking(validate_project(data)): errors.append(f'negative {bad} not blocking')
    except Exception:
        pass
# native MF6 workflow on both sites
workflows={}
for ds in ['client_site_alpha','client_site_beta']:
    try:
        ev=run_field_workflow(ROOT,ds)
        workflows[ds]=ev
        if ev['baseline']['calibration']['mae']>5.0: errors.append(f'{ds} baseline MAE >5')
        if ev['improvement']<0.5: errors.append(f'{ds} improvement <0.5')
        if ev['baseline']['run']['hds_sha256']==ev['best']['run']['hds_sha256']: errors.append(f'{ds} HDS SHA not distinct')
        if not ev['baseline']['run']['stdout_contains_modflow']: errors.append(f'{ds} mf6 stdout lacks MODFLOW 6')
        dis_txt=Path(ev['baseline']['run']['workspace']).joinpath('flow.dis').read_text() if 'workspace' in ev['baseline']['run'] else ''
        if 'BOTM LAYERED' not in dis_txt or 'BOTM LAYERED\n    CONSTANT' in dis_txt:
            errors.append(f'{ds} DIS BOTM is not cell-by-cell INTERNAL arrays')
        # independent survey evidence: obs are in raw CSV and are not identical to computed heads.
        diffs=[abs(o['observed_head']-o['computed_head']) for o in ev['baseline']['calibration']['obs']]
        if not any(d>0.25 for d in diffs): errors.append(f'{ds} obs too close to computed heads; possible paint')
    except Exception as exc:
        errors.append(f'workflow failed for {ds}: {exc!r}')
# app/API/report checks
js=(ROOT/'frontend/public/app.js').read_text()
for token in ['gl.TRIANGLES','gl.LINES','surface_top_grid','head color scale','client_site_alpha','client_site_beta','client_site_alpha_shp','data-selected-cell','screen_top','screen_bottom']:
    if token not in js: errors.append('frontend MARKET token missing '+token)
# API live smoke on free port
def choose_port():
    for p in range(18888,19000):
        with socket.socket() as s:
            try: s.bind(('127.0.0.1',p)); return p
            except OSError: pass
    raise RuntimeError('no free port')
port=choose_port(); env=os.environ.copy(); env['PORT']=str(port)
proc=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
base=f'http://127.0.0.1:{port}'
try:
    ready=False; last=None
    for _ in range(100):
        try:
            with urllib.request.urlopen(base+'/app.js',timeout=.5) as r:
                body=r.read().decode()
            ready=True; break
        except Exception as exc:
            last=exc; time.sleep(.1)
    if not ready:
        errors.append('API readiness failed '+repr(last))
    else:
        with urllib.request.urlopen(base+'/api/import?dataset=client_site_beta',timeout=5) as r:
            body=json.loads(r.read())
        if body['crs']!='EPSG:32633' or 'surface_top.csv' not in body.get('raw_formats',[]): errors.append('API dataset switch/raw formats failed')
except Exception as exc:
    errors.append('API smoke failed '+repr(exc))
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
# report check from last workflow
rep=ROOT/'evidence/report.html'
if workflows:
    from api_server import write_report
    write_report(list(workflows.values())[0],rep)
if not rep.exists() or rep.stat().st_size<3000:
    errors.append('report too thin/missing')
else:
    rtxt=rep.read_text()
    for token in ['Plan map','Section map','Residual scatter/table','Input provenance','Run evidence hashes','Limitations','well-line','river','obs','top-surface','botm-surface','BOTM L1 cell-by-cell']:
        if token not in rtxt: errors.append('report token missing '+token)
    if rtxt.count('<circle') < 4 or rtxt.count('<polyline') < 4:
        errors.append('report maps/residuals are too sparse; expected real grid/well/obs/residual SVG content')
out={'status':'FAIL' if errors else 'PASS','errors':errors,'sites':{k:{'grid':v['grid'],'crs':v['crs'],'provenance_files':[p['file'] for p in v.get('provenance',[])]} for k,v in site_results.items()},'workflows':{k:{'baseline_mae':v['baseline']['calibration']['mae'],'improvement':v['improvement'],'baseline_hds_sha256':v['baseline']['run']['hds_sha256'],'best_hds_sha256':v['best']['run']['hds_sha256']} for k,v in workflows.items()}}
(ROOT/'evidence/market_finished_verify.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
sys.exit(1 if errors else 0)
