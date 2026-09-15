# Author: Angelis Pseftis
# Synthetic benchmark; MIT.
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluator import evaluate

REFERENCE_CODE = '''import hashlib

def verify_snapshot(entries, blobs, per_file_limit, total_limit):
    if per_file_limit < 0 or total_limit < 0:
        raise ValueError('negative limit')
    seen = set()
    total = 0
    for entry in entries:
        path = entry['path']
        if not path or '\\\\' in path or '\\x00' in path or any(p in ('', '.', '..') for p in path.split('/')):
            raise ValueError('noncanonical path')
        if path in seen:
            raise ValueError('duplicate path')
        seen.add(path)
        if path not in blobs:
            raise ValueError('missing blob')
        data = blobs[path]
        size = len(data)
        if entry['size'] < 0 or entry['size'] != size:
            raise ValueError('size mismatch')
        digest = entry['sha256']
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest) or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('digest mismatch')
        total += size
        if size > per_file_limit or total > total_limit:
            raise ValueError('limit exceeded')
    return {'files': len(entries), 'total_bytes': total}
'''

REFERENCES = {
'T01': {'counts': {'PASS':3,'FAIL':0,'NOT_RUN':1,'UNKNOWN':1}, 'findings_observed':0,'overall_status':'INCOMPLETE','unknowns':['S03','S04']},
'T03': {'decisions':[
 {'id':'C01','is_issue':False,'lines':[7],'reason':'Exact host equality enforces the stated canonical host requirement.'},
 {'id':'C02','is_issue':True,'lines':[9,10],'reason':'Only existence is checked; authenticated=false sessions reach the protected write.'},
 {'id':'C03','is_issue':True,'lines':[17],'reason':'Prefix matching admits an attacker Origin with an appended suffix.'},
 {'id':'C04','is_issue':True,'lines':[19],'reason':'Any nonempty token passes without equality to session csrf_token.'},
 {'id':'C05','is_issue':False,'lines':[13,14],'reason':'GET returns only the public static document and makes no change.'}]},
'T04': {'as_of':'2026-08-12','current_state':'LAB_VERIFIED','current_source':'SRC-B','completed_gates':['G1','G2'],'unrun_gates':['G3','G4'],'unknowns':['U1','U2'],'superseded_sources':['SRC-A'],'production_ready':False},
}

def response(task, data=None):
    return {'answer':json.dumps(REFERENCES[task] if data is None else data),'code':''}

class EvaluatorTests(unittest.TestCase):
    def test_noncoding_references_pass(self):
        for task in REFERENCES:
            with self.subTest(task=task):
                result=evaluate(task,response(task))
                self.assertTrue(result['passed'],result)
                self.assertEqual(result['checks_passed'],result['checks_total'])
    def test_coding_reference_passes(self):
        result=evaluate('T02',{'answer':'Implementation','code':REFERENCE_CODE})
        self.assertTrue(result['passed'],result)
    def test_t01_false_clean_fails(self):
        bad=copy.deepcopy(REFERENCES['T01']);bad['overall_status']='PASSED'
        self.assertFalse(evaluate('T01',response('T01',bad))['passed'])
    def test_t01_missing_unknown_fails(self):
        bad=copy.deepcopy(REFERENCES['T01']);bad['unknowns']=[]
        self.assertFalse(evaluate('T01',response('T01',bad))['passed'])
    def test_t03_each_wrong_decision_fails(self):
        for i in range(5):
            bad=copy.deepcopy(REFERENCES['T03']);bad['decisions'][i]['is_issue']=not bad['decisions'][i]['is_issue']
            with self.subTest(candidate=i): self.assertFalse(evaluate('T03',response('T03',bad))['passed'])
    def test_t03_bad_reference_fails(self):
        bad=copy.deepcopy(REFERENCES['T03']);bad['decisions'][2]['lines']=[1]
        self.assertFalse(evaluate('T03',response('T03',bad))['passed'])
    def test_t04_vendor_claim_and_plan_do_not_prove_completion(self):
        for key,value in [('current_source','SRC-C'),('current_state','OPERATIONAL'),('completed_gates',['G1','G2','G3']),('production_ready',True),('unknowns',[])]:
            bad=copy.deepcopy(REFERENCES['T04']);bad[key]=value
            with self.subTest(key=key): self.assertFalse(evaluate('T04',response('T04',bad))['passed'])
    def test_coding_deliberate_defects(self):
        mutants={
          'size_unchecked':REFERENCE_CODE.replace("entry['size'] < 0 or entry['size'] != size",'False'),
          'hash_unchecked':REFERENCE_CODE.replace(" or hashlib.sha256(data).hexdigest() != digest",''),
          'aggregate_unchecked':REFERENCE_CODE.replace(' or total > total_limit',''),
          'perfile_unchecked':REFERENCE_CODE.replace('size > per_file_limit or ','') ,
          'duplicate_unchecked':REFERENCE_CODE.replace('if path in seen:', 'if False:'),
          'strict_limit':REFERENCE_CODE.replace('total > total_limit','total >= total_limit'),
          'path_unchecked':REFERENCE_CODE.replace("if not path or '\\\\' in path or '\\x00' in path or any(p in ('', '.', '..') for p in path.split('/')):", 'if False:'),
          'input_mutated':REFERENCE_CODE.replace("return {'files': len(entries), 'total_bytes': total}", "entries.clear()\n    return {'files': len(seen), 'total_bytes': total}"),
        }
        for name,code in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(code,REFERENCE_CODE)
                result=evaluate('T02',{'answer':'Deliberately defective','code':code})
                self.assertFalse(result['errors'],result)
                self.assertFalse(result['passed'],result)
    def test_prohibited_source_even_with_correct_output_fails(self):
        for prefix in ['import os\n', 'unused = eval\n', 'unused = (1).__class__\n']:
            result=evaluate('T02',{'answer':'Correct behavior, prohibited source','code':prefix+REFERENCE_CODE})
            self.assertFalse(result['passed'],result)
            self.assertFalse(result['errors'],result)
            self.assertTrue(any(c['name']=='code_contract' and not c['passed'] for c in result['checks']))
    def test_malformed_responses_fail_without_exception(self):
        for task in ['T01','T02','T03','T04']:
            for data in [None,{}, {'answer':{},'code':''},{'answer':'null','code':''},{'answer':'{}','code':''}]:
                with self.subTest(task=task,data=data):self.assertFalse(evaluate(task,data)['passed'])
    def test_boolean_is_not_count(self):
        bad=copy.deepcopy(REFERENCES['T01']);bad['counts']['FAIL']=False
        self.assertFalse(evaluate('T01',response('T01',bad))['passed'])

if __name__=='__main__': unittest.main()
