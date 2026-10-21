import argparse, json, asyncio
from dockagent.core import parse_vina_log, summarize_pair, read_ligand_csv
from dockagent.agent import ask
from dockagent.legacy_bridge import validate_score4_inputs, scoring4_command, run_checked_command, convert_command

def main():
    p=argparse.ArgumentParser(description='ERalpha-DockAgent staged prototype')
    sub=p.add_subparsers(dest='operation',required=True)
    a=sub.add_parser('read-log');a.add_argument('log')
    a=sub.add_parser('compare');a.add_argument('agonist_log');a.add_argument('antagonist_log')
    a=sub.add_parser('read-csv');a.add_argument('csv');a.add_argument('--id-column',default='CASRN');a.add_argument('--smiles-column',default='SMILES')
    a=sub.add_parser('agent');a.add_argument('question')
    a=sub.add_parser('score4-check');a.add_argument('--dock-root',required=True);a.add_argument('--results',required=True);a.add_argument('--group',required=True);a.add_argument('--proteins',required=True);a.add_argument('--ligands',required=True)
    a=sub.add_parser('score4-command');a.add_argument('--script',default='legacy/scoring4_linux.py');a.add_argument('--results',required=True);a.add_argument('--group',required=True);a.add_argument('--proteins',required=True);a.add_argument('--ligands',required=True)
    a=sub.add_parser('convert-command');a.add_argument('--script',default='legacy/pdbqt2sdf.py');a.add_argument('--pdbqt',required=True);a.add_argument('--smiles',required=True)
    args=p.parse_args()
    if args.operation=='read-log':out=parse_vina_log(args.log)
    elif args.operation=='compare':out=summarize_pair(args.agonist_log,args.antagonist_log)
    elif args.operation=='read-csv':out=read_ligand_csv(args.csv,args.id_column,args.smiles_column)
    elif args.operation=='score4-check':out=validate_score4_inputs(args.dock_root,args.results,args.group,args.proteins.split(','),args.ligands.split(','))
    elif args.operation=='score4-command':out=run_checked_command(scoring4_command(args.script,args.proteins.split(','),args.group,args.ligands.split(','),args.results))
    elif args.operation=='convert-command':out=run_checked_command(convert_command(args.script,args.pdbqt,args.smiles))
    else:out=asyncio.run(ask(args.question))
    print(json.dumps(out,indent=2) if not isinstance(out,str) else out)
if __name__=='__main__':main()
