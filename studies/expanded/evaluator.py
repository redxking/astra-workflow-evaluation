# Author: Angelis Pseftis
# SPDX-License-Identifier: MIT
"""Independent deterministic oracles. Never copy this file into a task workspace.

All tasks use structured outcome reasoning; candidate code is never executed.
These synthetic contracts establish benchmark correctness, not operational safety.
"""
from pathlib import Path
import itertools
import json

BASE = Path(__file__).resolve().parent
AUTHOR = 'Angelis Pseftis'
LICENSE = 'MIT'
ROUTING_METADATA = {
 'E01': dict(review_opportunity=True,rationale='Network cut optimality and credential validity have independent failure modes.',independent_workstreams=['Directed reachability and minimum feasible cut','Identity, expiry, tenant and revocation decisions'],critical_checks=['authorized_probes','repair_edges']),
 'E02': dict(review_opportunity=True,rationale='Correlated failure survivability must be reconciled with placement constraints.',independent_workstreams=['Quorum and writable survivor scenarios','Latency, cost and deterministic selection'],critical_checks=['feasible_placements','selected']),
 'E03': dict(review_opportunity=False,rationale='Small ordered rule table is a bounded single-pass control.',independent_workstreams=[],critical_checks=['decisions']),
 'E04': dict(review_opportunity=True,rationale='Bitemporal evidence selection and dependency release gating can fail independently.',independent_workstreams=['Eligibility, freshness and observation chronology','Gate dependency and release decision'],critical_checks=['gates','decision','blocked_dependencies']),
 'E05': dict(review_opportunity=True,rationale='Correction eligibility and interval-set aggregation have distinct consequential errors.',independent_workstreams=['Publication cutoff and direct supersession','Downtime unions, monitor differences and fleet overlap'],critical_checks=['services','fleet_confirmed_minutes','retained_report_ids']),
 'E06': dict(review_opportunity=False,rationale='Explicit bounded evidence labels need no independent specialist work.',independent_workstreams=[],critical_checks=['claims']),
 'E07': dict(review_opportunity=True,rationale='Lease and attempt transitions interact with global idempotency and cancellation.',independent_workstreams=['Verify transition rules including lease, attempt and token guards','Independently derive chronological replay and terminal state trace'],critical_checks=['jobs','accepted_sequences','accepted_tokens']),
 'E08': dict(review_opportunity=True,rationale='Time-window reachability and recharge-constrained paths require independent checks.',independent_workstreams=['Simple path temporal feasibility and optimal arrival','Battery accounting and feasible sequence enumeration'],critical_checks=['selected_edges','departures','feasible_path_count']),
 'E09': dict(review_opportunity=False,rationale='Small dependency graph and deterministic SCC closure are bounded control work.',independent_workstreams=[],critical_checks=['cycle_components','blocked','build_order']),
 'E10': dict(review_opportunity=True,rationale='Migration precedence and windows must agree with capacity and exposure optimization.',independent_workstreams=['Dependency and permitted-start feasibility','Concurrent capacity and multi-objective schedule search'],critical_checks=['starts','makespan']),
 'E11': dict(review_opportunity=True,rationale='Portfolio constraint enumeration is separable from correlated scenario and bonus analysis.',independent_workstreams=['Budget, prerequisite and incompatibility feasibility','Scenario losses, interactions and minimax objective'],critical_checks=['actions','scenario_losses','worst_loss']),
 'E12': dict(review_opportunity=False,rationale='Small common-clock interval intersection is a bounded control.',independent_workstreams=[],critical_checks=['feasible_starts']),
}


def _subsets(values):
    return itertools.chain.from_iterable(itertools.combinations(values,k) for k in range(len(values)+1))


def _reach(edges, source, target, removed=()):
    seen={source}
    while True:
        nxt=seen | {e['target'] for e in edges if e['source'] in seen and e['id'] not in removed}
        if nxt==seen:return target in seen
        seen=nxt


def _e01(d):
    reach=[p['id'] for p in d['probes'] if _reach(d['edges'],p['source'],p['target'])]
    auth=[p['id'] for p in d['probes'] if p['id'] in reach and p['signed'] and p['audience']=='control' and p['tenant']==p['resource_tenant'] and d['now']<p['expires'] and p['key'] not in d['revoked_keys']]
    candidates=[]
    for subset in _subsets([e for e in d['edges'] if e['removable']]):
        ids=sorted(e['id'] for e in subset)
        if any(_reach(d['edges'],s,t,ids) for s,t in d['forbidden']):continue
        if not all(_reach(d['edges'],s,t,ids) for s,t in d['required']):continue
        candidates.append((sum(e['cost'] for e in subset),len(ids),ids))
    cost,_,cut=min(candidates)
    return dict(reachable_probes=sorted(reach),authorized_probes=sorted(auth),repair_edges=cut,repair_cost=cost)


