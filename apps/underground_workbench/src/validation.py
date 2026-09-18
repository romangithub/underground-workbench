def validate_project(data):
    f=[]
    crs=data.get('crs','')
    units=data.get('units',{})
    unit_len=units.get('length') if isinstance(units,dict) else units
    if not isinstance(crs,str) or not crs.startswith('EPSG:'):
        f.append({'severity':'ERROR','code':'CRS_INVALID','message':'CRS must be EPSG code'})
    if crs=='EPSG:4326':
        f.append({'severity':'ERROR','code':'CRS_GEOGRAPHIC','message':'MARKET requires projected CRS in meters, not geographic degrees'})
    if unit_len!='meters':
        f.append({'severity':'ERROR','code':'UNITS_LENGTH','message':'Length unit must be meters'})
    g=data.get('grid',{})
    if int(g.get('nlay',0))<2 or not g.get('botm'):
        f.append({'severity':'ERROR','code':'NO_LAYERS','message':'Layer/bottom surfaces are required'})
    for k in ['nrow','ncol']:
        if int(g.get(k,0))<6:
            f.append({'severity':'ERROR','code':'GRID_TOO_SMALL','message':'Imported extents/spacing grid must be non-toy'})
    if not data.get('wells'):
        f.append({'severity':'ERROR','code':'NO_WELLS','message':'At least one well required'})
    if not data.get('rivers'):
        f.append({'severity':'ERROR','code':'NO_RIV','message':'At least one RIV feature required'})
    if not data.get('observations'):
        f.append({'severity':'ERROR','code':'NO_OBS','message':'At least one observation required'})
    if data.get('market_site_package'):
        needed={'boundary.geojson','wells.geojson','wells.csv','observations.csv','surface_top.csv'}
        got={p['file'] for p in data.get('provenance',[])}
        miss=needed-got
        if miss:
            f.append({'severity':'ERROR','code':'MARKET_RAW_FILES_MISSING','message':'Missing raw files: '+','.join(sorted(miss))})
    return f

def has_blocking(findings):
    return any(x['severity']=='ERROR' for x in findings)
