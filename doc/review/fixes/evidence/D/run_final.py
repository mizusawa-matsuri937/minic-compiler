"""Reproduce D's final validation using only temporary generated artifacts."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
PYTHON = '/Users/aqua_night/.local/bin/python3.11'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')


def snapshot():
    result = {}
    for directory in ('ccgen', 'minic', 'tests', 'scripts', 'rules', 'examples'):
        for path in sorted((ROOT / directory).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                result[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def execute(label, command, env=ENV, timeout=120):
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    elapsed = time.monotonic() - start
    (HERE / (label + '.stdout')).write_text(result.stdout)
    (HERE / (label + '.stderr')).write_text(result.stderr)
    count = re.search(r'Ran (\d+) tests? in ([\d.]+)s', result.stderr)
    counts = {'tests': int(count[1]), 'reported_seconds': float(count[2]),
              'failures': len(re.findall(r'^FAIL:', result.stderr, re.M)),
              'errors': len(re.findall(r'^ERROR:', result.stderr, re.M)),
              'skipped': len(re.findall(r'\.\.\. skipped ', result.stderr))} if count else None
    record = {'cwd':str(ROOT),'command':command,'environment':{key:env[key] for key in
              ('PYTHONDONTWRITEBYTECODE','MINIC_PYTHON','MINIC_BUILD_DIR','MINIC_OUT_DIR') if key in env},
              'exit_code':result.returncode,'elapsed_seconds':elapsed,'counts':counts,
              'stdout':result.stdout,'stderr':result.stderr}
    (HERE / (label + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print(label, result.returncode, counts, flush=True)
    if result.returncode or counts and (counts['failures'] or counts['errors'] or counts['skipped']):
        raise SystemExit('Validation failed: '+label)
    return result


if __name__ == '__main__':
    phase = sys.argv[1]
    before = snapshot()
    (HERE / ('source-snapshot-'+phase+'-before.json')).write_text(json.dumps(before,indent=2)+'\n')
    if phase == 'targeted':
        for ac in ('02','05','06','10','13','14','15','16','17','18','19','20','21','22'):
            execute('ac'+ac, [PYTHON,'-B','-m','unittest','discover','-s','tests','-k','ac'+ac,'-v'])
        execute('new-regressions', [PYTHON,'-B','-m','unittest','discover','-s','tests','-p','test_review*.py','-v'])
    elif phase == 'integration':
        execute('full-regression', [PYTHON,'-B','-m','unittest','discover','-s','tests','-v'])
        with tempfile.TemporaryDirectory(prefix='minic D final ') as directory:
            root=Path(directory)
            env=dict(ENV, MINIC_PYTHON=PYTHON, MINIC_BUILD_DIR=str(root/'frontend'), MINIC_OUT_DIR=str(root/'out'))
            result=execute('demo', ['bash','-c','echo 5 | bash scripts/demo.sh'],env=env)
            assert result.stdout.splitlines()[-3:] == ['15','120','1'], result.stdout
            generated={p.name:p.stat().st_size for p in (root/'frontend').iterdir() if p.is_file()}
            outputs={p.name:p.stat().st_size for p in (root/'out').iterdir() if p.is_file()}
            assert set(generated)=={'lexer.py','parser.py','lexer_tables.json','parser_tables.json','report.html'}
            assert set(outputs)=={'tokens.txt','tokens.json','ast.json','ast.txt','ast.html','ast.dot','demo.ll','demo.opt.ll','demo.s','demo'}
            assert all(generated.values()) and all(outputs.values())
            (HERE/'demo-products.json').write_text(json.dumps({'generated':generated,'outputs':outputs},indent=2)+'\n')
    else:
        raise SystemExit('expected targeted or integration')
    after=snapshot()
    (HERE / ('source-snapshot-'+phase+'-after.json')).write_text(json.dumps(after,indent=2)+'\n')
    assert before==after, 'Sources changed during validation'
    print('source_snapshot_unchanged', flush=True)
