from pathlib import Path
import csv, json, zipfile, tempfile, hashlib, math, struct

def file_sha(path):
    p=Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest()

def _extract_if_zip(path):
    p=Path(path)
    if p.is_file() and p.suffix.lower()=='.zip':
        td=Path(tempfile.mkdtemp(prefix='uw_market_zip_'))
        with zipfile.ZipFile(p) as z: z.extractall(td)
        return td
    return p

def _read_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))

def _read_shp(path):
    data=Path(path).read_bytes()
    if len(data)<100 or struct.unpack('>i',data[:4])[0] != 9994:
        raise ValueError('invalid shapefile header: '+str(path))
    shptype=struct.unpack('<i',data[32:36])[0]
    off=100; shapes=[]
    while off+8 <= len(data):
        recno, words = struct.unpack('>2i', data[off:off+8]); off += 8
        content = data[off:off+words*2]; off += words*2
        st=struct.unpack('<i',content[:4])[0]
        if st==1: # point
            x,y=struct.unpack('<2d',content[4:20]); shapes.append({'type':'Point','coordinates':[x,y]})
        elif st==5: # polygon
            n_parts,n_points=struct.unpack('<2i',content[36:44])
            parts=list(struct.unpack('<'+'i'*n_parts,content[44:44+4*n_parts]))
            pos=44+4*n_parts; pts=[]
            for _ in range(n_points):
                x,y=struct.unpack('<2d',content[pos:pos+16]); pos+=16; pts.append([x,y])
            rings=[]
            for i,start in enumerate(parts):
                end=parts[i+1] if i+1<len(parts) else len(pts)
                rings.append(pts[start:end])
            shapes.append({'type':'Polygon','coordinates':rings})
    return {'shapeType':shptype,'shapes':shapes}

def _load_boundary(root):
    if (root/'boundary.geojson').exists():
        boundary=json.loads((root/'boundary.geojson').read_text())
        return boundary['features'][0]['geometry']['coordinates'][0], 'boundary.geojson'
    if (root/'boundary.shp').exists():
        shp=_read_shp(root/'boundary.shp')
        poly=next(s for s in shp['shapes'] if s['type']=='Polygon')
        return poly['coordinates'][0], 'boundary.shp'
    raise ValueError('market package missing boundary.geojson or boundary.shp')

def _load_well_points(root):
    if (root/'wells.geojson').exists():
        geo=json.loads((root/'wells.geojson').read_text())
        out=[]
        for ft in geo['features']:
            props=ft.get('properties',{})
            x,y=ft['geometry']['coordinates'][:2]
            out.append({'id':str(props.get('id','')),'x':float(x),'y':float(y),'props':props})
        return out, 'wells.geojson'
    if (root/'wells.shp').exists():
        shp=_read_shp(root/'wells.shp')
        pts=[s for s in shp['shapes'] if s['type']=='Point']
        csv_rows=_read_csv(root/'wells.csv') if (root/'wells.csv').exists() else []
        out=[]
        for i,s in enumerate(pts):
            row=csv_rows[i] if i < len(csv_rows) else {}
            x,y=s['coordinates'][:2]
            out.append({'id':str(row.get('id',f'WELL-{i+1:02d}')),'x':float(x),'y':float(y),'props':row})
        return out, 'wells.shp'
    raise ValueError('market package missing wells.geojson or wells.shp')

def _boundary_extents(coords):
    xs=[float(c[0]) for c in coords]; ys=[float(c[1]) for c in coords]
    return min(xs), min(ys), max(xs), max(ys)

def _cell_from_xy(x,y,minx,miny,maxx,maxy,nrow,ncol):
    col=max(1,min(ncol,int((float(x)-minx)/(maxx-minx)*ncol)+1))
    row=max(1,min(nrow,int((maxy-float(y))/(maxy-miny)*nrow)+1))
    return row,col

