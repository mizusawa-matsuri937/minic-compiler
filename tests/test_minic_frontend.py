import json
from pathlib import Path
import tempfile
import unittest
from support import Frontend, python


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class FrontendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)

    def test_ac06_all_lex_errors_and_stale_cleanup(self):
        for name in ['ast.json', 'ast.html', 'ast.dot', 'ast.txt', 'lex_error.ll', 'lex_error.opt.ll', 'lex_error.s', 'lex_error']:
            (self.out / name).write_text('stale')
        (self.out / 'unrelated.keep').write_text('keep')
        result = frontend.compile('tests/fixtures/lex_error.mc', self.out)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr.splitlines(), [
            "tests/fixtures/lex_error.mc:1:11: 词法错误[L001]: 非法字符 '@'",
            "tests/fixtures/lex_error.mc:2:7: 词法错误[L001]: 非法字符 '$'",
        ])
        self.assertEqual({p.name for p in self.out.iterdir()}, {'tokens.json', 'tokens.txt', 'unrelated.keep'})
        payload = json.loads((self.out / 'tokens.json').read_text())
        self.assertEqual(len(payload['errors']), 2)
        self.assertEqual([t['lexeme'] for t in payload['tokens']],
                         ['int', 'a', '=', '3', '4', ';', 'a', '=', 'a', '2', ';'])

    def test_ac10_expression_ast(self):
        result = frontend.compile('tests/fixtures/expr.mc', self.out, '--stop-after', 'ast')
        self.assertEqual(result.returncode, 0, result.stderr)
        tree = json.loads((self.out / 'ast.json').read_text())
        self.assertEqual(tree['type'], 'Program')
        self.assertEqual(len(tree['body']), 3)
        decl, second, third = tree['body']
        self.assertEqual((decl['type'], decl['name']), ('VarDecl', 'x'))
        self.assertEqual(second['type'], 'Assign')
        self.assertEqual(third['type'], 'Assign')
        def expression(node):
            if node['type'] == 'Number':
                return int(node['value'])
            self.assertEqual(node['type'], 'BinaryOp')
            return node['op'], expression(node['left']), expression(node['right'])
        self.assertEqual(expression(decl['init']), ('-', ('+', 1, ('*', 2, 3)), 4))
        self.assertEqual(expression(second['value']), ('*', ('+', 1, 2), 3))
        self.assertEqual(expression(third['value']), ('/', ('/', 8, 4), 2))

    def test_ac11_nearest_else(self):
        result = frontend.compile('tests/fixtures/dangling_else.mc', self.out, '--stop-after', 'ast')
        self.assertEqual(result.returncode, 0, result.stderr)
        outer = json.loads((self.out / 'ast.json').read_text())['body'][3]
        self.assertEqual(outer['type'], 'If')
        self.assertNotIn('else', outer)
        self.assertEqual(outer['then']['type'], 'If')
        self.assertIn('else', outer['then'])

    def test_ac12_exact_syntax_errors(self):
        for name, position, actual, expected in [
            ('syntax_chain', (1, 15), '<', ['+', '-', '*', '/', ';']),
            ('syntax_eof', (1, 10), '$', None),
        ]:
            with self.subTest(name=name):
                source = f'tests/fixtures/{name}.mc'
                out = self.out / name
                out.mkdir()
                for stale in ['ast.json', 'ast.txt', 'ast.dot', 'ast.html', name + '.ll']:
                    (out / stale).write_text('stale')
                result = frontend.compile(source, out)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(len(result.stderr.splitlines()), 1)
                self.assertTrue(result.stderr.startswith(f'{source}:{position[0]}:{position[1]}: 语法错误[P001]:'))
                self.assertEqual({p.name for p in out.iterdir()}, {'tokens.json', 'tokens.txt'})
                tokens = json.loads((out / 'tokens.json').read_text())['tokens']
                with self.assertRaises(frontend.parser.ParseError) as caught:
                    frontend.parser.parse(tokens)
                error = caught.exception
                self.assertEqual((error.line, error.col), position)
                self.assertEqual(error.actual_kind, actual)
                if expected is not None:
                    self.assertEqual(error.expected, expected)
                    self.assertEqual(result.stderr.split(': 语法错误[P001]: ')[1].strip(),
                                     "遇到 '<'，期望 '+' '-' '*' '/' ';' 之一")
                else:
                    self.assertIn(';', error.expected)
                    self.assertIn('输入结束', result.stderr)

    def test_ac12_stop_after_tokens_and_missing_frontend(self):
        result = frontend.compile('tests/fixtures/syntax_chain.mc', self.out, '--stop-after', 'tokens')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.name for p in self.out.iterdir()}, {'tokens.json', 'tokens.txt'})
        result = python('-m', 'minic', 'examples/demo.mc', '--frontend', self.out / 'missing', '--out', self.out)
        self.assertEqual(result.returncode, 2)
        self.assertIn('请先运行', result.stderr)
