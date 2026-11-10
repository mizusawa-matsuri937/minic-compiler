"""Regression for the failure-tool test under a spaced interpreter path."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from support import ROOT


class PortabilityReviewTests(unittest.TestCase):
    def test_ac17_ac21_rv11_failed_clang_under_spaced_python(self):
        with tempfile.TemporaryDirectory(prefix="minic Python's path ") as directory:
            interpreter = Path(directory) / 'python3.11'
            interpreter.symlink_to(sys.executable)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            identity = subprocess.run(
                [str(interpreter), '-c', 'import sys; print(sys.executable)'],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(identity.returncode, 0, identity.stderr)
            self.assertEqual(identity.stdout.strip(), str(interpreter))
            result = subprocess.run(
                [str(interpreter), '-B', '-m', 'unittest', 'discover', '-s', 'tests',
                 '-p', 'test_backend.py', '-k', 'ac17_failed_clang_keeps_frontend', '-v'],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Ran 1 test', result.stderr)
            self.assertIn('test_ac17_failed_clang_keeps_frontend', result.stderr)
            self.assertNotIn('skipped', result.stderr)
