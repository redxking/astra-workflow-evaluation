"""Review export tests. Author: Angelis Pseftis."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('blind',Path(__file__).with_name('blind.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def fixture(self,root):
  s=root/'study';s.mkdir();jobs=[]
  for arm in 'ABC':
   jobs.append({'run_id':arm,'arm':arm,'task':'T01'});p=s/'results'/arm;p.mkdir(parents=True);(p/'record.json').write_text(json.dumps({'response':{'answer':'same','code':''},'secret_config':'DO_NOT_EXPORT'}));(p/'score.json').write_text('{}')
  (s/'protocol.json').write_text(json.dumps({'run_order':jobs}));return s
 def test_all_outputs_no_arm_metadata(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=self.fixture(r);out=r/'review';key=r/'private/key.json';result=m.build(s,out,key,1);self.assertEqual(result['items'],3);self.assertEqual(len(json.loads(key.read_text())['mapping']),3);self.assertNotIn('DO_NOT_EXPORT',''.join(p.read_text() for p in out.glob('*.json')));self.assertNotIn('"arm"',''.join(p.read_text() for p in out.glob('*.json')))
 def test_incomplete_refused(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=self.fixture(r);(s/'results/A/score.json').unlink()
   with self.assertRaises(ValueError):m.build(s,r/'review',r/'key.json',1)
   self.assertFalse((r/'review').exists())
 def test_key_in_git_refused(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=self.fixture(r);(s/'.git').mkdir()
   with self.assertRaises(ValueError):m.build(s,r/'review',s/'key.json',1)
if __name__=='__main__':unittest.main()
