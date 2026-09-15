# Author: Angelis Pseftis
# Synthetic benchmark and evaluator; MIT.
"""Deterministic rubric, deliberately outside model-visible fixture directories.

Generated Python executes only in the child process through the macOS OS sandbox
provided by scripts.execution_sandbox. Unsupported hosts fail closed. The tested
profile denies network and private workspace reads, uses a clean environment,
and bounds CPU, file size, open descriptors, output, and elapsed runtime.
Data-memory limits are not claimed on this host.
Natural-language rationale correctness is not scored: presence, decisions, and
source line references are scored deterministically.
"""
import ast
import hashlib
import json

TIMEOUT_SECONDS = 5
MAX_CODE_BYTES = 100_000


_WORKER = r'''
import copy, json, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
resource.setrlimit(resource.RLIMIT_FSIZE, (1048576, 1048576))
resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
# macOS RLIMIT_AS is not consistently supported. OS sandbox remains required.
try:
    resource.setrlimit(resource.RLIMIT_AS, (268435456, 268435456))
except (ValueError, OSError):
    pass
payload = json.load(sys.stdin)
namespace = {'__name__': 'candidate'}
exec(compile(payload['code'], '<candidate>', 'exec'), namespace)
results = []
for case in payload['cases']:
    entries = case['entries']
    blobs = {k: bytes.fromhex(v) for k, v in case['blobs'].items()}
    before = copy.deepcopy((entries, blobs))
    try:
        result = namespace['verify_snapshot'](entries, blobs, case['per_file_limit'], case['total_limit'])
        item = {'outcome': 'return', 'value': result}
    except ValueError:
        item = {'outcome': 'ValueError'}
    except BaseException as exc:
        item = {'outcome': type(exc).__name__}
    item['mutated'] = (entries, blobs) != before
    results.append(item)
print(json.dumps(results))
'''


def _run_generated(code, cases):
    """Run only bounded synthetic cases in the required OS sandbox child."""
    from scripts.execution_sandbox import run_python
    payload = {'code': code, 'cases': [
        {k: v for k, v in case.items() if k not in ('expected', 'name')}
        for case in cases
    ]}
    result = run_python(_WORKER, stdin_text=json.dumps(payload), timeout=TIMEOUT_SECONDS)
    if result.returncode:
        raise RuntimeError(f'Worker exited {result.returncode}: {result.stderr[:2000]}')
    if len(result.stdout.encode()) > 1_048_576:
        raise ValueError('Worker output exceeds bound')
    return json.loads(result.stdout)


