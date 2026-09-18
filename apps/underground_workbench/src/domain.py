from dataclasses import dataclass, field
from typing import List, Dict, Any
@dataclass
class Project: project_id:str; name:str; crs:str; units:Dict[str,str]; grid:Dict[str,Any]
@dataclass
class Finding: severity:str; code:str; message:str
@dataclass
class ModelBuild: model_id:str; workspace:str; package_sha256:str; grid:Dict[str,Any]
@dataclass
class RunResult: run_id:str; workspace:str; exit_code:int; hds_sha256:str; cbc_sha256:str; heads:Dict[str,float]
