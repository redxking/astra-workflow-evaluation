# Author: Angelis Pseftis
# SPDX-License-Identifier: MIT
"""Reference, semantic-mutant, boundary and independently formulated oracle checks."""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('expanded_fixture_evaluator',BASE/'evaluator.py')
e=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(e)

# Manually reviewed contract outcomes; numeric optimality is also cross-checked
# below using formulations distinct from the production oracle.
EXPECTED={
'E01':dict(authorized_probes=['p1','p8'],reachable_probes=['p1','p2','p3','p4','p5','p7','p8'],repair_cost=5,repair_edges=['e03','e09']),
'E02':dict(feasible_placements=[['n1','n2','n3'],['n1','n3','n5'],['n1','n3','n7'],['n1','n5','n7'],['n3','n4','n5'],['n3','n4','n7'],['n3','n5','n7'],['n4','n5','n7'],['n5','n6','n7']],selected=['n3','n4','n5'],selected_cost=11,selected_min_surviving_weight=3),
'E03':dict(decisions=[dict(id=i,decision=d,rule=r) for i,d,r in [('q1','deny','r3'),('q2','allow','r2'),('q3','deny','EXPIRED'),('q4','allow','r1'),('q5','deny',None),('q6','allow','r6')]]),
'E04':dict(gates=[dict(id=i,status=s,source=r) for i,s,r in [('g1','PASS','a'),('g2','FAIL','d'),('g3','UNKNOWN','h'),('g4','UNKNOWN','l'),('g5','PASS','j'),('g6','UNKNOWN',None)]],decision='BLOCKED',blocked_dependencies=['g3','g5'],observed_findings=1,unknown_finding_gates=['g4','g6']),
'E05':dict(services=[dict(id=i,confirmed_minutes=c,possible_minutes=p,unobserved_confirmed_minutes=u) for i,c,p,u in [('api',18,30,2),('db',30,45,10),('queue',10,11,5)]],fleet_confirmed_minutes=55,retained_report_ids=['r01','r03','r04','r06','r07','r09','r12','r13']),
'E06':dict(claims=[dict(id=i,status=s,supporting=a,contradicting=b) for i,s,a,b in [('c1','SUPPORTED',['s1'],[]),('c2','CONFLICTED',['s1'],['s2']),('c3','UNKNOWN',[],[]),('c4','CONTRADICTED',[],['s7'])]]),
'E07':dict(jobs=[dict(id=i,state=s,attempt=a,lease_until=None) for i,s,a in [('a','DONE',2),('b','DONE',1),('c','CANCELLED',2),('d','PENDING',1)]],accepted_sequences=[1,2,5,6,8,11,14,15,17],rejected_sequences=[3,4,7,9,10,12,13,16,18,19],accepted_tokens=['x','y']),
'E08':dict(selected_edges=['b','f','j','k'],departures=[0,2,4,7],arrival=9,energy_consumed=14,feasible_path_count=8),
'E09':dict(cycle_components=[['b','c'],['f']],blocked=['a','b','c','d','e','f'],build_order=['h','g','j','i','k']),
'E10':dict(starts=dict(a=0,b=0,c=2,d=3,e=5,f=6),makespan=8,risk_exposure=72),
'E11':dict(actions=['a','b','c','e','g'],cost=12,scenario_losses=dict(data=10,identity=25,site=30),worst_loss=30,weighted_loss=145,feasible_portfolios=43),
'E12':dict(feasible_starts=[10,11,12,13],earliest=10,latest=13),
}

# Two task-specific realistic failure mutants each; no arm-specific assumptions.
MUTATIONS={
'E01': [('expired_token_allowed',lambda a:a['authorized_probes'].append('p2')),('break_required_ops_path',lambda a:a.update(repair_edges=['e03','e07','e09'],repair_cost=13))],
'E02': [('ignore_correlated_site_failure',lambda a:a['feasible_placements'].append(['n1','n3','n4'])),('choose_higher_cost_feasible',lambda a:a.update(selected=['n1','n2','n3'],selected_cost=13))],
'E03': [('allow_wins_priority_tie',lambda a:a['decisions'][0].update(decision='allow',rule='r4')),('expiry_inclusive',lambda a:a['decisions'][2].update(decision='allow',rule='r6'))],
'E04': [('record_time_over_observation_time',lambda a:a['gates'][0].update(status='FAIL',source='b')),('stale_pass_counts_as_pass',lambda a:a['gates'][2].update(status='PASS'))],
'E05': [('sum_service_outages',lambda a:a.update(fleet_confirmed_minutes=58)),('future_correction_applied',lambda a:a['services'][1].update(confirmed_minutes=20))],
'E06': [('conflict_hidden',lambda a:a['claims'][1].update(status='SUPPORTED',contradicting=[])),('future_evidence_accepted',lambda a:a['claims'][2].update(status='SUPPORTED',supporting=['s3']))],
'E07': [('lease_equality_not_expired',lambda a:a['jobs'][3].update(state='RUNNING',lease_until=40)),('rejected_result_consumes_token',lambda a:a.update(accepted_tokens=['y']))],
'E08': [('battery_ignored_shortcut',lambda a:a.update(selected_edges=['b','f','i'],departures=[0,2,4],arrival=7,energy_consumed=9)),('count_timings_instead_of_paths',lambda a:a.update(feasible_path_count=9))],
'E09': [('self_cycle_ignored',lambda a:a.update(cycle_components=[['b','c']])),('lexical_sort_not_ready_order',lambda a:a.update(build_order=['g','h','i','j','k']))],
'E10': [('capacity_overbooked',lambda a:a['starts'].update(d=2)),('risk_uses_finish',lambda a:a.update(risk_exposure=123))],
'E11': [('scenario_bonus_ignored',lambda a:a['scenario_losses'].update(site=40)),('empty_portfolio_not_counted',lambda a:a.update(feasible_portfolios=42))],
'E12': [('blackout_overlap',lambda a:a['feasible_starts'].insert(0,7)),('adjacency_treated_as_gap',lambda a:a.update(feasible_starts=[10,11],latest=11))],
}


