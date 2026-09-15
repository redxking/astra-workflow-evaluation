"""Planning calculation checks. Author: Angelis Pseftis."""
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('precision',Path(__file__).with_name('precision.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_more_discordance_requires_more_tasks(self):self.assertGreater(m.plan(.2)['approx_independent_task_pairs'],m.plan(.1)['approx_independent_task_pairs'])
 def test_tighter_margin_requires_more_tasks(self):self.assertGreater(m.plan(.1,.025)['approx_independent_task_pairs'],m.plan(.1,.05)['approx_independent_task_pairs'])
 def test_cluster_inflation(self):self.assertGreater(m.plan(.1,cluster_size=5,rho=.1)['approx_tasks_with_design_effect'],m.plan(.1)['approx_independent_task_pairs'])
 def test_zero_and_bad_inputs_rejected(self):
  for q in [0,-.1,1.1]:
   with self.assertRaises(ValueError):m.plan(q)
if __name__=='__main__':unittest.main()