def _coding_cases():
    def entry(path='a', data=b'abc'):
        return {'path': path, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    cases = []
    def add(name, entries, blobs, per=100, total=100, valid=False):
        expected = {'files': len(entries), 'total_bytes': sum(len(blobs[e['path']]) for e in entries)} if valid else None
        cases.append({'name': name, 'entries': entries, 'blobs': {k: v.hex() for k,v in blobs.items()}, 'per_file_limit': per, 'total_limit': total, 'expected': expected})
    add('valid_exact_limits', [entry('dir/a'), entry('b', b'xy')], {'dir/a': b'abc', 'b': b'xy'}, 3, 5, True)
    add('empty_snapshot', [], {}, 0, 0, True)
    add('empty_file', [entry('empty', b'')], {'empty': b''}, 0, 0, True)
    add('extra_blobs_ignored', [entry()], {'a': b'abc', 'extra': b'123456789'}, 3, 3, True)
    add('unicode_and_dot_in_name', [entry('δ/.keep')], {'δ/.keep': b'abc'}, valid=True)
    add('negative_perfile', [], {}, -1, 0)
    add('negative_aggregate', [], {}, 0, -1)
    for path in ['', '/a', 'a/', 'a//b', './a', 'a/../b', '../a', 'a/./b', 'a\\b', 'a\x00b']:
        add('bad_path_' + repr(path), [entry(path)], {path:b'abc'})
    add('duplicate_paths', [entry(), entry()], {'a':b'abc'})
    add('missing_blob', [entry()], {})
    for size in [-1, 2, 4]:
        e=entry(); e['size']=size
        add('declared_size_' + str(size), [e], {'a':b'abc'})
    for label,digest in [('mismatch','0'*64),('uppercase',hashlib.sha256(b'abc').hexdigest().upper()),('short','a'*63),('not_hex','g'*64)]:
        e=entry(); e['sha256']=digest
        add('digest_'+label,[e],{'a':b'abc'})
    add('perfile_overflow',[entry()],{'a':b'abc'},2,100)
    add('aggregate_overflow',[entry('a'),entry('b')],{'a':b'abc','b':b'abc'},3,5)
    return cases


def _code_contract(code):
    """Enforce only the explicitly enumerated source restrictions, not a sandbox."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f'SyntaxError: {exc}'
    forbidden = {'exec', 'eval', 'compile', '__import__', 'globals', 'locals',
                 'vars', 'getattr', 'setattr', 'delattr', 'dir'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name != 'hashlib' for a in node.names):
            return False, 'Only hashlib imports are allowed'
        if isinstance(node, ast.ImportFrom) and (node.module != 'hashlib' or node.level or any(a.name.startswith('__') for a in node.names)):
            return False, 'Only public hashlib imports are allowed'
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.decorator_list:
            return False, 'Decorators are prohibited'
        if isinstance(node, ast.Name) and node.id in forbidden:
            return False, f'Prohibited identifier: {node.id}'
        if isinstance(node, ast.Attribute) and node.attr.startswith('__') and node.attr.endswith('__'):
            return False, 'Double-underscore attribute access is prohibited'
    return True, 'Declared source constraints satisfied'


def evaluate(task_id, response):
    """Return passed/check counts, named checks, and evaluator errors (JSON safe)."""
    checks=[]
    errors=[]
    def check(name, passed, detail=''):
        checks.append({'name':name,'passed':bool(passed),'detail':detail})
    def finish():
        count=sum(c['passed'] for c in checks)
        return {'passed':bool(checks) and count==len(checks) and not errors,'checks_passed':count,'checks_total':len(checks),'checks':checks,'errors':errors}
    if task_id not in {'T01','T02','T03','T04'}:
        check('known_task',False); errors.append('Unknown task ID'); return finish()
    shape=isinstance(response,dict) and set(response)=={'answer','code'} and all(isinstance(response[k],str) for k in ('answer','code'))
    check('response_schema',shape)
    if not shape: return finish()
    if task_id=='T02':
        valid_code=0<len(response['code'].encode())<=MAX_CODE_BYTES
        check('bounded_nonempty_code',valid_code)
        if not valid_code:return finish()
        cases=_coding_cases()
        allowed, detail = _code_contract(response['code'])
        check('code_contract', allowed, detail)
        if not allowed:
            for case in cases:check(case['name'],False,'Source violates explicit contract')
            return finish()
        try:
            results=_run_generated(response['code'],cases)
            if not isinstance(results,list) or len(results)!=len(cases):raise ValueError('Malformed worker results')
            for case,result in zip(cases,results):
                expected=case['expected']
                success=isinstance(result,dict) and result.get('mutated') is False
                if expected is None:
                    success=success and result.get('outcome')=='ValueError'
                else:
                    value=result.get('value')
                    success=success and result.get('outcome')=='return' and type(value) is dict and value==expected and all(type(v) is int for v in value.values())
                check(case['name'],success,'Correct outcome and inputs preserved' if success else 'Outcome differs or input mutated')
        except Exception as exc:
            errors.append(f'{type(exc).__name__}: {exc}')
            for case in cases:check(case['name'],False,'Code could not be evaluated')
        return finish()
    check('noncoding_code_empty',response['code']=='')
    try: answer=json.loads(response['answer'])
    except (ValueError,TypeError) as exc:
        check('answer_json',False,str(exc));return finish()
    check('answer_object',isinstance(answer,dict))
    if not isinstance(answer,dict):return finish()
    if task_id=='T01':
        expected={'counts':{'PASS':3,'FAIL':0,'NOT_RUN':1,'UNKNOWN':1},'findings_observed':0,'overall_status':'INCOMPLETE','unknowns':['S03','S04']}
        check('answer_keys',set(answer)==set(expected))
        for key,value in expected.items():
            good=answer.get(key)==value
            if key=='counts':good=good and isinstance(answer[key],dict) and all(type(v) is int for v in answer[key].values())
            if key=='findings_observed':good=good and type(answer[key]) is int
            check(key,good)
    elif task_id=='T03':
        check('answer_keys',set(answer)=={'decisions'})
        decisions=answer.get('decisions')
        valid=isinstance(decisions,list) and len(decisions)==5 and all(isinstance(d,dict) and set(d)=={'id','is_issue','lines','reason'} and isinstance(d['id'],str) for d in decisions)
        if valid:valid={d['id'] for d in decisions}=={'C01','C02','C03','C04','C05'}
        check('candidate_coverage',valid)
        oracle={'C01':(False,{7}),'C02':(True,{9,10}),'C03':(True,{17}),'C04':(True,{19}),'C05':(False,{13,14})}
        by_id={d['id']:d for d in decisions} if valid else {}
        for cid,(issue,lines) in oracle.items():
            d=by_id.get(cid,{})
            check(cid+'_decision',type(d.get('is_issue')) is bool and d['is_issue']==issue)
            refs=d.get('lines',[])
            check(cid+'_source_reference',isinstance(refs,list) and bool(refs) and all(type(n) is int and 1<=n<=22 for n in refs) and bool(lines.intersection(refs)))
            check(cid+'_rationale_present',isinstance(d.get('reason'),str) and bool(d['reason'].strip()))
    else:
        expected={'as_of':'2026-08-12','current_state':'LAB_VERIFIED','current_source':'SRC-B','completed_gates':['G1','G2'],'unrun_gates':['G3','G4'],'unknowns':['U1','U2'],'superseded_sources':['SRC-A'],'production_ready':False}
        check('answer_keys',set(answer)==set(expected))
        for key,value in expected.items():
            got=answer.get(key)
            good=isinstance(got,list) and len(got)==len(value) and all(isinstance(x,str) for x in got) and set(got)==set(value) if isinstance(value,list) else type(got) is type(value) and got==value
            check(key,good)
    return finish()
