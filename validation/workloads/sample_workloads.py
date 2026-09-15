#!/usr/bin/env python3
"""Author: Angelis Pseftis. Metadata-only cluster split and stratified sampling."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ALLOWED = {'instance_id', 'repo', 'base_commit', 'source_ref', 'source_revision',
           'source_split', 'cluster_id', 'difficulty_stratum', 'metadata_eligible',
           'execution_eligible', 'eligibility_blockers', 'contamination_status'}

def rank(seed, namespace, value):
    return hashlib.sha256(f'{seed}\0{namespace}\0{value}'.encode()).hexdigest()

def sample(rows, seed=20260915, confirm_fraction=1/3, per_stratum=3):
    if not 0 < confirm_fraction < 1 or per_stratum < 1:
        raise ValueError('Require 0 < confirm_fraction < 1 and per_stratum >= 1')
    if not rows or len({r['instance_id'] for r in rows}) != len(rows):
        raise ValueError('Empty frame or duplicate instance IDs')
    for row in rows:
        if set(row) != ALLOWED or row['cluster_id'] != row['repo']:
            raise ValueError('Unexpected metadata schema or inconsistent repo cluster')
        if not isinstance(row['metadata_eligible'], bool):
            raise ValueError('Invalid metadata eligibility')
    eligible = [r for r in rows if r['metadata_eligible']]
    counts = Counter(r['repo'] for r in eligible)
    size_groups = defaultdict(list)
    for repo, n in counts.items():
        size_groups['small' if n <= 10 else 'medium' if n <= 50 else 'large'].append(repo)
    assignment = {}
    for size, repos in sorted(size_groups.items()):
        ordered = sorted(repos, key=lambda r: (rank(seed, 'repo:'+size, r), r))
        # For >=2 clusters, preserve both arms. Singletons go to tuning; do not split a repo.
        n_confirm = min(len(repos)-1, max(1, int(len(repos)*confirm_fraction + .5))) if len(repos)>1 else 0
        for i, repo in enumerate(ordered):
            assignment[repo] = {'arm': 'confirmatory' if i < n_confirm else 'train_tuning', 'size_stratum': size}
    buckets = defaultdict(list)
    for r in eligible:
        buckets[(r['repo'], r['difficulty_stratum'])].append(r)
    selected = set()
    for key, bucket in sorted(buckets.items()):
        ordered = sorted(bucket, key=lambda r: (rank(seed, 'instance', r['instance_id']), r['instance_id']))
        selected.update(r['instance_id'] for r in ordered[:per_stratum])
    output = []
    for r in sorted(eligible, key=lambda r:r['instance_id']):
        output.append({'instance_id':r['instance_id'], 'cluster_id':r['repo'],
                       **assignment[r['repo']], 'difficulty_stratum':r['difficulty_stratum'],
                       'selected':r['instance_id'] in selected})
    return {'design_version':1,'seed':seed,'confirm_fraction_target_clusters':confirm_fraction,
            'per_repo_difficulty_cap':per_stratum,'assignment_unit':'entire_repository',
            'status':'candidate_design_only_no_execution', 'assignments':output}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=Path(__file__).with_name('candidate-index.jsonl'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=20260915)
    p.add_argument('--confirm-fraction',type=float,default=1/3)
    p.add_argument('--per-stratum',type=int,default=3)
    a=p.parse_args()
    rows=[json.loads(line) for line in a.input.read_text().splitlines() if line.strip()]
    result=sample(rows,a.seed,a.confirm_fraction,a.per_stratum)
    result['input_sha256']=hashlib.sha256(a.input.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
