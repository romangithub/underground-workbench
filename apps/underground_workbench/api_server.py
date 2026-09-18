from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import json, os, shutil, sys
sys.path.insert(0,str(Path(__file__).parent/'src'))
from importer import import_project
from validation import validate_project, has_blocking
from workflow import run_field_workflow

def dataset_path(ds):
    for p in [ROOT/'fixtures/site_packages'/ds, ROOT/'fixtures/site_packages'/(ds+'.zip'), ROOT/'fixtures/raw_projects'/ds]:
        if p.exists(): return p
    return ROOT/'fixtures/raw_projects'/ds

def load_dataset(ds):
    return import_project(dataset_path(ds))
ROOT=Path(__file__).parent
STATE={'dataset':'client_site_alpha','last':None}
ThreadingHTTPServer.allow_reuse_address = True
class ReuseThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

class H(SimpleHTTPRequestHandler):
    def do_HEAD(self):
      return self.do_GET(head=True)
    def do_GET(self, head=False):
      u=urlparse(self.path)
      if u.path.startswith('/api/import'):
        ds=parse_qs(u.query).get('dataset',['client_site_alpha'])[0]; STATE['dataset']=ds
        data=load_dataset(ds); body={'dataset':ds,'project_id':data['project_id'],'site_name':data.get('site_name'),'crs':data['crs'],'units':data['units'],'grid':data['grid'],'boundary_extents':data.get('boundary_extents'),'surface_top_points':data.get('surface_top_points',[]),'wells':data['wells'],'rivers':data['rivers'],'observations':data['observations'],'provenance':data.get('provenance',[]),'raw_formats':data.get('raw_formats',[])}; return self.json(body,head)
      if u.path=='/api/validate':
        data=load_dataset(STATE['dataset']); return self.json({'findings':validate_project(data)},head)
      if u.path=='/api/run-calibrate':
        ev=run_field_workflow(ROOT, STATE['dataset']); STATE['last']=ev; return self.json(ev,head)
      if u.path=='/api/report':
        p=ROOT/'evidence/report.html';
        if not p.exists() and STATE['last']: write_report(STATE['last'],p)
        if p.exists():
          b=p.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(b))); self.end_headers();
          if not head: self.wfile.write(b); return
      # static
      if u.path=='/' or u.path=='/index.html': fp=ROOT/'frontend/public/index.html'; ctype='text/html'
      elif u.path=='/app.js': fp=ROOT/'frontend/public/app.js'; ctype='application/javascript'
      elif u.path=='/styles.css': fp=ROOT/'frontend/public/styles.css'; ctype='text/css'
      else: self.send_error(404); return
      b=fp.read_bytes(); self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(b))); self.end_headers();
      if not head: self.wfile.write(b)
    def json(self,obj,head=False):
      b=json.dumps(obj).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers();
      if not head: self.wfile.write(b)
def _norm(v, lo, hi, a, b):
    if hi == lo:
        return (a+b)/2
    return a + (float(v)-float(lo))*(b-a)/(float(hi)-float(lo))

