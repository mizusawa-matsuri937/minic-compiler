import json
from pathlib import Path
import tempfile
import unittest
from minic.semantic import check
from support import Frontend


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class SemanticTests(unittest.TestCase):
    def test_ac13_diagnostics_and_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / 'semantic_error.ll').write_text('stale')
            result = frontend.compile('tests/fixtures/semantic_error.mc', out)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(result.stderr.splitlines(), [
                "tests/fixtures/semantic_error.mc:2:1: 语义错误[S002]: 变量 'a' 重复声明",
                "tests/fixtures/semantic_error.mc:3:1: 语义错误[S001]: 变量 'b' 未声明",
                'tests/fixtures/semantic_error.mc:4:9: 语义错误[S003]: 整型常数超过 2147483647',
                "tests/fixtures/semantic_error.mc:6:1: 语义错误[S001]: 变量 'd' 未声明",
            ])
            self.assertEqual({p.name for p in out.iterdir()},
                             {'tokens.txt', 'tokens.json', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot'})
            self.assertNotIn('_slot', (out / 'ast.json').read_text())

    def test_ac13_scopes_initializers_and_range(self):
        cases = [
            ('int x = x;', ['S001']),
            ('if (1) int a; write(a);', ['S001']),
            ('if (0) int a; else int b; read(b);', ['S001']),
            ('while (0) int a; a = 1;', ['S001']),
            ('int x = 1; { int x = x + 1; write(x); } write(x);', []),
            ('int x = 2147483647;', []),
            ('write(' + '9' * 5000 + ');', ['S003']),
            ('int a; a = 1; read(a); write(a);', []),
        ]
        for source, expected in cases:
            with self.subTest(source=source[:80]):
                tokens, errors = frontend.lexer.tokenize(source)
                self.assertEqual(errors, [])
                tree = frontend.parser.parse(tokens)
                self.assertEqual([e['code'] for e in check(tree)], expected)
        tokens, _ = frontend.lexer.tokenize('int x; { int x; write(x); } write(x);')
        tree = frontend.parser.parse(tokens)
        self.assertEqual(check(tree), [])
        self.assertEqual(tree['body'][0]['_slot'], 'x.addr')
        self.assertEqual(tree['body'][1]['body'][0]['_slot'], 'x.addr.1')
        self.assertEqual(tree['body'][1]['body'][1]['value']['_slot'], 'x.addr.1')
        self.assertEqual(tree['body'][2]['value']['_slot'], 'x.addr')