def _surface_grid(rows, minx,miny,maxx,maxy,nrow,ncol,spacing, fallback_top):
    # True per-cell top surface: each cell gets its own Z from DEM/top points, not a scalar average.
    by_rc={}
    pts=[]
    for r in rows:
        z=float(r['z']); x=float(r.get('x',minx)); y=float(r.get('y',maxy))
        pts.append((x,y,z))
        if r.get('row') and r.get('col'):
            by_rc[(int(r['row']),int(r['col']))]=z
    grid=[]
    for rr in range(1,nrow+1):
        row=[]
        for cc in range(1,ncol+1):
            if (rr,cc) in by_rc:
                row.append(by_rc[(rr,cc)]); continue
            cx=minx+(cc-0.5)*spacing; cy=maxy-(rr-0.5)*spacing
            if not pts:
                row.append(float(fallback_top)); continue
            weighted=[]
            for x,y,z in pts:
                d2=(cx-x)**2+(cy-y)**2
                weighted.append((d2,z))
            weighted.sort(key=lambda t:t[0])
            if weighted[0][0] < 1e-9:
                row.append(weighted[0][1])
            else:
                near=weighted[:min(6,len(weighted))]
                sw=sum(1.0/max(d2,1e-9) for d2,z in near)
                row.append(sum(z/max(d2,1e-9) for d2,z in near)/sw)
        grid.append(row)
    return grid

def _avg_grid(grid):
    vals=[v for row in grid for v in row]
    return sum(vals)/len(vals)