def write_report(ev,p):
    ext=ev.get('boundary_extents') or {'minx':0,'miny':0,'maxx':1,'maxy':1}
    minx,miny,maxx,maxy=ext['minx'],ext['miny'],ext['maxx'],ext['maxy']
    wells=ev.get('wells',[])
    rivers=ev.get('rivers',[])
    obs_best=ev['best']['calibration']['obs']
    obs_by_id={o['id']:o for o in obs_best}
    obs_raw=ev.get('observations',[])
    prov=''.join(f"<tr><td>{q.get('file')}</td><td><code>{q.get('sha256')}</code></td><td>{q.get('bytes')}</td></tr>" for q in ev.get('provenance',[]))
    rows=''.join(f"<tr><td>{o['id']}</td><td>{o['observed_head']:.3f}</td><td>{o['computed_head']:.3f}</td><td>{o['residual']:.3f}</td><td>{abs(o['residual']):.3f}</td></tr>" for o in obs_best)
    grid=ev.get('grid',{})
    # Real plan map: boundary from extents, wells from imported coordinates, observations from imported coordinates, residual size from solver residuals.
    well_svg=''.join(
        f"<g><line x1='{_norm(w['x'],minx,maxx,40,760):.1f}' y1='{_norm(w['y'],maxy,miny,40,420):.1f}' x2='{_norm(w['x'],minx,maxx,40,760):.1f}' y2='{_norm(w['y'],maxy,miny,48,428):.1f}' class='well-line'/><circle cx='{_norm(w['x'],minx,maxx,40,760):.1f}' cy='{_norm(w['y'],maxy,miny,40,420):.1f}' r='5' class='well'/><text x='{_norm(w['x'],minx,maxx,40,760)+7:.1f}' y='{_norm(w['y'],maxy,miny,40,420)-7:.1f}'>{w['id']}</text></g>" for w in wells)
    river_svg=''
    for rv in rivers:
        pts=rv.get('line_xy') or []
        if pts:
            coords=' '.join(f"{_norm(x,minx,maxx,40,760):.1f},{_norm(y,maxy,miny,40,420):.1f}" for x,y in pts)
        else:
            r=rv.get('row',1); y=40+(r/max(1,grid.get('nrow',1)))*380; coords=f"60,{y:.1f} 740,{y:.1f}"
        river_svg += f"<polyline points='{coords}' class='river'/>"
    obs_svg=''
    for o in obs_raw:
        cal=obs_by_id.get(o['id'],{})
        rad=4+min(16,abs(float(cal.get('residual',0)))*3)
        obs_svg += f"<g><circle cx='{_norm(o['x'],minx,maxx,40,760):.1f}' cy='{_norm(o['y'],maxy,miny,40,420):.1f}' r='{rad:.1f}' class='obs'/><text x='{_norm(o['x'],minx,maxx,40,760)+7:.1f}' y='{_norm(o['y'],maxy,miny,40,420)+5:.1f}'>{o['id']}</text></g>"
    # Real section map: sampled imported DEM/top along middle row and cell-by-cell BOTM surfaces from DIS source arrays.
    tg=grid.get('top_array') or []
    botm_arrays=grid.get('botm_array') or []
    mid=max(0,min(len(tg)-1, len(tg)//2)) if tg else 0
    def line_for(vals, y_min, y_max):
        if not vals: return ''
        vmin=min(y_min,min(vals)); vmax=max(y_max,max(vals))
        return ' '.join(f"{40+i*(720/max(1,len(vals)-1)):.1f},{_norm(v,vmax,vmin,40,330):.1f}" for i,v in enumerate(vals))
    top_vals=tg[mid] if tg else []
    all_vals=list(top_vals)
    for arr in botm_arrays:
        if arr: all_vals += arr[mid]
    y_min=min(all_vals) if all_vals else 0; y_max=max(all_vals) if all_vals else 1
    section_lines=f"<polyline points='{line_for(top_vals,y_min,y_max)}' class='top-surface'/><text x='45' y='30'>Imported top / DEM</text>"
    for i,arr in enumerate(botm_arrays):
        vals=arr[mid] if arr else []
        section_lines += f"<polyline points='{line_for(vals,y_min,y_max)}' class='botm-surface'/><text x='45' y='{55+i*18}'>BOTM L{i+1} cell-by-cell</text>"
    scatter=''
    obs_min=min([o['observed_head'] for o in obs_best] or [0]); obs_max=max([o['observed_head'] for o in obs_best] or [1])
    comp_min=min([o['computed_head'] for o in obs_best] or [0]); comp_max=max([o['computed_head'] for o in obs_best] or [1])
    lo=min(obs_min,comp_min); hi=max(obs_max,comp_max)
    for o in obs_best:
        scatter += f"<circle cx='{_norm(o['computed_head'],lo,hi,50,360):.1f}' cy='{_norm(o['observed_head'],hi,lo,30,260):.1f}' r='5'><title>{o['id']} residual {o['residual']:.3f}</title></circle>"
    html=f"""<html><head><title>UNDERGROUND Workbench MARKET FINISHED Report</title><style>body{{font-family:Arial,sans-serif;margin:32px}}svg{{border:1px solid #ccd;margin:8px 0 22px}}table{{border-collapse:collapse;width:100%;margin:8px 0 22px}}td,th{{border:1px solid #ddd;padding:6px;font-size:12px}}code{{font-size:11px}}.well{{fill:#d33}}.well-line{{stroke:#d33;stroke-width:3}}.river{{stroke:#1677ff;stroke-width:4;fill:none}}.obs{{fill:#f6a000;fill-opacity:.55;stroke:#8a5200}}.top-surface{{stroke:#111;stroke-width:3;fill:none}}.botm-surface{{stroke:#6b7280;stroke-width:2;fill:none}}</style></head><body><h1>UNDERGROUND Workbench MARKET / CLIENT FIELD FINISHED Report</h1><p>Report generated from imported client package grid, wells, observations, residuals and native MODFLOW 6 run evidence.</p><h2>Plan map</h2><svg width='820' height='460'><rect x='40' y='40' width='720' height='380' fill='none' stroke='black'/>{river_svg}{well_svg}{obs_svg}</svg><h2>Section map</h2><svg width='820' height='360'>{section_lines}</svg><h2>Residual scatter/table</h2><svg width='420' height='300'><line x1='50' y1='260' x2='360' y2='260' stroke='black'/><line x1='50' y1='30' x2='50' y2='260' stroke='black'/><line x1='50' y1='260' x2='360' y2='30' stroke='#999' stroke-dasharray='4 4'/>{scatter}<text x='150' y='292'>Computed head</text><text x='5' y='25'>Observed</text></svg><table><tr><th>obs</th><th>observed</th><th>computed</th><th>residual</th><th>abs residual</th></tr>{rows}</table><h2>Input provenance</h2><table><tr><th>file</th><th>sha256</th><th>bytes</th></tr>{prov}</table><h2>Run evidence hashes</h2><pre>{json.dumps(ev['baseline']['run'],indent=2)}\n{json.dumps(ev['best']['run'],indent=2)}</pre><h2>Grid evidence</h2><pre>{json.dumps({'nlay':grid.get('nlay'),'nrow':grid.get('nrow'),'ncol':grid.get('ncol'),'has_top_array':bool(grid.get('top_array')),'has_botm_array':bool(grid.get('botm_array'))},indent=2)}</pre><h2>Limitations</h2><p>This package demonstrates reproducible MARKET / CLIENT FIELD workflow. Final engineering decisions still require qualified hydrogeological review and client data QA.</p></body></html>"""
    p.write_text(html)
def main():
  port=int(os.environ.get('PORT','18888')); ReuseThreadingHTTPServer(('127.0.0.1',port),H).serve_forever()
if __name__=='__main__': main()
