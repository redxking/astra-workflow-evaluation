"""End-to-end controller state tests with fake adapter. Author: Angelis Pseftis."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from controller.cli import execute,verify
class Tests(unittest.TestCase):
 def adapter(self,**kw):
  p=kw['private_run'];p.mkdir();return {'operational_status':'completed','requested_effort':kw['effort'],'response':{'answer':'ok','code':''},'usage':None}
 def call(self,r,**kw):
  return execute(cli='fake',workspace=r,prompt='task',features={},certificate=None,reference='medium',private_run=r/'run',auth_file=r/'auth',adapter=self.adapter,**kw)
 def test_no_verifier_is_unverified(self):
  with tempfile.TemporaryDirectory() as t:
   s=self.call(Path(t));self.assertEqual(s['status'],'unverified');self.assertEqual(len(s['attempts']),1)
 def test_explicit_verifier_receives_file(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);v=r/'verify.py';v.write_text('import json,sys\nassert json.load(open(sys.argv[1]))["answer"]=="ok"\n');s=self.call(r,verifier=[sys.executable,str(v)]);self.assertEqual(s['status'],'accepted_by_supplied_verifier')
 def test_failed_verifier_retained(self):
  with tempfile.TemporaryDirectory() as t:
   s=self.call(Path(t),verifier=[sys.executable,'-c','raise SystemExit(2)']);self.assertEqual(s['status'],'verification_failed');self.assertEqual(len(s['attempts']),1)
 def test_existing_run_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/'run').mkdir()
   with self.assertRaises(FileExistsError):self.call(r)
 def test_private_inside_git_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/'.git').mkdir()
   with self.assertRaises(ValueError):self.call(r)
 def test_bad_verifier_before_dispatch(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with self.assertRaises(ValueError):self.call(r,verifier='echo yes')
   self.assertFalse((r/'run').exists())
if __name__=='__main__':unittest.main()

class IntegrationTests(unittest.TestCase):
 def test_fallback_preserves_both_attempts_and_usage(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   def adapter(**kw):
    kw['private_run'].mkdir();return {'operational_status':'completed','response':{'answer':kw['effort'],'code':''},'usage':{'reconciled':{'input_tokens':10,'output_tokens':2,'total_tokens':12}}}
   with patch('controller.cli.choose',return_value=('low','test')):
    result=execute(cli='fake',workspace=root,prompt='x',features={},certificate=None,reference='medium',private_run=root/'run',auth_file=root/'auth',adapter=adapter,verifier=[sys.executable,'-c','import json,sys;sys.exit(json.load(open(sys.argv[1]))["answer"]!="medium")'])
   self.assertEqual(result['status'],'accepted_by_supplied_verifier');self.assertEqual(len(result['attempts']),2);self.assertEqual(result['usage_totals']['total_tokens'],24);self.assertIsNone(result['usage_totals']['cached_input_tokens'])
 def test_original_response_verified(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'response.json').write_text('{"answer":"original","code":""}')
   result=verify([sys.executable,'-c','import json,sys;assert json.load(open(sys.argv[1]))["answer"]=="original"'],{'answer':'redacted'},p,p,5)
   self.assertTrue(result['passed'])
 def test_adapter_exception_retained(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   def bad(**kw):raise ValueError('retained privately')
   r=execute(cli='fake',workspace=p,prompt='x',features={},certificate=None,reference='medium',private_run=p/'run',auth_file=p/'auth',adapter=bad)
   self.assertEqual(r['status'],'execution_failed');self.assertIsNone(r['usage_totals']['total_tokens']);self.assertTrue((p/'run/attempt-1/adapter-error.txt').is_file())
