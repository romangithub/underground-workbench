from pathlib import Path
import hashlib, json

def _write(p,s): Path(p).write_text(s)
def build_packages(data, workspace, *, pumping_multiplier=1.0, k_multiplier=1.0, chd_delta=0.0, riv_delta=0.0):
    ws=Path(workspace); ws.mkdir(parents=True, exist_ok=True)
    g=data['grid']; nlay,nrow,ncol=g['nlay'],g['nrow'],g['ncol']
    _write(ws/'mfsim.nam','''BEGIN options
END options

BEGIN timing
  TDIS6 flow.tdis
END timing

BEGIN models
  GWF6 flow.nam flow
END models

BEGIN exchanges
END exchanges

BEGIN solutiongroup 1
  IMS6 flow.ims flow
END solutiongroup
''')
    _write(ws/'flow.tdis','''BEGIN options
  TIME_UNITS days
END options

BEGIN dimensions
  NPER 1
END dimensions

BEGIN perioddata
  1.0 1 1.0
END perioddata
''')
    _write(ws/'flow.ims','''BEGIN options
  PRINT_OPTION SUMMARY
  COMPLEXITY SIMPLE
END options
''')
    _write(ws/'flow.nam','''BEGIN options
  SAVE_FLOWS
END options

BEGIN packages
  DIS6 flow.dis dis
  IC6 flow.ic ic
  NPF6 flow.npf npf
  CHD6 flow.chd chd
  WEL6 flow.wel wel
  RIV6 flow.riv riv
  OC6 flow.oc oc
END packages
''')
    if g.get('botm_array'):
        blocks=[]
        for layer in g['botm_array']:
            blocks.append('    INTERNAL FACTOR 1.0')
            blocks.extend('    ' + ' '.join(f'{float(v):.3f}' for v in row) for row in layer)
        botm='\n'.join(blocks)
    else:
        botm='\n'.join(f'    CONSTANT {b:.3f}' for b in g['botm'])
    if g.get('top_array'):
        top_block='    INTERNAL FACTOR 1.0\n' + '\n'.join('    ' + ' '.join(f'{float(v):.3f}' for v in row) for row in g['top_array'])
    else:
        top_block=f"    CONSTANT {g['top']}"
    _write(ws/'flow.dis',f'''BEGIN options
  LENGTH_UNITS meters
END options

BEGIN dimensions
  NLAY {nlay}
  NROW {nrow}
  NCOL {ncol}
END dimensions

BEGIN griddata
  DELR
    CONSTANT {g['delr']}
  DELC
    CONSTANT {g['delc']}
  TOP
{top_block}
  BOTM LAYERED
{botm}
  IDOMAIN
    CONSTANT 1
END griddata
''')
    _write(ws/'flow.ic',f'''BEGIN griddata
  STRT
    CONSTANT {data.get('initial_head',110.0)}
END griddata
''')
    k_lines='\n'.join(f'    CONSTANT {k*k_multiplier:.6f}' for k in data['hydraulic']['k_by_layer'])
    icell='\n'.join('    CONSTANT 0' for _ in range(nlay))
    _write(ws/'flow.npf',f'''BEGIN options
  SAVE_SPECIFIC_DISCHARGE
END options

BEGIN griddata
  ICELLTYPE LAYERED
{icell}
  K LAYERED
{k_lines}
END griddata
''')
    chd=[]; west=data['chd']['west']; east=data['chd']['east']; vg=data['chd'].get('vertical_gradient',0)
    for k in range(1,nlay+1):
      for r in range(1,nrow+1):
        chd.append(f'  {k} {r} 1 {west+(k-1)*vg+chd_delta:.3f}')
        chd.append(f'  {k} {r} {ncol} {east+(k-1)*vg+chd_delta:.3f}')
    _write(ws/'flow.chd','BEGIN dimensions\n  MAXBOUND '+str(len(chd))+'\nEND dimensions\n\nBEGIN period 1\n'+'\n'.join(chd)+'\nEND period\n')
    wells=[f"  {w['layer']} {w['row']} {w['col']} {w['q']*pumping_multiplier:.3f}" for w in data['wells']]
    _write(ws/'flow.wel','BEGIN dimensions\n  MAXBOUND '+str(len(wells))+'\nEND dimensions\n\nBEGIN period 1\n'+'\n'.join(wells)+'\nEND period\n')
    rivs=[]
    for rv in data['rivers']:
      for c in range(rv['col_start'], rv['col_end']+1):
        st=rv['stage_start']+(c-rv['col_start'])*rv['stage_gradient']+riv_delta
        rivs.append(f"  {rv['layer']} {rv['row']} {c} {st:.3f} {rv['cond']:.3f} {st+rv['rbot_offset']:.3f}")
    _write(ws/'flow.riv','BEGIN dimensions\n  MAXBOUND '+str(len(rivs))+'\nEND dimensions\n\nBEGIN period 1\n'+'\n'.join(rivs)+'\nEND period\n')
    _write(ws/'flow.oc','''BEGIN options
  BUDGET FILEOUT flow.cbc
  HEAD FILEOUT flow.hds
END options

BEGIN period 1
  SAVE HEAD LAST
  SAVE BUDGET LAST
  PRINT HEAD LAST
  PRINT BUDGET LAST
END period
''')
    h=hashlib.sha256()
    for p in sorted(ws.glob('flow.*'))+ [ws/'mfsim.nam']:
      if p.is_file(): h.update(p.name.encode()+b'\0'+p.read_bytes())
    (ws/'package_manifest.json').write_text(json.dumps({'package_sha256':h.hexdigest(),'grid':g},indent=2))
    return {'workspace':str(ws),'package_sha256':h.hexdigest(),'grid':g}