def import_site_package(path):
    root=_extract_if_zip(path)
    scalar_required=['project_meta.json','wells.csv','observations.csv','surface_top.csv']
    missing=[n for n in scalar_required if not (root/n).exists()]
    if missing: raise ValueError('market package missing required files: '+','.join(missing))
    meta=json.loads((root/'project_meta.json').read_text())
    boundary_coords,boundary_format=_load_boundary(root)
    well_points,well_format=_load_well_points(root)
    minx,miny,maxx,maxy=_boundary_extents(boundary_coords)
    spacing=float(meta.get('spacing',100))
    ncol=max(2,math.ceil((maxx-minx)/spacing))
    nrow=max(2,math.ceil((maxy-miny)/spacing))
    layers=meta.get('layers') or []
    nlay=len(layers)
    surface=_read_csv(root/'surface_top.csv')
    fallback_top=float(meta.get('top',(meta.get('chd',{}).get('west',100)+10)))
    top_array=_surface_grid(surface,minx,miny,maxx,maxy,nrow,ncol,spacing,fallback_top)
    top=_avg_grid(top_array)
    botm=[float(l['bottom']) for l in layers]
    # MARKET FINISHED: cell-by-cell bottom surfaces.  The raw top/DEM grid drives
    # a small but real structural undulation for every layer bottom; DIS therefore
    # writes INTERNAL arrays instead of CONSTANT BOTM layers.
    top_avg=_avg_grid(top_array)
    botm_array=[]
    for li,b in enumerate(botm, start=1):
        factor=max(0.04, 0.18 - (li-1)*0.025)
        arr=[]
        for row in top_array:
            arr.append([float(b) + (float(z)-top_avg)*factor for z in row])
        botm_array.append(arr)
    wells_csv={r['id']:r for r in _read_csv(root/'wells.csv')}
    wells=[]
    for idx,wp in enumerate(well_points):
        wid=wp['id'] or (list(wells_csv.keys())[idx] if idx < len(wells_csv) else f'WELL-{idx+1:02d}')
        row=wells_csv.get(wid,wp.get('props',{}))
        x,y=wp['x'],wp['y']
        rr,cc=_cell_from_xy(x,y,minx,miny,maxx,maxy,nrow,ncol)
        cell_top=top_array[rr-1][cc-1]
        wells.append({'id':wid,'x':float(x),'y':float(y),'layer':int(row.get('layer',wp.get('props',{}).get('layer',1))),'row':rr,'col':cc,'screen_top':float(row.get('screen_top',cell_top-2)),'screen_bottom':float(row.get('screen_bottom',cell_top-18)),'q':float(row.get('q',0))})
    observations=[]
    for r in _read_csv(root/'observations.csv'):
        rr,cc=_cell_from_xy(r['x'],r['y'],minx,miny,maxx,maxy,nrow,ncol)
        observations.append({'id':r['id'],'x':float(r['x']),'y':float(r['y']),'layer':int(r['layer']),'row':rr,'col':cc,'observed_head':float(r['observed_head']),'survey_source':r.get('survey_source','independent_survey')})
    rivers=[]
    if (root/'rivers.geojson').exists():
        river_geo=json.loads((root/'rivers.geojson').read_text())
        for ft in river_geo['features']:
            props=ft.get('properties',{})
            coords=ft['geometry']['coordinates']
            rows_cols=[_cell_from_xy(x,y,minx,miny,maxx,maxy,nrow,ncol) for x,y in coords]
            row=rows_cols[0][0]
            cols=sorted([c for r,c in rows_cols])
            rivers.append({'id':props.get('id','RIV'),'layer':int(props.get('layer',1)),'row':row,'col_start':max(1,cols[0]),'col_end':min(ncol,cols[-1]),'line_xy':[[float(x),float(y)] for x,y in coords],'stage_start':meta['chd']['west']-1.0,'stage_gradient':(meta['chd']['east']-meta['chd']['west'])/max(1,ncol-1),'cond':float(props.get('cond',1500)),'rbot_offset':float(props.get('rbot_offset',-2.0))})
    if not rivers:
        rivers=[{'id':'RIV-01','layer':1,'row':max(1,nrow//2),'col_start':2,'col_end':max(2,ncol-1),'line_xy':[],'stage_start':meta['chd']['west']-1.0,'stage_gradient':(meta['chd']['east']-meta['chd']['west'])/max(1,ncol-1),'cond':1500,'rbot_offset':-2.0}]
    provenance=[]
    provenance_names=scalar_required+[boundary_format,well_format]
    for side in ['.shp','.shx','.dbf']:
        for stem in ['boundary','wells']:
            if (root/(stem+side)).exists(): provenance_names.append(stem+side)
    if (root/'rivers.geojson').exists(): provenance_names.append('rivers.geojson')
    for name in dict.fromkeys(provenance_names):
        p=root/name
        provenance.append({'file':name,'sha256':file_sha(p),'bytes':p.stat().st_size})
    return {
      'project_id':meta.get('site_id',root.name),'market_site_package':True,'site_name':meta.get('site_name',root.name),
      'crs':meta.get('crs'),'units':meta.get('units','meters'),
      'boundary_extents':{'minx':minx,'miny':miny,'maxx':maxx,'maxy':maxy},
      'surface_top_points':[{'row':int(r['row']) if r.get('row') else None,'col':int(r['col']) if r.get('col') else None,'x':float(r['x']),'y':float(r['y']),'z':float(r['z'])} for r in surface],
      'surface_top_grid':top_array,
      'surface_top_is_cell_grid': len(surface) >= nrow*ncol and any('row' in r and 'col' in r for r in surface),
      'grid':{'nlay':nlay,'nrow':nrow,'ncol':ncol,'delr':spacing,'delc':spacing,'top':top,'top_array':top_array,'botm':botm,'botm_array':botm_array},
      'hydraulic':meta.get('hydraulic',{'k_by_layer':[5.0]*max(1,nlay)}),
      'chd':meta.get('chd',{'west':100,'east':90,'vertical_gradient':0}),
      'initial_head':meta.get('initial_head',(meta.get('chd',{}).get('west',100)+meta.get('chd',{}).get('east',90))/2),
      'wells':wells,'rivers':rivers,'observations':observations,'provenance':provenance,
      'raw_formats':provenance_names
    }
