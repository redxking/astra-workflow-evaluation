#!/usr/bin/env python3
"""Offline replication intake and integrity checks. Author: Angelis Pseftis."""
import argparse
import datetime
import hashlib
import json
import platform
import re
import sys
from pathlib import Path, PurePosixPath

AUTHOR = 'Angelis Pseftis'
HERE = Path(__file__).resolve().parent
HEX = re.compile(r'^[0-9a-f]{64}$')
REQUIRED = ('release_integrity', 'protocol_integrity', 'environment', 'run_records',
            'scoring', 'usage_accounting', 'timing', 'deviations', 'reviewer_independence')


def read_json(path):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError('Duplicate JSON key')
            obj[key] = value
        return obj
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))


def local_file(root, name):
    """Confine user-specified references; never follow symlinks or private path names."""
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Invalid relative path')
    parts = PurePosixPath(name).parts
    if PurePosixPath(name).is_absolute() or '..' in parts or ':' in name:
        raise ValueError('Path must remain inside supplied root')
    denied = {'.git', '.ssh', '.aws', '.azure', '.codex', '.config', 'auth.json',
              'credentials', 'credentials.json', 'secrets.json', 'config.toml'}
    if any(p.lower() in denied or p.lower().startswith('.env') or p.lower().endswith(('.pem', '.key')) for p in parts):
        raise ValueError('Private or credential path rejected')
    p = root.resolve()
    for part in parts:
        p = p / part
        if p.is_symlink():
            raise ValueError('Symlinks are not accepted')
    if not p.is_file():
        raise FileNotFoundError('Referenced file missing')
    return p


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify_files(root, mapping):
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError('Nonempty hash mapping required')
    rows = []
    for name, expected in sorted(mapping.items()):
        row = {'path': name, 'expected_sha256': expected, 'status': 'unknown'}
        try:
            if not isinstance(expected, str) or not HEX.fullmatch(expected):
                raise ValueError('Invalid SHA256')
            row['observed_sha256'] = digest(local_file(root, name))
            row['status'] = 'pass' if row['observed_sha256'] == expected else 'fail'
        except (OSError, ValueError) as exc:
            row['reason'] = type(exc).__name__
        rows.append(row)
    return {'status': 'fail' if any(r['status'] == 'fail' for r in rows) else
            'unknown' if any(r['status'] == 'unknown' for r in rows) else 'pass', 'files': rows}


def verify_release(root, manifest_name, anchor=None):
    manifest_path = local_file(root, manifest_name)
    manifest = read_json(manifest_path)
    observed = digest(manifest_path)
    if anchor is not None and not HEX.fullmatch(anchor):
        raise ValueError('Invalid manifest anchor SHA256')
    release = verify_files(root, manifest)
    protocols = {}
    for name in ('protocol.json', 'studies/expanded/protocol.json'):
        try:
            p = local_file(root, name)
            pin = verify_files(root, {name: manifest.get(name)})
            content = read_json(p)
            frozen = verify_files(p.parent, content.get('files'))
            protocols[name] = {'manifest_pin': pin, 'frozen_files': frozen}
        except (OSError, ValueError, AttributeError) as exc:
            protocols[name] = {'status': 'unknown', 'reason': type(exc).__name__}
    states = [release['status']]
    for p in protocols.values():
        states.extend([p['manifest_pin']['status'], p['frozen_files']['status']] if 'manifest_pin' in p else ['unknown'])
    anchor_status = 'unknown' if anchor is None else 'pass' if anchor == observed else 'fail'
    if anchor is not None:
        states.append(anchor_status)
    return {'author': AUTHOR, 'creator': AUTHOR,
            'status': 'fail' if 'fail' in states else 'unknown' if 'unknown' in states else 'pass',
            'scope': 'Listed bytes and frozen inputs only; not scientific validity or publication state.',
            'manifest_sha256': observed, 'external_manifest_anchor_status': anchor_status,
            'manifest_self_coverage': 'excluded; obtain digest through a separately trusted channel',
            'unlisted_files': 'not inspected; not covered or represented as published',
            'release': release, 'protocols': protocols}


