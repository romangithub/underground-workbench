from pathlib import Path
import shutil, json, uuid
from importer import import_project
from validation import validate_project, has_blocking
from model_builder import build_packages
from runner import run_mf6, obs_heads, sha

def run_field_workflow(root, dataset='calibratable_basin'):
    root=Path(root); 
    # MARKET/CLIENT FIELD supports both legacy FIELD JSON fixtures and raw site packages.
    candidates=[root/'fixtures/site_packages'/dataset, root/'fixtures/site_packages'/(dataset+'.zip'), root/'fixtures/raw_projects'/dataset]
    project_dir=next((c for c in candidates if c.exists()), candidates[-1])
    data=import_project(project_dir)
    findings=validate_project(data)
    if has_blocking(findings): raise RuntimeError('blocking validation findings: '+json.dumps(findings))
    runs=root/'runs'; shutil.rmtree(runs,ignore_errors=True); runs.mkdir(exist_ok=True)
    base_ws=runs/'baseline'
    build_packages(data, base_ws, pumping_multiplier=1.0, k_multiplier=1.0, chd_delta=0.0)
    base_run=run_mf6(base_ws, root); base_cal=obs_heads(data, base_ws)
    candidates=[('chd_plus_2',{'chd_delta':2.0}),('pump_half',{'pumping_multiplier':0.5}),('k_up',{'k_multiplier':1.5}),('pump_half_k_up',{'pumping_multiplier':0.5,'k_multiplier':1.5})]
    best=None
    for name,kw in candidates:
      ws=runs/name; build_packages(data, ws, **({'pumping_multiplier':1.0,'k_multiplier':1.0,'chd_delta':0.0}|kw))
      rr=run_mf6(ws, root); cal=obs_heads(data, ws)
      item={'name':name,'run':rr,'calibration':cal,'workspace':str(ws),'package_sha256':json.loads((ws/'package_manifest.json').read_text())['package_sha256']}
      if best is None or cal['mae']<best['calibration']['mae']: best=item
    improvement=base_cal['mae']-best['calibration']['mae']
    if base_cal['mae']>5.0: raise RuntimeError('baseline MAE FIELD fail: %.3f'%base_cal['mae'])
    if improvement<0.5: raise RuntimeError('calibration improvement FIELD fail: %.3f'%improvement)
    ev={'dataset':dataset,'grid':data['grid'],'market_site_package':data.get('market_site_package',False),'raw_formats':data.get('raw_formats',[]),'provenance':data.get('provenance',[]),'boundary_extents':data.get('boundary_extents'),'market_inputs':{'wells':len(data.get('wells',[])),'rivers':len(data.get('rivers',[])),'observations':len(data.get('observations',[])),'surface_points':len(data.get('surface_top_points',[]))},'wells':data.get('wells',[]),'rivers':data.get('rivers',[]),'observations':data.get('observations',[]),'surface_top_points':data.get('surface_top_points',[]),'findings':findings,'baseline':{'run':base_run,'calibration':base_cal,'package_sha256':json.loads((base_ws/'package_manifest.json').read_text())['package_sha256']},'best':best,'improvement':improvement,'native_solver':'mf6 subprocess only','fallback_numeric_heads_present':False}
    out=root/'evidence'; out.mkdir(exist_ok=True); (out/'field_finished_master_verify.json').write_text(json.dumps(ev,indent=2))
    return ev
