"""Capture only B's targeted unittest cases and actual child-process output."""
import argparse
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=('before', 'after', 'final'))
args = parser.parse_args()
os.chdir(ROOT)
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT)]
from test_review_generated import GeneratedReviewTests

records = []
original_run = subprocess.run

def recorded_run(command, *positional, **options):
    result = original_run(command, *positional, **options)
    records.append({'command': [str(v) for v in command], 'cwd': str(options.get('cwd', ROOT)),
                    'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    return result

suite = unittest.defaultTestLoader.loadTestsFromTestCase(GeneratedReviewTests)
stream = io.StringIO()
with patch('subprocess.run', recorded_run):
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
exit_code = 0 if result.wasSuccessful() else 1
command = f'PYTHONDONTWRITEBYTECODE=1 {shlex.quote(sys.executable)} -B ' + shlex.join(sys.argv)
payload = {'command': command, 'cwd': str(ROOT), 'python': sys.version,
           'exit_code': exit_code, 'tests_run': result.testsRun,
           'failures': len(result.failures), 'errors': len(result.errors),
           'skipped': len(result.skipped), 'stdout': '', 'stderr': stream.getvalue(),
           'children': records}
target = Path(__file__).with_name(args.phase + '.json')
if target.exists():
    raise SystemExit(f'Refusing to overwrite evidence: {target}')
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(stream.getvalue(), end='')
print(f'Captured {len(records)} child commands; exit_code={exit_code}; evidence={target}')
sys.exit(exit_code)