def environment():
    return {'author': AUTHOR, 'creator': AUTHOR, 'captured_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'python_version': platform.python_version(), 'python_implementation': platform.python_implementation(),
            'os_family': platform.system(), 'os_release': platform.release(), 'architecture': platform.machine(),
            'collection_scope': 'Python and OS runtime metadata only; no host/user names, paths, environment variables, CLI commands, account configuration or package inventory.',
            'model_version': None, 'model_version_evidence': None, 'codex_version': None,
            'account_tier': None, 'cache_control': 'unknown'}


def validate(value, schema, path='$'):
    """Validate the JSON Schema subset used by submission.schema.json, no dependencies."""
    types = {'object': dict, 'array': list, 'string': str, 'null': type(None), 'boolean': bool,
             'number': (int, float), 'integer': int}
    if 'type' in schema:
        allowed = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(isinstance(value, types[t]) and not (t in ('number', 'integer') and isinstance(value, bool)) for t in allowed):
            raise ValueError(path + ': incorrect type')
    if 'const' in schema and value != schema['const']:
        raise ValueError(path + ': incorrect constant')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(path + ': invalid enum')
    if isinstance(value, str) and 'pattern' in schema and not re.search(schema['pattern'], value):
        raise ValueError(path + ': invalid pattern')
    if isinstance(value, dict):
        if any(k not in value for k in schema.get('required', [])):
            raise ValueError(path + ': required field missing')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError(path + ': unexpected field')
        for k, v in value.items():
            if k in props:
                validate(v, props[k], path + '.' + k)
    if isinstance(value, list):
        for i, v in enumerate(value):
            validate(v, schema.get('items', {}), path + '[' + str(i) + ']')


def inspect_bundle(root, name):
    submission = read_json(local_file(root, name))
    validate(submission, read_json(HERE / 'submission.schema.json'))
    rows = []
    for claim in submission['claims']:
        links = []
        for link in claim['evidence']:
            if link['kind'] == 'local_file':
                checked = verify_files(root, {link['reference']: link['sha256']})
                links.append({'reference': link['reference'], 'classification': 'linked_local_evidence',
                              'integrity_status': checked['status']})
            else:
                links.append({'reference': link['reference'], 'classification': 'external_link_unretrieved',
                              'integrity_status': 'unknown'})
        rows.append({'category': claim['category'], 'self_reported_status': claim['reported_status'],
                     'classification': 'self_report_only' if not links else 'claim_with_evidence_links',
                     'evidence': links, 'substantiation_status': 'unknown'})
    categories = [c['category'] for c in rows]
    if len(set(categories)) != len(categories):
        raise ValueError('Duplicate claim category')
    missing = sorted(set(REQUIRED) - set(categories))
    tampered = any(e['integrity_status'] == 'fail' for c in rows for e in c['evidence'])
    return {'author': AUTHOR, 'creator': AUTHOR, 'inspection_status': 'fail' if tampered else 'unknown',
            'independence_status': 'unknown', 'replication_outcome': 'unknown',
            'missing_claim_categories': missing, 'claims': rows,
            'boundary': 'Matching hashes establish bytes only. Identity, independence, source authenticity, evidence relevance, scoring, completeness and conclusions require substantive external review. No submission was transmitted.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    v = sub.add_parser('verify'); v.add_argument('--root', type=Path, required=True)
    v.add_argument('--manifest', default='release-manifest.json'); v.add_argument('--manifest-sha256')
    sub.add_parser('environment')
    t = sub.add_parser('template'); t.add_argument('--output', type=Path, required=True)
    i = sub.add_parser('inspect'); i.add_argument('--bundle', type=Path, required=True)
    i.add_argument('--submission', default='submission.json')
    args = parser.parse_args()
    try:
        if args.command == 'verify':
            report = verify_release(args.root, args.manifest, args.manifest_sha256)
        elif args.command == 'environment':
            report = environment()
        elif args.command == 'template':
            report = read_json(HERE / 'submission.template.json')
            with args.output.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, indent=2); stream.write('\n')
            print('Blank template created; no replication conducted or submitted.')
            return 0
        else:
            report = inspect_bundle(args.bundle, args.submission)
        print(json.dumps(report, indent=2, allow_nan=False))
        state = report.get('status', report.get('inspection_status'))
        return 1 if state == 'fail' else 2 if state == 'unknown' else 0
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(json.dumps({'status': 'unknown', 'error_type': type(exc).__name__,
                          'message': 'Input could not be safely processed; no pass is established.'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