def _e02(d):
    latency={frozenset((x['a'],x['b'])):x['ms'] for x in d['latencies']}
    candidates=[]
    for nodes in itertools.combinations(d['nodes'],3):
        cost=sum(n['cost'] for n in nodes)
        if cost>d['budget'] or any(latency[frozenset((a['id'],b['id']))]>d['max_pair_latency'] for a,b in itertools.combinations(nodes,2)):continue
        weights=[]
        for s in d['failures']:
            survivors=[n for n in nodes if n['site'] not in s['sites'] and n['provider'] not in s['providers']]
            weight=sum(n['vote_weight'] for n in survivors)
            if weight<d['quorum'] or not any(n['writable'] for n in survivors):break
            weights.append(weight)
        else:candidates.append((cost,-min(weights),sorted(n['id'] for n in nodes)))
    cost,negative,ids=min(candidates)
    return dict(feasible_placements=sorted(x[2] for x in candidates),selected=ids,selected_cost=cost,selected_min_surviving_weight=-negative)


def _e03(d):
    result=[]
    for q in sorted(d['requests'],key=lambda q:q['id']):
        rules=[r for r in d['rules'] if all(r[k] in ('*',q[k]) for k in ('subject','resource','action'))]
        rule=min(rules,key=lambda r:(-r['priority'],r['effect']!='deny',r['id'])) if rules else None
        expired=d['now']>=q['expiry']
        result.append(dict(id=q['id'],decision='deny' if expired or rule is None else rule['effect'],rule='EXPIRED' if expired else None if rule is None else rule['id']))
    return dict(decisions=result)


def _e04(d):
    selected={}
    for g in d['gates']:
        eligible=[r for r in d['records'] if r['gate']==g['id'] and r['recorded_at']<=d['cutoff'] and r['release']==d['release'] and r['environment']==d['environment'] and r['status'] in ('PASS','FAIL','NOT_RUN','UNKNOWN')]
        selected[g['id']]=max(eligible,key=lambda r:(r['observed_at'],r['recorded_at'],r['id'])) if eligible else None
    gates=[]
    for gid,r in sorted(selected.items()):
        status='UNKNOWN' if r is None or d['cutoff']-r['observed_at']>d['max_age'] else r['status']
        gates.append(dict(id=gid,status=status,source=None if r is None else r['id']))
    status={g['id']:g['status'] for g in gates}
    blocked=sorted(g['id'] for g in d['gates'] if any(status[p]!='PASS' for p in g['requires']))
    decision='BLOCKED' if 'FAIL' in status.values() else 'INCOMPLETE' if blocked or any(s!='PASS' for s in status.values()) else 'READY'
    return dict(gates=gates,decision=decision,blocked_dependencies=blocked,observed_findings=sum(r['findings'] for r in selected.values() if r and r['findings'] is not None),unknown_finding_gates=sorted(g for g,r in selected.items() if r is None or r['findings'] is None))


def _e05(d):
    published={r['id'] for r in d['reports'] if r['published']<=d['cutoff']}
    retained=[r for r in d['reports'] if r['id'] in published and r['superseded_by'] not in published and max(0,r['start'])<min(60,r['end']) and (r['kind']=='uncertain' or r['kind']=='down' and r['authoritative'])]
    def minutes(r):return set(range(max(0,r['start']),min(60,r['end'])))
    services=[];fleet=set()
    for sid in d['services']:
        confirmed=set();possible=set();coverage=set()
        for r in retained:
            if r['service']!=sid:continue
            if r['kind']=='down' and r['authoritative']:confirmed |= minutes(r)
            if r['kind']=='uncertain':possible |= minutes(r)
        possible |= confirmed
        for m in d['monitors']:
            if m['service']==sid:coverage |= minutes(m)
        fleet |= confirmed
        services.append(dict(id=sid,confirmed_minutes=len(confirmed),possible_minutes=len(possible),unobserved_confirmed_minutes=len(confirmed-coverage)))
    return dict(services=sorted(services,key=lambda x:x['id']),fleet_confirmed_minutes=len(fleet),retained_report_ids=sorted(r['id'] for r in retained))


