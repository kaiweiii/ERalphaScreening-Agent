
from pathlib import Path
import pandas as pd

from dockagent.core import summarize_pair


def batch_agvina1(log_directory, output_csv):
    log_directory = Path(log_directory)
    results = []

    agonist_logs = sorted(
        log_directory.glob("*_1qkua_noteq_*_log.txt")
    )

    for agonist_log in agonist_logs:
        ligand_prefix = agonist_log.name.split(
            "_1qkua_noteq_"
        )[0]

        run_suffix = agonist_log.name.split(
            "_1qkua_noteq_"
        )[1]

        antagonist_log = log_directory / (
            f"{ligand_prefix}_3uucb_noteq_{run_suffix}"
        )

        if not antagonist_log.exists():
            results.append({
                "ligand": ligand_prefix,
                "status": "missing_3uucb_log",
            })
            continue

        try:
            result = summarize_pair(
                agonist_log,
                antagonist_log
            )

            results.append({
                "ligand": ligand_prefix,
                "run": run_suffix,
                "score": result["score"],
                "threshold": result["threshold"],
                "classification": result["classification"],
                "energy_1qkua": result["receptors"]["1qkua"]["best_energy"],
                "energy_3uucb": result["receptors"]["3uucb"]["best_energy"],
                "status": "success",
            })

        except Exception as exc:
            results.append({
                "ligand": ligand_prefix,
                "run": run_suffix,
                "status": "failed",
                "error": str(exc),
            })

    df = pd.DataFrame(results)

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(
        parents=True, exist_ok=True
    )
    df.to_csv(output_csv, index=False)

    return df
