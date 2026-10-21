"""Deterministic tools. No LLM is required. Standard-library only for score/manifest tasks."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone

POSE_RE = re.compile(r'^\s*(\d+)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*$')

def parse_vina_log(path):
    """Parse Vina affinity table. Require valid table header and one or more poses."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    lines = path.read_text(errors='replace').splitlines()
    header = next((i for i,l in enumerate(lines) if 'affinity' in l.lower() and 'mode' in l.lower()), None)
    if header is None:
        raise ValueError(f'No Vina affinity/RMSD header in {path}')
    poses = []
    for line in lines[header+1:]:
        match = POSE_RE.match(line)
        if match:
            n, affinity, rmsdl, rmsdu = match.groups()
            poses.append({'pose':int(n), 'affinity_kcal_mol':float(affinity), 'rmsd_lb':float(rmsdl), 'rmsd_ub':float(rmsdu)})
        elif poses:
            break
    if not poses or poses[0]['pose'] != 1:
        raise ValueError(f'No pose 1 found in {path}')
    if len({x['pose'] for x in poses}) != len(poses):
        raise ValueError(f'Duplicate pose identifiers in {path}')
    return poses


def calculate_agvina1(energies: dict) -> dict:
    """Calculate the calibrated ERalpha agonist score."""
    threshold = 0.179475

    score = (
        energies["3uucb"]["best_energy"]
        - energies["1qkua"]["best_energy"]
    )

    return {
        "method": "agVina1-score",
        "score": round(score, 6),
        "threshold": threshold,
        "classification": (
            "active" if score > threshold else "inactive"
        ),
    }


def summarize_pair(
    agonist_log,
    antagonist_log,
    agonist_id="1qkua",
    antagonist_id="3uucb"
):
    a = parse_vina_log(agonist_log)
    b = parse_vina_log(antagonist_log)

    energies = {
        agonist_id: {
            "best_energy": min(
                x["affinity_kcal_mol"] for x in a
            ),
            "poses": len(a),
        },
        antagonist_id: {
            "best_energy": min(
                x["affinity_kcal_mol"] for x in b
            ),
            "poses": len(b),
        },
    }

    prediction = calculate_agvina1(energies)

    return {
        "receptors": energies,
        **prediction,
        "input_logs": {
            agonist_id: str(agonist_log),
            antagonist_id: str(antagonist_log),
        },
    }


def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def record_manifest(paths, destination, details=None):
    rec={'created_utc':datetime.now(timezone.utc).isoformat(), 'files':{}, 'details':details or {}}
    for p in paths:
        p=Path(p)
        if not p.is_file():raise FileNotFoundError(p)
        rec['files'][str(p.resolve())]=sha256_file(p)
    destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(rec,indent=2))
    return rec

def validate_inputs(receptor_pdbqt, ligand_pdbqt, center, size):
    for f in [receptor_pdbqt,ligand_pdbqt]:
        if not Path(f).is_file() or Path(f).stat().st_size==0:raise FileNotFoundError(f)
    if len(center)!=3 or len(size)!=3 or any(not isinstance(v,(int,float)) for v in [*center,*size]):
        raise ValueError('Center and size each require three numeric values')
    if any(x<=0 for x in size):raise ValueError('Box sizes must be positive')

def make_vina_command(receptor, ligand, center, size, output, seed=42, exhaustiveness=32, num_modes=20, vina='vina'):
    validate_inputs(receptor,ligand,center,size)
    cmd=[str(vina),'--receptor',str(receptor),'--ligand',str(ligand)]
    for key,x in zip(['center_x','center_y','center_z'],center):cmd += ['--'+key,str(x)]
    for key,x in zip(['size_x','size_y','size_z'],size):cmd += ['--'+key,str(x)]
    return cmd+['--exhaustiveness',str(exhaustiveness),'--num_modes',str(num_modes),'--seed',str(seed),'--out',str(output)]

def run_vina(command, logfile, execute=False):
    """Explicit opt-in execution: otherwise returns command only."""
    if not execute:return {'status':'dry_run','command':command}
    logfile=Path(logfile); logfile.parent.mkdir(parents=True,exist_ok=True)
    with logfile.open('w') as fp:
        result=subprocess.run(command,stdout=fp,stderr=subprocess.PIPE,text=True,timeout=7200,check=False)
    if result.returncode!=0:
        raise RuntimeError(f'Vina exited {result.returncode}: {result.stderr[-1000:]}')
    return {'status':'completed','logfile':str(logfile),'poses':parse_vina_log(logfile)}

def read_ligand_csv(path, id_column='CASRN', smiles_column='SMILES'):
    with open(path,newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    if not rows:raise ValueError('Empty ligand CSV')
    if any(id_column not in r or smiles_column not in r for r in rows):raise ValueError(f'Requires {id_column} and {smiles_column}')
    return [{ 'ligand_id':r[id_column], 'smiles':r[smiles_column]} for r in rows]