def _e06(d):
    eligible=[s for s in d['sources'] if s['published']<=d['cutoff'] and s['scope']==d['scope'] and s['primary'] and not s['retracted']]
    out=[]
    for c in sorted(d['claims']):
        support=sorted(s['id'] for s in eligible if c in s['supports']);contra=sorted(s['id'] for s in eligible if c in s['contradicts'])
        status='CONFLICTED' if support and contra else 'SUPPORTED' if support else 'CONTRADICTED' if contra else 'UNKNOWN'
        out.append(dict(id=c,status=status,supporting=support,contradicting=contra))
    return dict(claims=out)


def _e07(d):
    jobs={j:dict(id=j,state='PENDING',attempt=0,lease_until=None) for j in d['jobs']};tokens=set();yes=[];no=[]
    def expire(t):
        for j in jobs.values():
            if j['state']=='RUNNING' and j['lease_until']<=t:j.update(state='PENDING',lease_until=None)
    for e in sorted(d['events'],key=lambda e:(e['time'],e['sequence'])):
        expire(e['time']);j=jobs[e['job']];accepted=False
        if e['kind']=='START' and j['state']=='PENDING':
            j.update(state='RUNNING',attempt=j['attempt']+1,lease_until=e['time']+e['lease']);accepted=True
        elif e['kind']=='RESULT' and j['state']=='RUNNING' and e['attempt']==j['attempt'] and e['token'] not in tokens:
            j.update(state='DONE',lease_until=None);tokens.add(e['token']);accepted=True
        elif e['kind']=='CANCEL' and j['state'] not in ('DONE','CANCELLED'):
            j.update(state='CANCELLED',lease_until=None);accepted=True
        (yes if accepted else no).append(e['sequence'])
    expire(d['horizon'])
    return dict(jobs=[jobs[j] for j in sorted(jobs)],accepted_sequences=yes,rejected_sequences=no,accepted_tokens=sorted(tokens))


def _e08(d):
    # With no deadlines on vertex arrival other than edge windows, earlier arrival
    # weakly dominates later arrival for a fixed simple path; waiting is free.
    candidates=[]
    def visit(v,t,battery,seen,ids,deps,energy):
        if v=='T':
            candidates.append((t,energy,ids,deps));return
        if v in d['recharge']:battery=d['capacity']
        for e in d['edges']:
            if e['source']!=v or e['target'] in seen or e['energy']>battery:continue
            depart=max(t,e['open']);arrival=depart+e['duration']
            if depart>=e['close'] or arrival>d['deadline']:continue
            visit(e['target'],arrival,battery-e['energy'],seen|{e['target']},ids+[e['id']],deps+[depart],energy+e['energy'])
    visit('S',0,d['capacity'],{'S'},[],[],0)
    t,energy,ids,deps=min(candidates)
    return dict(selected_edges=ids,departures=deps,arrival=t,energy_consumed=energy,feasible_path_count=len(candidates))


def _e09(d):
    deps={n:{b for a,b in d['edges'] if a==n} for n in d['nodes']}
    reach={n:set(deps[n]) for n in deps}
    for _ in deps:
        for n in deps:reach[n]|=set().union(*(reach[x] for x in list(reach[n]))) if reach[n] else set()
    cycle={n for n in deps if n in reach[n]};components=[]
    while cycle:
        n=min(cycle);comp=sorted(x for x in cycle if x==n or x in reach[n] and n in reach[x]);components.append(comp);cycle-=set(comp)
    members=set().union(*(set(c) for c in components));blocked={n for n in deps if n in members or reach[n]&members}
    order=[];todo=set(deps)-blocked
    while todo:
        n=min(n for n in todo if deps[n]<=set(order));order.append(n);todo.remove(n)
    return dict(cycle_components=sorted(components),blocked=sorted(blocked),build_order=order)


def _e10(d):
    ops={o['id']:o for o in d['operations']};order=[]
    while len(order)<len(ops):order.append(min(k for k,o in ops.items() if k not in order and set(o['requires'])<=set(order)))
    feasible=[]
    usage={r:[0]*d['horizon'] for r in d['capacities']}
    def visit(starts):
        if len(starts)==len(ops):
            makespan=max(starts[k]+ops[k]['duration'] for k in ops)
            risk=sum(starts[k]*ops[k]['risk_weight'] for k in ops)
            feasible.append((makespan,risk,tuple(starts[k] for k in sorted(ops))));return
        key=order[len(starts)];o=ops[key]
        earliest=max((starts[p]+ops[p]['duration'] for p in o['requires']),default=0)
        times=range(earliest,d['horizon']-o['duration']+1) if o['permitted_starts'] is None else o['permitted_starts']
        for t in times:
            if t<earliest or t+o['duration']>d['horizon']:continue
            span=range(t,t+o['duration'])
            if any(usage[r][m]+o['demand'][r]>cap for r,cap in d['capacities'].items() for m in span):continue
            for r in usage:
                for m in span:usage[r][m]+=o['demand'][r]
            starts[key]=t;visit(starts);del starts[key]
            for r in usage:
                for m in span:usage[r][m]-=o['demand'][r]
    visit({});makespan,risk,vector=min(feasible)
    return dict(starts=dict(zip(sorted(ops),vector)),makespan=makespan,risk_exposure=risk)


