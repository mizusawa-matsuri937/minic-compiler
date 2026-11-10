"""Regenerate baseline/fixed AST HTML and read-only browser measurement copies.

Run from any cwd; all generated analyzers, sources and HTML use a temporary directory.
Pass --hold to keep it alive while manually opening the printed file:// URLs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BASELINE = '2fa29b29440069881b91735e13c9a870450ef918'


def run(*command):
    result = subprocess.run([str(x) for x in command], cwd=ROOT,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--hold', action='store_true')
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='minic D browser ') as directory:
        root = Path(directory).resolve()
        frontend = root / 'frontend'
        run(sys.executable, '-B', '-m', 'ccgen', '--lex', 'rules/minic.lex',
            '--grammar', 'rules/minic.grammar', '--out', frontend)
        baseline = types.ModuleType('baseline_astviz')
        source = run('git', 'show', BASELINE + ':minic/astviz.py')
        exec(compile(source, 'baseline_astviz.py', 'exec'), baseline.__dict__)
        name = 'a' * 200
        long_source = root / 'long_identifier.mc'
        long_source.write_text(f'int {name}; write({name} + {name});\n', encoding='utf-8')
        hashes = {}
        for sample, source in [('long_identifier', long_source), ('demo', ROOT/'examples/demo.mc')]:
            fixed = root/'fixed'/sample
            run(sys.executable, '-B', '-m', 'minic', source, '--frontend', frontend,
                '--out', fixed, '--stop-after', 'ast')
            tree = json.loads((fixed/'ast.json').read_text())
            old = root/'baseline'/sample
            old.mkdir(parents=True)
            (old/'ast.html').write_text(baseline.html_tree(tree), encoding='utf-8')
            for original in (old/'ast.html', fixed/'ast.html'):
                html = original.read_text()
                measurement = original.with_name('geometry.html')
                measurement.write_text(html.replace('</body>', (HERE/'geometry.js').read_text()+'</body>'))
                hashes[str(original)] = hashlib.sha256(original.read_bytes()).hexdigest()
                print(original.as_uri())
                print(measurement.as_uri())
        print(json.dumps(hashes,indent=2))
        if args.hold:
            input('Press Return to clean temporary products after browser verification: ')


if __name__ == '__main__':
    main()
