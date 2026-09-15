"""Analysis boundary tests. Author: Angelis Pseftis."""
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('analysis',Path(__file__).resolve().parents[1]/'scripts/analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class BoundTests(unittest.TestCase):
 def test_zero_failures_not_zero_uncertainty(self):self.assertAlmostEqual(m.upper_bound(0,12),1-.05**(1/12),places=12)
 def test_more_tasks_tighten_bound(self):self.assertLess(m.upper_bound(0,59),.05)
 def test_all_failures(self):self.assertEqual(m.upper_bound(12,12),1.)
 def test_one_failure_increases_bound(self):self.assertGreater(m.upper_bound(1,12),m.upper_bound(0,12))
if __name__=='__main__':unittest.main()

class EndToEndTests(unittest.TestCase):
 def test_known_synthetic_aggregation(self):
  import tempfile,json,contextlib,io
  with tempfile.TemporaryDirectory() as tmp:
   old=m.ROOT;m.ROOT=Path(tmp)
   try:
    tasks=[f'E{i:02}' for i in range(1,13)];jobs=[]
    labels={t:{'review_opportunity':i%3!=2,'critical_checks':['fact']} for i,t in enumerate(tasks)}
    for t in tasks:
     for arm in 'ABC':
      for repeat in range(1,4):
       rid=f'{t}-{arm}-{repeat}';jobs.append({'run_id':rid,'task':t,'arm':arm,'repeat':repeat});out=m.ROOT/'results'/rid;out.mkdir(parents=True)
       sessions=[{'id':'root','usage':{'total_tokens':{'A':120,'B':100,'C':90}[arm]},'model_effort':[{'model':'gpt-6-astra','effort':'medium'}]}]
       if arm=='C' and labels[t]['review_opportunity']:sessions.append({'id':'child','usage':{'total_tokens':0},'model_effort':[{'model':'gpt-6-astra','effort':'high'}]})
       (out/'record.json').write_text(json.dumps({'accounting':{'sessions':sessions,'root_id':'root'},'setup_seconds':1,'elapsed_seconds':5}))
       (out/'score.json').write_text(json.dumps({'accepted':True,'checks':[{'name':'fact','passed':True}],'grading_seconds':0}))
    (m.ROOT/'protocol.json').write_text(json.dumps({'run_order':jobs,'routing_labels':labels,'domains':{str(i):tasks[i*3:i*3+3] for i in range(4)},'analysis_seed':123}))
    with contextlib.redirect_stdout(io.StringIO()):m.main()
    s=json.loads((m.ROOT/'results/summary.json').read_text());self.assertEqual(s['totals']['C']['tokens'],3240);self.assertEqual(s['routing_confusion_matrix'],{'TP':8,'FN':0,'FP':0,'TN':4});self.assertTrue(s['critical_failure_gate']);self.assertEqual(s['comparisons']['C_vs_A']['quality_noninferiority'],'inconclusive');self.assertGreater(s['comparisons']['C_vs_A']['regression_incidence_upper_95'],.22)
   finally:m.ROOT=old
