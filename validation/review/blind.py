#!/usr/bin/env python3
"""Create an arm-blinded review bundle. Author: Angelis Pseftis."""
import argparse,hashlib,json,random
from pathlib import Path

def build(study,out,key_out,seed):
 study=Path(study).resolve();out=Path(out).resolve();key_out=Path(key_out).resolve()
 if out.exists() or key_out.exists():raise ValueError('New destinations required; never overwrite reviews or keys')
 if out==key_out or out in key_out.parents:raise ValueError('Unblinding key must remain outside review bundle')
 if any((p/'.git').exists() for p in key_out.parents):raise ValueError('Unblinding key must be outside every Git checkout')
 protocol=json.loads((study/'protocol.json').read_text());jobs=list(protocol['run_order'])
 for job in jobs:
  if not (study/'results'/job['run_id']/'score.json').is_file():raise ValueError('Study incomplete; no selective review export')
 random.Random(seed).shuffle(jobs);items=[];key=[]
 # Validate all records before creating any outputs.
 for i,job in enumerate(jobs):
  record=json.loads((study/'results'/job['run_id']/'record.json').read_text());blind_id=f'item-{i+1:04}'
  response=record.get('response');encoded=json.dumps(response,ensure_ascii=False,sort_keys=True).encode()
  if len(encoded)>10_000_000:raise ValueError('Response too large')
  items.append({'blind_id':blind_id,'task_id':job['task'],'response':response,'response_sha256':hashlib.sha256(encoded).hexdigest()})
  key.append({'blind_id':blind_id,'run_id':job['run_id'],'arm':job['arm'],'repeat':job.get('repeat')})
 out.mkdir(parents=True);key_out.parent.mkdir(parents=True,exist_ok=True)
 for item in items:(out/(item['blind_id']+'.json')).write_text(json.dumps(item,indent=2,ensure_ascii=False)+'\n')
 (out/'review-sheet.json').write_text(json.dumps({'reviewer_id':None,'independence_declaration':None,'review_started_at':None,'ratings':[{'blind_id':x['blind_id'],'correctness':None,'evidence_traceability':None,'edge_case_coverage':None,'completeness':None,'critical_error':None,'decision':None,'evidence_notes':None} for x in items]},indent=2)+'\n')
 key_out.write_text(json.dumps({'author':'Angelis Pseftis','seed':seed,'mapping':key},indent=2)+'\n');key_out.chmod(0o600)
 return {'items':len(items),'status':'prepared_unreviewed','blinding_limit':'Arm metadata withheld; output content/public prior publication may reveal identity. No human review or independence established.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--study',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key-out',type=Path,required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args();print(json.dumps(build(a.study,a.out,a.key_out,a.seed)))
if __name__=='__main__':main()
