"""Adversarial offline checks. Author: Angelis Pseftis."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('replicate', HERE / 'replicate.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class ReplicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, data):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data) if not isinstance(data, str) else data)
        return r.digest(p)

    def release(self):
        manifest = {}
        for prefix in ('', 'studies/expanded/'):
            sha = self.write(prefix + 'fixture.txt', 'fixed')
            manifest[prefix + 'fixture.txt'] = sha
            manifest[prefix + 'protocol.json'] = self.write(prefix + 'protocol.json', {'files': {'fixture.txt': sha}})
        self.write('release-manifest.json', manifest)

    def submission(self):
        s = r.read_json(HERE / 'submission.template.json')
        self.write('submission.json', s)
        return s

    def test_release_complete_and_unanchored(self):
        self.release()
        result = r.verify_release(self.root, 'release-manifest.json')
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['external_manifest_anchor_status'], 'unknown')

    def test_tamper_original_and_expanded(self):
        self.release()
        self.write('fixture.txt', 'tampered')
        self.write('studies/expanded/fixture.txt', 'tampered')
        result = r.verify_release(self.root, 'release-manifest.json')
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(all(p['frozen_files']['status'] == 'fail' for p in result['protocols'].values()))

    def test_manifest_anchor_detects_rewritten_manifest(self):
        self.release()
        self.assertEqual(r.verify_release(self.root, 'release-manifest.json', '0'*64)['status'], 'fail')

    def test_missing_release_input_unknown(self):
        self.release(); (self.root / 'fixture.txt').unlink()
        self.assertEqual(r.verify_release(self.root, 'release-manifest.json')['status'], 'unknown')

    def test_blank_submission_never_passes(self):
        self.submission()
        result = r.inspect_bundle(self.root, 'submission.json')
        self.assertEqual(result['inspection_status'], 'unknown')
        self.assertTrue(all(x['classification'] == 'self_report_only' for x in result['claims']))

    def test_self_report_and_matching_link_do_not_establish_independence(self):
        s = self.submission(); sha = self.write('evidence.txt', 'independent pass claimed')
        for c in s['claims']:
            c.update(reported_status='pass', evidence=[{'kind':'local_file','reference':'evidence.txt','sha256':sha,'description':'assertion'}])
        self.write('submission.json', s)
        result = r.inspect_bundle(self.root, 'submission.json')
        self.assertEqual(result['independence_status'], 'unknown')
        self.assertEqual(result['inspection_status'], 'unknown')
        self.assertEqual(result['claims'][0]['evidence'][0]['integrity_status'], 'pass')

    def test_missing_evidence_and_tampered_evidence(self):
        s = self.submission(); link = {'kind':'local_file','reference':'missing.txt','sha256':'0'*64,'description':''}
        s['claims'][0]['evidence'] = [link]; self.write('submission.json', s)
        self.assertEqual(r.inspect_bundle(self.root, 'submission.json')['claims'][0]['evidence'][0]['integrity_status'], 'unknown')
        self.write('missing.txt', 'different')
        self.assertEqual(r.inspect_bundle(self.root, 'submission.json')['inspection_status'], 'fail')

    def test_external_url_not_retrieved(self):
        s = self.submission(); s['claims'][0]['evidence'] = [{'kind':'external_url','reference':'https://example.invalid/a','sha256':None,'description':''}]
        self.write('submission.json', s)
        self.assertEqual(r.inspect_bundle(self.root, 'submission.json')['claims'][0]['evidence'][0]['integrity_status'], 'unknown')

    def test_paths_rejected(self):
        for p in ('../private', '/etc/passwd', '.codex/auth.json', '.env', 'config.toml', 'https://x/y', 'a\\b'):
            with self.assertRaises(ValueError): r.local_file(self.root, p)
        (self.root/'link').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError): r.local_file(self.root, 'link')

    def test_missing_claim_categories_unknown(self):
        s = self.submission(); s['claims'] = []; self.write('submission.json', s)
        self.assertEqual(len(r.inspect_bundle(self.root, 'submission.json')['missing_claim_categories']), 9)

    def test_malformed_and_duplicate_keys_rejected(self):
        self.write('duplicate.json', '{"a":1,"a":2}')
        with self.assertRaises(ValueError): r.read_json(self.root/'duplicate.json')
        s=self.submission(); s['claims'] = 'pass'; self.write('submission.json',s)
        with self.assertRaises(ValueError): r.inspect_bundle(self.root,'submission.json')

    def test_environment_has_no_identifiers_or_paths(self):
        e = r.environment()
        self.assertNotIn('hostname', e); self.assertNotIn('user', e); self.assertNotIn('cwd', e)
        self.assertIsNone(e['model_version'])

if __name__ == '__main__': unittest.main()
