from pathlib import Path
import os, shutil, subprocess, hashlib, struct, math, uuid, json

def resolve_mf6(root):
    candidates=[]
    if os.environ.get('MF6_BIN'): candidates.append(Path(os.environ['MF6_BIN']))
    candidates += [Path(root)/'bin/mf6', Path('/workspace/mf6_stage4/bin/mf6')]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK): return str(c.resolve())
    found=shutil.which('mf6')
    if found: return found
    raise FileNotFoundError('MF6 binary not found. Set MF6_BIN or provide ./bin/mf6. No fallback heads are allowed.')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run_mf6(ws, root):
    exe=resolve_mf6(root); cp=subprocess.run([exe],cwd=ws,capture_output=True,text=True)
    Path(ws,'mf6.stdout').write_text(cp.stdout); Path(ws,'mf6.stderr').write_text(cp.stderr); Path(ws,'mf6.exit').write_text(str(cp.returncode))
    if cp.returncode!=0: raise RuntimeError('native mf6 failed exit=%s stderr=%s'%(cp.returncode,cp.stderr[-1000:]))
    hds=Path(ws,'flow.hds'); cbc=Path(ws,'flow.cbc')
    if not hds.exists() or hds.stat().st_size==0: raise RuntimeError('native mf6 produced no flow.hds')
    if not cbc.exists() or cbc.stat().st_size==0: raise RuntimeError('native mf6 produced no flow.cbc')
    return {'exit_code':cp.returncode,'workspace':str(Path(ws)),'stdout_contains_modflow':'MODFLOW 6' in cp.stdout or 'MODFLOW-6' in cp.stdout,'hds_size':hds.stat().st_size,'cbc_size':cbc.stat().st_size,'hds_sha256':sha(hds),'cbc_sha256':sha(cbc),'mf6_stdout':str(Path(ws,'mf6.stdout'))}

def read_hds(path,nlay,nrow,ncol):
    arr=[[[0.0 for _ in range(ncol)] for _ in range(nrow)] for _ in range(nlay)]
    with open(path,'rb') as f:
      for _ in range(nlay):
        hdr=f.read(52)
        if len(hdr)!=52: raise RuntimeError('short HDS header')
        kstp,kper,pertim,totim,text,cn,rn,ilay=struct.unpack('<iidd16siii',hdr)
        raw=f.read(8*nrow*ncol)
        if len(raw)!=8*nrow*ncol: raise RuntimeError('short HDS data')
        vals=struct.unpack('<'+'d'*(nrow*ncol), raw)
        idx=0
        for r in range(nrow):
          for c in range(ncol):
            arr[ilay-1][r][c]=float(vals[idx]); idx+=1
    return arr

def obs_heads(data, ws):
    g=data['grid']; arr=read_hds(Path(ws)/'flow.hds',g['nlay'],g['nrow'],g['ncol'])
    out=[]; dry=0
    for o in data['observations']:
      val=float(arr[o['layer']-1][o['row']-1][o['col']-1])
      finite=math.isfinite(val) and abs(val)<1e20
      if not finite:
        dry+=1
        continue
      out.append({'id':o['id'],'layer':o['layer'],'row':o['row'],'col':o['col'],'observed_head':o['observed_head'],'computed_head':val,'residual':o['observed_head']-val})
    if not out: raise RuntimeError('no finite observation heads')
    mae=sum(abs(x['residual']) for x in out)/len(out); rmse=(sum(x['residual']**2 for x in out)/len(out))**0.5
    return {'obs':out,'finite_obs_count':len(out),'dry_rejected_count':dry,'mae':mae,'rmse':rmse}
