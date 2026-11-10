import ast
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from support import ROOT, run


class ProjectTests(unittest.TestCase):
    def test_ac21_standard_library_only(self):
        allowed = sys.stdlib_module_names | {'ccgen', 'minic', 'support'}
        files = [p for directory in ('ccgen', 'minic', 'tests', 'scripts')
                 for p in (ROOT / directory).rglob('*.py')]
        self.assertGreater(len(files), 20)
        for path in files:
            with self.subTest(path=str(path.relative_to(ROOT))):
                tree = ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 11))
                for node in ast.walk(tree):
                    names = []
                    if isinstance(node, ast.Import):
                        names = [n.name.split('.')[0] for n in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0:
                        names = [node.module.split('.')[0]]
                    self.assertTrue(set(names) <= allowed, names)
        manifests = ['requirements*.txt', 'Pipfile*', 'poetry.lock', 'uv.lock', 'pyproject.toml', 'setup.py', 'setup.cfg']
        for pattern in manifests:
            self.assertEqual(list(ROOT.glob(pattern)), [])
        # Check all test names, including ones not selected by a -k filter.
        for path in (ROOT / 'tests').glob('test_*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                    self.assertRegex(node.name, r'ac\d{2}')

    def test_ac21_exact_rule_and_sample_sources(self):
        spec = (ROOT / 'doc/task1/spec.md').read_text()
        for name, content in re.findall(r'`((?:examples|tests/fixtures)/[^`]+)`[^\n]*\n\n```(?:c|text)\n(.*?)```', spec, re.S):
            self.assertEqual((ROOT / name).read_bytes(), content.encode('utf-8'), name)
        runtime = spec.split('### 运行样例', 1)[1]
        samples = re.findall(r'^\| `([^`]+\.mc)` \| `([^`]+)` \|', runtime, re.M)
        self.assertEqual(len(samples), 6)
        for name, content in samples:
            self.assertEqual((ROOT / 'tests/fixtures/run' / name).read_bytes(), (content + '\n').encode('utf-8'), name)
        design = (ROOT / 'doc/task1/design.md').read_text()
        blocks = re.findall(r'```text\n(.*?)```', design, re.S)
        for name, prefix in [('minic.lex', '# mini-C 词法规则'), ('minic.grammar', '# mini-C 语法规则')]:
            expected = next(b for b in blocks if b.startswith(prefix))
            self.assertEqual((ROOT / 'rules' / name).read_bytes(), expected.encode('utf-8'))

    @unittest.skipUnless(shutil.which('clang'), 'clang 不在 PATH 中，AC22 演示未验证')
    def test_ac22_demo_script_and_statement_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = dict(os.environ, MINIC_PYTHON=sys.executable,
                       MINIC_BUILD_DIR=str(root / 'frontend'), MINIC_OUT_DIR=str(root / 'compiled'))
            result = run('bash', ROOT / 'scripts/demo.sh', cwd=root, env=env, input='5\n')
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            self.assertEqual(lines[-3:], ['15', '120', '1'])
            for name in ('tokens.txt', 'tokens.json', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot',
                         'demo.ll', 'demo.opt.ll', 'demo.s', 'demo'):
                self.assertIn(str(root / 'compiled' / name), lines[:-3])
            tree = json.loads((root / 'compiled/ast.json').read_text())
            nodes = []
            def walk(value):
                if isinstance(value, dict):
                    if 'type' in value:
                        nodes.append(value)
                    for child in value.values():
                        walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)
            walk(tree)
            self.assertTrue({'VarDecl', 'Assign', 'If', 'While', 'Read', 'Write'} <= {n['type'] for n in nodes})
            self.assertTrue(any(n['type'] == 'If' and 'else' in n for n in nodes))
