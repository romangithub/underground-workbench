import json, zipfile, tempfile
from pathlib import Path
from market_importer import import_site_package

def import_project(path):
    p=Path(path)
    if p.is_file() and p.suffix=='.zip':
        td=Path(tempfile.mkdtemp(prefix='uw_zip_import_'))
        with zipfile.ZipFile(p) as z: z.extractall(td)
        if (td/'project.json').exists() or list(td.rglob('project.json')):
            cand=(td/'project.json') if (td/'project.json').exists() else list(td.rglob('project.json'))[0]
            return json.loads(cand.read_text())
        return import_site_package(td)
    if p.is_dir():
        if (p/'project.json').exists():
            return json.loads((p/'project.json').read_text())
        return import_site_package(p)
    return json.loads(p.read_text())