def _e11(d):
    feasible=[]
    for subset in _subsets(d['actions']):
        ids=sorted(a['id'] for a in subset);chosen=set(ids);cost=sum(a['cost'] for a in subset)
        if cost>d['budget'] or any(not set(a['requires'])<=chosen for a in subset) or any(set(pair)<=chosen for pair in d['incompatible']):continue
        losses={s['id']:max(0,s['base_loss']-sum(s['reductions'][i] for i in ids)-sum(b['reduction'] for b in s['bonuses'] if set(b['actions'])<=chosen)) for s in d['scenarios']}
        worst=max(losses.values());weighted=sum(losses[s['id']]*s['weight'] for s in d['scenarios'])
        feasible.append((worst,weighted,cost,ids,losses))
    worst,weighted,cost,ids,losses=min(feasible,key=lambda x:x[:4])
    return dict(actions=ids,cost=cost,scenario_losses=losses,worst_loss=worst,weighted_loss=weighted,feasible_portfolios=len(feasible))


def _e12(d):
    availability=[set().union(*(set(range(a,b)) for a,b in intervals)) for intervals in d['teams'].values()]
    blocked=set().union(*(set(range(a,b)) for a,b in d['blackouts']))
    starts=[]
    for t in range(d['window_start'],min(d['window_end'],d['deadline'])-d['duration']+1):
        interval=set(range(t,t+d['duration']))
        if not interval&blocked and all(interval<=a for a in availability):starts.append(t)
    return dict(feasible_starts=starts,earliest=min(starts) if starts else None,latest=max(starts) if starts else None)


SOLVERS={f'E{i:02}':globals()[f'_e{i:02}'] for i in range(1,13)}


def reference_answer(task_id):
    """Oracle for grader/tests only; not supplied in model-visible task workspace; access forbidden by common contract."""
    return SOLVERS[task_id](json.loads((BASE/'fixtures'/task_id/'input.json').read_text()))


def reference_response(task_id):
    return dict(answer=json.dumps(reference_answer(task_id),sort_keys=True),code='')


def _strict_equal(actual,expected):
    if type(actual) is not type(expected):return False
    if isinstance(expected,dict):return actual.keys()==expected.keys() and all(_strict_equal(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):return len(actual)==len(expected) and all(_strict_equal(a,b) for a,b in zip(actual,expected))
    return actual==expected


def _no_duplicates(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('Duplicate JSON key: '+k)
        result[k]=v
    return result


def evaluate(task_id,response):
    """Same result API as the frozen pilot; no candidate code executes."""
    checks=[];errors=[]
    def check(name,passed,detail=''):checks.append(dict(name=name,passed=bool(passed),detail=detail))
    def finish():
        count=sum(c['passed'] for c in checks)
        return dict(passed=bool(checks) and count==len(checks) and not errors,checks_passed=count,checks_total=len(checks),checks=checks,errors=errors)
    if task_id not in SOLVERS:
        check('known_task',False);errors.append('Unknown task ID');return finish()
    shape=type(response) is dict and set(response)=={'answer','code'} and all(type(response[k]) is str for k in response)
    check('response_schema',shape)
    if not shape:return finish()
    check('noncoding_code_empty',response['code']=='')
    if len(response['answer'].encode())>100000:
        check('answer_json',False,'Answer exceeds bound');return finish()
    try:
        answer=json.loads(response['answer'],object_pairs_hook=_no_duplicates,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Nonfinite value')))
    except (ValueError,TypeError,RecursionError) as exc:
        check('answer_json',False,str(exc));return finish()
    check('answer_object',type(answer) is dict)
    if type(answer) is not dict:return finish()
    try:expected=reference_answer(task_id)
    except Exception as exc:
        errors.append(f'Oracle error: {type(exc).__name__}: {exc}');return finish()
    check('answer_keys',answer.keys()==expected.keys())
    for key,value in expected.items():check(key,key in answer and _strict_equal(answer[key],value),'Exact type-sensitive structured answer')
    return finish()
