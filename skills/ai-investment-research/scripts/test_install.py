"""Installer tests never touch installed host skills or the source skill."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install


class InstallTests(unittest.TestCase):
    def setUp(self):
        configured = os.environ.get('RESEARCH_TEST_TMPDIR')
        root = Path(configured).resolve() if configured else None
        if root: root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='install-synthetic-', dir=root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source' / install.NAME
        self.source.mkdir(parents=True)
        (self.source / 'SKILL.md').write_text('synthetic skill', encoding='utf-8')
        (self.source / '.hidden').write_text('pinned hidden bytes', encoding='utf-8')
        (self.source / '__pycache__').mkdir()
        (self.source / '__pycache__/ignored.pyc').write_bytes(b'cache')
        self.target = self.root / 'host-skills'

    def test_default_copy_preserves_hidden_and_omits_cache(self):
        result = install.install(self.target, source=self.source)
        self.assertEqual(result['mode'], 'copy')
        destination = self.target / install.NAME
        self.assertEqual((destination / '.hidden').read_bytes(), (self.source / '.hidden').read_bytes())
        self.assertFalse((destination / '__pycache__').exists())

    def test_dry_run_does_not_create_parent(self):
        self.assertEqual(install.install(self.target, dry_run=True, source=self.source)['status'], 'would-install')
        self.assertFalse(self.target.exists())

    def test_same_source_path_is_readonly_idempotent(self):
        with mock.patch('install.shutil.copytree', side_effect=AssertionError('write attempted')):
            self.assertEqual(install.install(self.source.parent, source=self.source)['status'], 'already-source')

    def test_identical_copy_is_readonly_idempotent(self):
        install.install(self.target, source=self.source)
        with mock.patch('install.shutil.copytree', side_effect=AssertionError('write attempted')):
            self.assertEqual(install.install(self.target, source=self.source)['status'], 'already-installed')

    def test_different_existing_directory_is_never_overwritten(self):
        install.install(self.target, source=self.source)
        existing = self.target / install.NAME / 'SKILL.md'; existing.write_text('keep this', encoding='utf-8')
        for dry in (False, True):
            with self.subTest(dry=dry), self.assertRaisesRegex(ValueError, 'refusing to overwrite'):
                install.install(self.target, dry_run=dry, source=self.source)
        self.assertEqual(existing.read_text(encoding='utf-8'), 'keep this')

    def test_nested_install_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inside the source'):
            install.install(self.source / 'nested', source=self.source)

    def test_link_is_created_and_idempotent_without_redirect(self):
        result = install.install(self.target, mode='link', source=self.source)
        self.assertEqual(result['status'], 'installed')
        destination = self.target / install.NAME
        self.addCleanup(lambda: destination.unlink() if destination.is_symlink() else destination.rmdir())
        self.assertEqual(destination.resolve(), self.source)
        self.assertEqual(install.install(self.target, mode='link', source=self.source)['status'], 'already-source')
        other = self.root / 'other'; other.mkdir(); (other / 'SKILL.md').write_text('other', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'refusing to replace or redirect'):
            install.install(self.target, mode='link', source=other)
        self.assertEqual(destination.resolve(), self.source)

    def test_public_cli_dry_run_uses_copy_and_creates_nothing(self):
        # Execute the real CLI bytes in a fake skill so the scoped temp target is
        # outside that fake source, matching an actual host installation.
        script = self.source / 'scripts/install.py'
        script.parent.mkdir()
        script.write_bytes(Path(install.__file__).read_bytes())
        result = subprocess.run([sys.executable, '-B', str(script), '--target', str(self.target), '--dry-run'],
                                text=True, capture_output=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['mode'], 'copy')
        self.assertFalse(self.target.exists())


if __name__ == '__main__':
    unittest.main()