def data(tid):return json.loads((BASE/'fixtures'/tid/'input.json').read_text())
def response(a):return dict(answer=json.dumps(a),code='')


class Fixtures(unittest.TestCase):
    def test_catalog_metadata_and_no_oracle_in_task_inputs(self):
        self.assertEqual(len(e.ROUTING_METADATA),12)
        self.assertEqual(sum(x['review_opportunity'] for x in e.ROUTING_METADATA.values()),8)
        domains={}
        for tid in EXPECTED:
            d=json.loads((BASE/'fixtures'/tid/'task.json').read_text())
            self.assertEqual(d['author'],'Angelis Pseftis');self.assertEqual(d['license'],'MIT');self.assertTrue(d['synthetic'])
            domains[d['kind']]=domains.get(d['kind'],0)+1
            text=d['prompt'].lower()
            for term in ('review_opportunity','specialist','subagent','delegat','independent analyses','routing_metadata','reference_answer'):
                self.assertNotIn(term,text)
            self.assertEqual(set(p.name for p in (BASE/'fixtures'/tid).iterdir()),{'task.json','input.json'})
            self.assertTrue(set(e.ROUTING_METADATA[tid]['critical_checks'])<=set(EXPECTED[tid]))
        self.assertEqual(sorted(domains.values()),[3,3,3,3])

    def test_strict_schema_and_json(self):
        for bad in (None,{},dict(answer='{}'),dict(answer={},code=''),dict(answer='{}',code='',extra=1)):
            self.assertFalse(e.evaluate('E01',bad)['passed'])
        for text in ('[]','{"x":1,"x":2}','{"x":NaN}','{'*10000):
            self.assertFalse(e.evaluate('E01',dict(answer=text,code=''))['passed'])
        self.assertFalse(e.evaluate('missing',response({}))['passed'])
        r=e.reference_response('E01');r['code']='print(1)';self.assertFalse(e.evaluate('E01',r)['passed'])
        a=copy.deepcopy(EXPECTED['E04']);a['observed_findings']=True
        self.assertFalse(e.evaluate('E04',response(a))['passed'])

    def test_e01_independent_floyd_cut_search(self):
        d=data('E01');vertices=sorted({e[k] for e in d['edges'] for k in ('source','target')});rem=[x for x in d['edges'] if x['removable']];candidates=[]
        for mask in range(1<<len(rem)):
            cut={rem[i]['id'] for i in range(len(rem)) if mask>>i&1}
            matrix={(a,b):a==b for a in vertices for b in vertices}
            for edge in d['edges']:
                if edge['id'] not in cut:matrix[edge['source'],edge['target']]=True
            for k in vertices:
                for a in vertices:
                    for b in vertices:matrix[a,b] |= matrix[a,k] and matrix[k,b]
            if any(matrix[a,b] for a,b in d['forbidden']) or not all(matrix[a,b] for a,b in d['required']):continue
            candidates.append((sum(x['cost'] for x in rem if x['id'] in cut),len(cut),sorted(cut)))
        self.assertEqual(min(candidates),(5,2,['e03','e09']))

    def test_e02_independent_failure_masks(self):
        d=data('E02');nodes=d['nodes'];n=len(nodes);lat={frozenset((x['a'],x['b'])):x['ms'] for x in d['latencies']};feasible=[]
        failure_masks=[sum(1<<i for i,x in enumerate(nodes) if x['site'] in s['sites'] or x['provider'] in s['providers']) for s in d['failures']]
        for mask in range(1<<n):
            chosen=[x for i,x in enumerate(nodes) if mask>>i&1]
            if len(chosen)!=3 or sum(x['cost'] for x in chosen)>d['budget']:continue
            if any(lat[frozenset((a['id'],b['id']))]>d['max_pair_latency'] for a,b in itertools.combinations(chosen,2)):continue
            valid=True
            for failed in failure_masks:
                survivors=[x for i,x in enumerate(nodes) if (mask&~failed)>>i&1]
                if sum(x['vote_weight'] for x in survivors)<d['quorum'] or not any(x['writable'] for x in survivors):valid=False
            if valid:feasible.append(sorted(x['id'] for x in chosen))
        self.assertEqual(sorted(feasible),EXPECTED['E02']['feasible_placements'])

    def test_e08_independent_all_integer_waits(self):
        d=data('E08');paths={};stack=[('S',0,d['capacity'],('S',),(),(),0)]
        while stack:
            node,time,battery,seen,ids,deps,energy=stack.pop()
            if node=='T':
                candidate=(time,energy,ids,deps)
                if ids not in paths or candidate<paths[ids]:paths[ids]=candidate
                continue
            for edge in d['edges']:
                if edge['source']!=node or edge['target'] in seen:continue
                available=d['capacity'] if node in d['recharge'] else battery
                if available<edge['energy']:continue
                for departure in range(max(time,edge['open']),min(edge['close'],d['deadline']-edge['duration']+1)):
                    stack.append((edge['target'],departure+edge['duration'],available-edge['energy'],seen+(edge['target'],),ids+(edge['id'],),deps+(departure,),energy+edge['energy']))
        self.assertEqual(len(paths),8);self.assertEqual(min(paths.values()),(9,14,('b','f','j','k'),(0,2,4,7)))

    def test_e10_independent_cartesian_schedules(self):
        d=data('E10');ops=sorted(d['operations'],key=lambda x:x['id']);feasible=[]
        choices=[o['permitted_starts'] if o['permitted_starts'] is not None else range(d['horizon']-o['duration']+1) for o in ops]
        for times in itertools.product(*choices):
            starts=dict(zip((o['id'] for o in ops),times));finish={o['id']:starts[o['id']]+o['duration'] for o in ops}
            if any(finish[p]>starts[o['id']] for o in ops for p in o['requires']):continue
            if any(sum(o['demand'][r] for o in ops if starts[o['id']]<=t<finish[o['id']])>cap for r,cap in d['capacities'].items() for t in range(d['horizon'])):continue
            feasible.append((max(finish.values()),sum(starts[o['id']]*o['risk_weight'] for o in ops),times))
        self.assertEqual(min(feasible),(8,72,(0,0,2,3,5,6)))

    def test_e11_independent_binary_portfolios(self):
        d=data('E11');actions=d['actions'];count=0;best=None
        for bits in itertools.product((0,1),repeat=len(actions)):
            chosen={a['id'] for a,b in zip(actions,bits) if b};cost=sum(a['cost']*b for a,b in zip(actions,bits))
            if cost>d['budget']:continue
            if any(a['id'] in chosen and any(p not in chosen for p in a['requires']) for a in actions):continue
            if any(a in chosen and b in chosen for a,b in d['incompatible']):continue
            count+=1;losses=[]
            for s in d['scenarios']:
                loss=s['base_loss']
                for a in chosen:loss-=s['reductions'][a]
                for bonus in s['bonuses']:
                    if all(a in chosen for a in bonus['actions']):loss-=bonus['reduction']
                losses.append(max(0,loss))
            objective=(max(losses),sum(x*s['weight'] for x,s in zip(losses,d['scenarios'])),cost,sorted(chosen))
            if best is None or objective<best:best=objective
        self.assertEqual(count,43);self.assertEqual(best,(30,145,12,['a','b','c','e','g']))


def _reference_test(tid):
    def test(self):
        self.assertEqual(e.reference_answer(tid),EXPECTED[tid]);self.assertTrue(e.evaluate(tid,response(EXPECTED[tid]))['passed'])
        # Every output field is indispensable to exact acceptance.
        for key in EXPECTED[tid]:
            a=copy.deepcopy(EXPECTED[tid]);del a[key]
            self.assertFalse(e.evaluate(tid,response(a))['passed'],key)
    return test

def _mutant_test(tid,mutate):
    def test(self):
        a=copy.deepcopy(EXPECTED[tid]);mutate(a);score=e.evaluate(tid,response(a))
        self.assertFalse(score['passed']);self.assertFalse(score['errors']);self.assertLess(score['checks_passed'],score['checks_total'])
    return test

for tid in EXPECTED:
    setattr(Fixtures,'test_'+tid+'_correct_reference',_reference_test(tid))
    for label,mutation in MUTATIONS[tid]:setattr(Fixtures,'test_'+tid+'_'+label,_mutant_test(tid,mutation))

if __name__=='__main__':unittest.main()
