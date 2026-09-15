"""Installation preservation checks. Author: Angelis Pseftis."""
from pathlib import Path
import tempfile
import tomllib
import unittest
from scripts.install_workflow import install, rollback


class InstallTests(unittest.TestCase):
    def test_preview_apply_idempotence_and_exact_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            original = '# preserve comment\nmodel = "old-model"\n[some_plugin]\nenabled = true\n'
            instructions = '# Existing instructions\n\nKeep this instruction.\n'
            (home / 'config.toml').write_text(original)
            (home / 'AGENTS.md').write_text(instructions)
            preview = install(home)
            self.assertEqual((home / 'config.toml').read_text(), original)
            self.assertTrue(preview['files'])
            install(home, True)
            self.assertTrue(tomllib.loads((home / 'config.toml').read_text())['some_plugin']['enabled'])
            self.assertIn(instructions.rstrip(), (home / 'AGENTS.md').read_text())
            self.assertEqual(install(home, True)['files'], [])
            rollback(home)
            self.assertEqual((home / 'config.toml').read_text(), original)
            self.assertEqual((home / 'AGENTS.md').read_text(), instructions)

    def test_existing_routing_section_preserves_neighbors(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            original = '# Before\n\n## Adaptive Model, Reasoning, and Work Routing\nOld route.\n\n## Evidence\nKeep evidence.\n'
            (home / 'AGENTS.md').write_text(original)
            install(home, True)
            updated = (home / 'AGENTS.md').read_text()
            self.assertIn('# Before', updated)
            self.assertIn('## Evidence\nKeep evidence.', updated)
            self.assertNotIn('Old route.', updated)
            rollback(home)
            self.assertEqual((home / 'AGENTS.md').read_text(), original)

    def test_rollback_refuses_later_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            install(home, True)
            p = home / 'AGENTS.md'
            text = p.read_text() + '\nLater user edit.\n'
            p.write_text(text)
            with self.assertRaises(ValueError):
                rollback(home)
            self.assertEqual(p.read_text(), text)


if __name__ == '__main__':
    unittest.main()
