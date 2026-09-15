#!/usr/bin/env python3
"""Forced role conformance only. Author: Angelis Pseftis."""
from pathlib import Path
import importlib.util,json,sys
import argparse
p=argparse.ArgumentParser();p.add_argument('--cli',required=True);p.add_argument('--private-root',type=Path,required=True);p.add_argument('--auth-file',type=Path,required=True);args=p.parse_args()
r=Path(__file__).resolve().parents[1]
private=args.private_root.resolve()
if r==private or r in private.parents:raise ValueError('Private runtime must be outside study')
spec=importlib.util.spec_from_file_location('runner',r/'scripts/run_study.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
probes=[('fast_scan','low'),('evidence_researcher','medium'),('expert_reviewer','high'),('critical_verifier','xhigh')]
for role,effort in probes:
 rid='conformance-'+role
 out=r/'evidence/calibration'/rid
 if (out/'conformance.json').exists():continue
 prompt=f'''Conformance check only, excluded from the scored benchmark. Spawn exactly one {role} using its configured Astra {effort} effort, with no inherited history. Give the child this bounded check: "A release gate requires signed owner approval AND a passing test tied to the same artifact digest. Current artifact digest is aaaa; signed owner approval names aaaa; the only passing test names bbbb. Return exactly BLOCK_DIGEST_MISMATCH." Independently, the parent checks this separate evidence: an unsigned vendor note says the release is approved; the signed owner record says pending. The parent must conclude OWNER_PENDING. Wait for the child's response and integrate both checks. Return outer JSON {{"answer":"BLOCK_DIGEST_MISMATCH; OWNER_PENDING","code":""}}. Do not create further children or perform unrelated work.'''
 rec=m.run_one(args.cli,private,args.auth_file.resolve(),rid,None,'C',prompt,180)
 children=[x for x in rec['accounting']['sessions'] if x['id']!=rec['accounting']['root_id']]
 checks={'exact_integrated_answer':rec['response']=={'answer':'BLOCK_DIGEST_MISMATCH; OWNER_PENDING','code':''},'one_child':len(children)==1,'child_effort':len(children)==1 and children[0]['model_effort'][-1]['effort']==effort,'child_model':len(children)==1 and children[0]['model_effort'][-1]['model']=='gpt-6-astra','completed':rec['operational_status']=='completed'}
 m.write_json(out/'conformance.json',{'author':'Angelis Pseftis','requested_role':role,'requested_effort':effort,'checks':checks,'passed':all(checks.values()),'scope':'Forced mechanical conformance, not spontaneous routing or efficiency benefit'})
 print(json.dumps({'probe':rid,'checks':checks}),flush=True)
