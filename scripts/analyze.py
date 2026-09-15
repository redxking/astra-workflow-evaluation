#!/usr/bin/env python3
"""Recompute descriptive pilot results. Author: Angelis Pseftis."""
import csv
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def analyze():
    rows=[]
    for p in sorted((ROOT/'results').glob('*/record.json')):
        d=json.loads(p.read_text()); s=json.loads(p.with_name('score.json').read_text())
        sessions=d['accounting']['sessions']
        if not sessions or any(x['usage'] is None for x in sessions):
            raise ValueError('Incomplete usage: '+d['run_id'])
        row={k:d[k] for k in ('run_id','task_id','arm')}
        row.update(accepted=s['accepted'],checks_passed=s['checks_passed'],checks_total=s['checks_total'],sessions=len(sessions),setup_seconds=d['setup_seconds'],execution_seconds=d['elapsed_seconds'],grading_seconds=s['grading_seconds'])
        row['total_seconds']=row['setup_seconds']+row['execution_seconds']+row['grading_seconds']
        for key in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens'):
            row[key]=sum(x['usage'][key] for x in sessions)
        rows.append(row)
    assert len(rows)==12
    totals={}
    for arm in 'ABC':
        group=[r for r in rows if r['arm']==arm]
        totals[arm]={k:sum(r[k] for r in group) for k in ('accepted','checks_passed','checks_total','sessions','setup_seconds','execution_seconds','grading_seconds','total_seconds','input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')}
    summary={'author':'Angelis Pseftis','design':'4 paired tasks, one observation per condition; descriptive only','runs':rows,'totals':totals,'C_vs_A':{'token_reduction_percent':100*(1-totals['C']['total_tokens']/totals['A']['total_tokens']),'elapsed_reduction_percent':100*(1-totals['C']['total_seconds']/totals['A']['total_seconds'])},'C_vs_B':{'token_reduction_percent':100*(1-totals['C']['total_tokens']/totals['B']['total_tokens']),'elapsed_reduction_percent':100*(1-totals['C']['total_seconds']/totals['B']['total_seconds'])}}
    (ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (ROOT/'results/summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return summary
if __name__=='__main__':
    print(json.dumps(analyze()['totals'],indent=2))
