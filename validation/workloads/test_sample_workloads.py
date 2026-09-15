"""Author: Angelis Pseftis. Offline verification of sampling invariants."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from sample_workloads import sample, ALLOWED

ROOT=Path(__file__).parent
class SamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[json.loads(x) for x in (ROOT/'candidate-index.jsonl').read_text().splitlines()]
    def test_frame_identity_and_patch_exclusion(self):
        self.assertEqual(len(self.rows),500)
        self.assertEqual(len({r['instance_id'] for r in self.rows}),500)
        self.assertEqual(len({r['repo'] for r in self.rows}),12)
        for row in self.rows:
            self.assertEqual(set(row),ALLOWED)
            self.assertRegex(row['base_commit'],r'^[0-9a-f]{40}$')
            self.assertFalse(row['execution_eligible'])
        p=json.loads((ROOT/'provenance.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT/'candidate-index.jsonl').read_bytes()).hexdigest(),p['index_sha256'])
    def test_determinism_input_order_and_seed_effect(self):
        a=sample(self.rows)
        self.assertEqual(a,sample(list(reversed(self.rows))))
        self.assertNotEqual(a['assignments'],sample(self.rows,seed=12)['assignments'])
    def test_no_repo_leakage_and_both_arms_per_size_stratum(self):
        repos={};sizes={}
        for row in sample(self.rows)['assignments']:
            repos.setdefault(row['cluster_id'],set()).add(row['arm'])
            sizes.setdefault(row['size_stratum'],set()).add(row['arm'])
        self.assertTrue(all(len(arms)==1 for arms in repos.values()))
        self.assertTrue(all(arms=={'train_tuning','confirmatory'} for arms in sizes.values()))
    def test_cap_and_coverage(self):
        groups={}
        for r in sample(self.rows)['assignments']:
            groups.setdefault((r['cluster_id'],r['difficulty_stratum']),[]).append(r)
        for rows in groups.values():
            self.assertEqual(sum(r['selected'] for r in rows),min(3,len(rows)))
    def test_saved_plan_matches_algorithm(self):
        expected=sample(self.rows)
        expected['input_sha256']=hashlib.sha256((ROOT/'candidate-index.jsonl').read_bytes()).hexdigest()
        self.assertEqual(expected,json.loads((ROOT/'sample-plan.json').read_text()))
    def test_reject_duplicate_and_sensitive_extra_column(self):
        with self.assertRaises(ValueError): sample(self.rows+[self.rows[0]])
        rows=copy.deepcopy(self.rows);rows[0]['patch']='forbidden'
        with self.assertRaises(ValueError): sample(rows)
        for f,n in [(0,3),(1,3),(.3,0)]:
            with self.assertRaises(ValueError):sample(self.rows,confirm_fraction=f,per_stratum=n)
    def test_ineligible_and_singleton(self):
        rows=copy.deepcopy(self.rows[:1]);rows[0]['metadata_eligible']=False
        self.assertEqual(sample(rows)['assignments'],[])
        rows[0]['metadata_eligible']=True
        self.assertEqual(sample(rows)['assignments'][0]['arm'],'train_tuning')
if __name__=='__main__':unittest.main()
