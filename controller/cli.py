#!/usr/bin/env python3
"""Explicit task-boundary launcher. Author: Angelis Pseftis."""
import argparse,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
EFFORTS=('low','medium','high','xhigh','max','ultra')

def read(path):return json.loads(Path(path).read_text())
def write(path,data):Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

def choose(certificate,features,reference,allow_demo=False):
 if not certificate:return reference,'reference_no_certificate'
 from controller.calibration import select_effort
 if certificate.get('reference_effort')!=reference:return reference,'reference_certificate_mismatch'
 if certificate.get('data_kind')=='synthetic_demo' and not allow_demo:return reference,'reference_demo_certificate_disabled'
 effort=select_effort(certificate,features,fallback_effort=reference)
 return (effort if effort in EFFORTS else reference),'calibrated_selector_or_reference_fallback'

def verify(command,response,folder,workspace,timeout):
 path=folder/'candidate-response.json'
 original=folder/'response.json'
 write(path,read(original) if original.is_file() else response)
 if command is None:return {'status':'not_configured','passed':None,'seconds':0}
 if not isinstance(command,list) or not command or not all(isinstance(x,str) and x for x in command):raise ValueError('Verifier must be a nonempty JSON argv array; never model-generated')
 start=time.monotonic()
 with (folder/'verifier.stdout').open('wb') as stdout,(folder/'verifier.stderr').open('wb') as stderr:
  try:
   p=subprocess.Popen(command+[str(path)],cwd=workspace,stdout=stdout,stderr=stderr,start_new_session=True)
   try:p.wait(timeout=timeout)
   except subprocess.TimeoutExpired:
    os.killpg(p.pid,signal.SIGKILL);p.wait();raise
   return {'status':'completed','passed':p.returncode==0,'exit_code':p.returncode,'seconds':time.monotonic()-start}
  except OSError:return {'status':'launch_failed','passed':False,'exit_code':None,'seconds':time.monotonic()-start}
  except subprocess.TimeoutExpired:return {'status':'timed_out','passed':False,'exit_code':None,'seconds':time.monotonic()-start}

def execute(*,cli,workspace,prompt,features,certificate,reference,private_run,auth_file,verifier=None,timeout=300,allow_demo=False,adapter=None):
 if adapter is None:
  from controller.runtime import run_task
  adapter=run_task
 private_run=Path(private_run).resolve();workspace=Path(workspace).resolve()
 if private_run.exists():raise FileExistsError('New private run directory required')
 if any((p/'.git').exists() for p in [private_run,*private_run.parents]):raise ValueError('Private run must remain outside Git checkouts')
 if type(timeout) is not int or timeout<=0:raise ValueError('Positive integer timeout required')
 if reference not in EFFORTS:raise ValueError('Unsupported reference effort')
 # Validate explicit verifier before dispatch, not after spending model tokens.
 if verifier is not None and (not isinstance(verifier,list) or not verifier or not all(isinstance(x,str) and x for x in verifier)):raise ValueError('Invalid verifier argv')
 effort,reason=choose(certificate,features,reference,allow_demo);private_run.mkdir(parents=True,mode=0o700)
 started=time.monotonic();attempts=[]
 for index,selected in enumerate([effort]+([reference] if effort!=reference and verifier is not None else [])):
  folder=private_run/f'attempt-{index+1}'
  try:
   result=adapter(cli=str(cli),workspace=workspace,prompt=prompt,effort=selected,private_run=folder,auth_file=Path(auth_file),timeout=timeout)
  except Exception as error:
   folder.mkdir(parents=True,exist_ok=True,mode=0o700)
   (folder/'adapter-error.txt').write_text(type(error).__name__+': '+str(error))
   result={'operational_status':'failed','requested_effort':selected,'response':None,'usage':None,'failure_reasons':['adapter_exception:'+type(error).__name__]}
  folder.mkdir(parents=True,exist_ok=True)
  check=verify(verifier,result.get('response'),folder,workspace,timeout) if result.get('operational_status')=='completed' else {'status':'not_run_execution_failed','passed':None,'seconds':0}
  attempts.append({'execution':result,'verification':check})
  if result.get('operational_status')!='completed' or check['passed'] is not False:break
 last=attempts[-1]
 if last['execution'].get('operational_status')!='completed':status='execution_failed'
 elif last['verification']['passed'] is True:status='accepted_by_supplied_verifier'
 elif last['verification']['passed'] is False:status='verification_failed'
 else:status='unverified'
 usage_rows=[(a['execution'].get('usage') or {}).get('reconciled') for a in attempts]
 usage_totals={k:sum(u[k] for u in usage_rows) if all(isinstance(u,dict) and type(u.get(k)) is int for u in usage_rows) else None for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')}
 summary={'usage_totals':usage_totals,'author':'Angelis Pseftis','controller_version':1,'selection_reason':reason,'reference_effort':reference,'initial_effort':effort,'status':status,'attempts':attempts,'total_wall_seconds':time.monotonic()-started,'acceptance_scope':'Supplied verifier only; not independent validation or general correctness','calibration_scope':'Certificate applies to its frozen policy/data/loss assumptions. End-to-end fallback workflow still requires separate calibration.','response':last['execution'].get('response')}
 write(private_run/'controller-result.json',summary);return summary

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
 fit=sub.add_parser('calibrate');fit.add_argument('--training',required=True);fit.add_argument('--calibration',required=True);fit.add_argument('--output',required=True);fit.add_argument('--reference',choices=EFFORTS,default='medium');fit.add_argument('--candidate',choices=EFFORTS,default='low');fit.add_argument('--alpha',type=float,default=.05);fit.add_argument('--delta',type=float,default=.05);fit.add_argument('--data-kind',default='unspecified')
 run=sub.add_parser('run');run.add_argument('--cli',required=True);run.add_argument('--workspace',type=Path,required=True);run.add_argument('--prompt-file',type=Path,required=True);run.add_argument('--features',type=Path,required=True);run.add_argument('--certificate',type=Path);run.add_argument('--reference',choices=EFFORTS,default='medium');run.add_argument('--private-run',type=Path,required=True);run.add_argument('--auth-file',type=Path,required=True);run.add_argument('--verifier-argv',help='Trusted JSON argv; response-file path appended');run.add_argument('--timeout',type=int,default=300);run.add_argument('--allow-demonstration',action='store_true')
 a=p.parse_args()
 if a.action=='calibrate':
  from controller.calibration import fit_and_calibrate
  out=Path(a.output)
  if out.exists():raise FileExistsError('Never overwrite a calibration certificate')
  c=fit_and_calibrate(read(a.training),read(a.calibration),reference_effort=a.reference,candidate_effort=a.candidate,alpha=a.alpha,delta=a.delta,source_data_kind=a.data_kind);write(out,c);print(json.dumps({'status':'certificate_prepared','output':str(out),'scope':'Conditional statistical evidence only; sampling and labels require external assurance'}))
 else:
  result=execute(cli=a.cli,workspace=a.workspace,prompt=a.prompt_file.read_text(),features=read(a.features),certificate=read(a.certificate) if a.certificate else None,reference=a.reference,private_run=a.private_run,auth_file=a.auth_file,verifier=json.loads(a.verifier_argv) if a.verifier_argv else None,timeout=a.timeout,allow_demo=a.allow_demonstration)
  print(json.dumps({'status':result['status'],'initial_effort':result['initial_effort'],'attempts':len(result['attempts']),'total_wall_seconds':result['total_wall_seconds']}))
  return 0 if result['status']=='accepted_by_supplied_verifier' else 2 if result['status']=='unverified' else 1
if __name__=='__main__':sys.exit(main())
