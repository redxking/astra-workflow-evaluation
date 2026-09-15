#!/usr/bin/env python3
"""Task-cluster descriptive analysis. Author: Angelis Pseftis."""
import json,random,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def upper_bound(k,n,alpha=.05):
 if k==n:return 1.
 lo,hi=0.,1.
 for _ in range(80):
  p=(lo+hi)/2
  cdf=sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k+1))
  if cdf>alpha:lo=p
  else:hi=p
 return (lo+hi)/2

def main():
 protocol=json.loads((ROOT/'protocol.json').read_text());rows=[]
 for job in protocol['run_order']:
  out=ROOT/'results'/job['run_id'];d=json.loads((out/'record.json').read_text());s=json.loads((out/'score.json').read_text())
  sessions=d['accounting']['sessions'];complete=bool(sessions) and all(x['usage'] is not None for x in sessions)
  ids=[x['id'] for x in sessions];assert len(set(ids))==len(ids)
  children=[x for x in sessions if x['id']!=d['accounting']['root_id']]
  high=any(x['model_effort'] and x['model_effort'][-1]['model']=='gpt-6-astra' and x['model_effort'][-1]['effort'] in ['high','xhigh'] for x in children)
  rows.append({**job,'accepted':bool(s['accepted']),'tokens':sum(x['usage']['total_tokens'] for x in sessions) if complete else None,'seconds':d['setup_seconds']+d['elapsed_seconds']+s['grading_seconds'],'children':len(children),'verified_high_child':high,'check_results':{c['name']:c['passed'] for c in s['checks']}})
 tasks=sorted(set(x['task'] for x in rows));groups={a:{t:[x for x in rows if x['arm']==a and x['task']==t] for t in tasks} for a in 'ABC'}
 totals={a:{'accepted':sum(x['accepted'] for t in tasks for x in groups[a][t]),'tokens':sum(x['tokens'] for t in tasks for x in groups[a][t]) if all(x['tokens'] is not None for t in tasks for x in groups[a][t]) else None,'seconds':sum(x['seconds'] for t in tasks for x in groups[a][t])} for a in 'ABC'}
 comparisons={};rng=random.Random(protocol['analysis_seed'])
 for comparator in 'AB':
  diffs=[(sum(x['accepted'] for x in groups['C'][t])-sum(x['accepted'] for x in groups[comparator][t]))/3 for t in tasks]
  reg=sum(x<0 for x in diffs)
  item={'task_balanced_acceptance_difference':sum(diffs)/len(tasks),'regression_tasks':reg,'regression_incidence_upper_95':upper_bound(reg,len(tasks)),'quality_noninferiority':'inconclusive','note':'Incidence bound is not a CI for acceptance difference; purposive synthetic tasks preclude population inference.'}
  for metric in ['tokens','seconds']:
   if any(x[metric] is None for x in rows):item[metric]={'status':'unknown'};continue
   samples=[]
   domains=protocol['domains']
   for _ in range(20000):
    selected=[rng.choice(ts) for ts in domains.values() for __ in ts]
    c=sum(x[metric] for t in selected for x in groups['C'][t]);b=sum(x[metric] for t in selected for x in groups[comparator][t]);samples.append(c/b)
   samples.sort();item[metric]={'ratio_C_to_comparator':totals['C'][metric]/totals[comparator][metric],'descriptive_cluster_interval_95':[samples[500],samples[19499]],'population_inference':False}
  comparisons['C_vs_'+comparator]=item
 labels=protocol['routing_labels'];matrix={'TP':0,'FN':0,'FP':0,'TN':0};routing=[]
 for t in tasks:
  count=sum(x['verified_high_child'] for x in groups['C'][t]);pred=count>=2;expected=labels[t]['review_opportunity'];matrix[('T' if pred==expected else 'F')+('P' if pred else 'N')]+=1
  routing.append({'task':t,'expected_opportunity':expected,'verified_high_child_runs':count,'task_positive':pred})
 critical_failures=[{'run_id':x['run_id'],'check':name} for x in rows if x['arm']=='C' for name in labels[x['task']]['critical_checks'] if not x['check_results'].get(name,False)]
 indispensable_regressions=[{'task':t,'check':name} for t in tasks for name in labels[t]['critical_checks'] if all(x['check_results'].get(name,False) for x in groups['A'][t]) and any(not x['check_results'].get(name,False) for x in groups['C'][t])]
 result={'author':'Angelis Pseftis','runs':rows,'totals':totals,'comparisons':comparisons,'routing_confusion_matrix':matrix,'routing':routing,'routing_invocation_gate':matrix['TP']>=6 and matrix['FP']<=1,'routing_integration':'Requires retained child/parent evidence review; invocation alone is insufficient','observed_acceptance_gate':totals['C']['accepted']>=33 and all(sum(x['accepted'] for x in groups['C'][t])>=sum(x['accepted'] for x in groups['A'][t]) for t in tasks),'critical_failure_gate':not critical_failures,'critical_failures':critical_failures,'indispensable_regressions':indispensable_regressions}
 (ROOT/'results/summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(totals,indent=2))
if __name__=='__main__':main()
