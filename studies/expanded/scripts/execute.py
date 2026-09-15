#!/usr/bin/env python3
"""Sequential frozen replication controller. Author: Angelis Pseftis."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_study import run_one,write_json
from evaluator import evaluate

def main():
 p=argparse.ArgumentParser();p.add_argument('--cli',required=True);p.add_argument('--private-root',type=Path,required=True);p.add_argument('--auth-file',type=Path,required=True);args=p.parse_args()
 private=args.private_root.resolve();auth=args.auth_file.resolve()
 if ROOT==private or ROOT in private.parents:raise ValueError('Private root must be outside study')
 private.mkdir(parents=True,exist_ok=True)
 lock=private/'controller.lock'
 try:
  fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
 except FileExistsError:raise RuntimeError('Controller lock exists; inspect PID before manual stale-lock removal')
 try:
  protocol=json.loads((ROOT/'protocol.json').read_text());done=[]
  for job in protocol['run_order']:
   for name,expected in protocol['files'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
   out=ROOT/'results'/job['run_id']
   if (out/'score.json').exists():done.append(job['run_id']);continue
   write_json(private/'checkpoint.json',{'state':'running','pid':os.getpid(),'completed':done,'current':job})
   saved=private/job['run_id']/'record.json'
   if saved.exists():rec=json.loads(saved.read_text())
   else:rec=run_one(args.cli,private,auth,job['run_id'],job['task'],job['arm'],timeout=protocol['timeout_seconds'])
   start=time.monotonic();score=evaluate(job['task'],rec['response']);score['grading_seconds']=time.monotonic()-start
   score['accepted']=score['passed'] and not score.get('errors') and rec['operational_status']=='completed' and rec['input_unchanged']
   write_json(out/'score.json',score);done.append(job['run_id'])
   print(json.dumps({'run':job['run_id'],'accepted':score['accepted'],'completed':len(done),'execution_seconds':round(rec['elapsed_seconds'],2)}),flush=True)
   limits=[e.get('rate_limits') for session in rec['accounting']['sessions'] for e in session.get('usage_events',[]) if e.get('rate_limits')]
   if limits and any(isinstance(limits[-1].get(w),dict) and limits[-1][w].get('used_percent',0)>=95 for w in ['primary','secondary']):
    write_json(private/'checkpoint.json',{'state':'waiting_allowance','completed':done,'reason':'preemptive allowance reserve; verify reset before resuming'});return
   if rec['exit_code']!=0:
    error=(private/job['run_id']/'stderr.log').read_text().lower()
    if any(x in error for x in ('usage limit','rate limit','quota','insufficient credits')):
     write_json(private/'checkpoint.json',{'state':'waiting_allowance','completed':done,'failed_attempt_retained':job['run_id']});return
  write_json(private/'checkpoint.json',{'state':'runs_complete','completed':done})
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()
