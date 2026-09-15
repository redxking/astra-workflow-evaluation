#!/usr/bin/env python3
"""Offline evidence reproduction; no model calls. Author: Angelis Pseftis."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluator import evaluate
from scripts.analyze import analyze

def main():
 protocol=json.loads((ROOT/'protocol.json').read_text())
 for name,wanted in protocol['files'].items():
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==wanted,name
 for p in sorted((ROOT/'results').glob('*/record.json')):
  d=json.loads(p.read_text());s=json.loads(p.with_name('score.json').read_text()); fresh=evaluate(d['task_id'],d['response'])
  for key in ('passed','checks_passed','checks_total','checks','errors'):assert fresh[key]==s[key],(p,key)
  assert d['input_hashes']==d['input_hashes_after']
  assert all(d['instruction_isolation']['checks'].values())
 analyze()
 print('PASS: frozen file hashes, 12 saved-response evaluations, input preservation, isolation checks and summary regeneration. Offline verification only.')
if __name__=='__main__':main()
