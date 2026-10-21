"""Non-destructive integration bridge to the original scripts.

Inspect prerequisites and generate exact commands; no job is launched implicitly.
"""
from pathlib import Path
import subprocess
import sys
import json

INTERACTIONS = ("vdw", "Hpho", "pi", "Hbond")

def validate_score4_inputs(dock_root, result_dir, ligand_group, proteins, ligand_ids):
    """Verify the files scoring4_linux.py expects before attempting a run."""
    root, results = Path(dock_root), Path(result_dir)
    missing = []
    for name in ("3ert_1ere_keyresidues.csv", "3ert_1ere_coakeyresidues.csv"):
        f = root / "pyscript" / "supportingfile" / name
        if not f.is_file(): missing.append(str(f))
    for protein in proteins:
        score = results / f"{protein}-{ligand_group}_deltaG.csv"
        if not score.is_file(): missing.append(str(score))
        for interaction in INTERACTIONS:
            f = results / f"{protein}-{ligand_group}_{interaction}.csv"
            if not f.is_file(): missing.append(str(f))
        for subfolder in ("out_pdbqt", "out_sdf"):
            folder = root / f"{protein}-{ligand_group}" / subfolder
            if not folder.is_dir(): missing.append(str(folder))
        for ligand in ligand_ids:
            folder = root / f"{protein}-{ligand_group}" / "out_pdbqt"
            if folder.is_dir() and not list(folder.glob(f"{ligand}*out_model*.pdbqt")):
                missing.append(f"Pose PDBQT: {folder}/{ligand}*out_model*.pdbqt")
    return {"ready":not missing, "missing":missing, "note":"Input presence only; not chemical/numerical validation."}

def scoring4_command(script, proteins, ligand_group, ligands, result_dir, new_vectors=False, python_executable=None):
    if not proteins or not ligands: raise ValueError("Explicit protein and ligand IDs are required")
    script=Path(script)
    if not script.is_file(): raise FileNotFoundError(script)
    return [python_executable or sys.executable, str(script.resolve()),
            "--proteinlist", ",".join(proteins), "--ligandtype", ligand_group,
            "--ligandname", ",".join(ligands), "--resultpath", str(Path(result_dir).resolve()),
            "--newfpvector" if new_vectors else "--no-newfpvector"]

def run_checked_command(cmd, execute=False, cwd=None, timeout=7200):
    """Dry run by default; report process exit code and stderr on execution."""
    if not execute: return {"status":"dry_run", "argv":cmd}
    result=subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"Exit status {result.returncode}: {result.stderr[-3000:]}")
    return {"status":"finished", "returncode":result.returncode,
            "stdout_tail":result.stdout[-3000:], "stderr_tail":result.stderr[-3000:]}

def validate_converter(script, pdbqt_file, smiles):
    """Check inputs before using the original Meeko/RDKit conversion logic."""
    if not Path(script).is_file():raise FileNotFoundError(script)
    if not Path(pdbqt_file).is_file():raise FileNotFoundError(pdbqt_file)
    if not smiles.strip():raise ValueError("SMILES cannot be empty")
    return {"ready":True,"note":"Chemical graph and output SDF must still be validated after conversion."}

def convert_command(script, pdbqt_file, smiles, python_executable=None):
    validate_converter(script,pdbqt_file,smiles)
    return [python_executable or sys.executable, str(Path(script).resolve()),
            "--pdbqt_files",str(Path(pdbqt_file).resolve()), "--smile",smiles]
