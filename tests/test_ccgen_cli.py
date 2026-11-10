import ast
from pathlib import Path
import tempfile
import unittest
from support import generate, ROOT


class CLItests(unittest.TestCase):
    def test_ac01_deterministic_standalone_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('one', 'two'):
                result = generate(root / name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(set(p.name for p in (root / name).iterdir()),
                                 {'lexer.py', 'parser.py', 'lexer_tables.json', 'parser_tables.json', 'report.html'})
            for file in (root / 'one').iterdir():
                self.assertEqual(file.read_bytes(), (root / 'two' / file.name).read_bytes())
                if file.suffix == '.py':
                    tree = ast.parse(file.read_text())
                    imports = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            imports.extend(n.name.split('.')[0] for n in node.names)
                        elif isinstance(node, ast.ImportFrom):
                            imports.append(node.module.split('.')[0])
                    self.assertTrue({'ccgen', 'minic'}.isdisjoint(imports))

    def test_ac08_undeclared_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            grammar = root / 'no_prefer.grammar'
            grammar.write_text((ROOT / 'rules/minic.grammar').read_text().replace('%prefer shift else\n', ''))
            for i, lex, gram, lookahead in [
                (1, 'tests/fixtures/calc.lex', 'tests/fixtures/ambiguous.grammar', '+'),
                (2, 'rules/minic.lex', grammar, 'else'),
            ]:
                with self.subTest(grammar=str(gram)):
                    out = root / str(i)
                    out.mkdir()
                    result = generate(out, lex, gram)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(repr(lookahead), result.stderr)
                    self.assertIn('移进-归约', result.stderr)
                    self.assertIn('状态', result.stderr)
                    self.assertIn(' -> ', result.stderr)
                    self.assertIn('·', result.stderr)
                    self.assertEqual(list(out.iterdir()), [])

    def test_ac08_reduce_reduce_never_resolved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            grammar = root / 'rr.grammar'
            grammar.write_text('%prefer shift num\nS -> A num\nS -> B num\nA -> ε\nB -> ε\n')
            result = generate(root / 'out', 'tests/fixtures/calc.lex', grammar)
            self.assertEqual(result.returncode, 2)
            self.assertIn('归约-归约', result.stderr)
            self.assertFalse((root / 'out').exists())

    def test_ac09_invalid_rules_atomic(self):
        cases = [
            ('X (ab\n', 'S -> X\n', 'bad.lex', '右括号'),
            ('X a\n', 'S -> foo\n', 'bad.grammar', 'foo'),
            ('X a\n', 'S -> X X X => $5\n', 'bad.grammar', '$5'),
            ('X a*\n', 'S -> X\n', 'bad.lex', '空串'),
            ('X a\n', 'S -> X => Node(value=$1\n', 'bad.grammar', '语法错误'),
        ]
        for lex, grammar, bad, message in cases:
            with self.subTest(bad=bad, content=lex + grammar), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'bad.lex').write_text(lex)
                (root / 'bad.grammar').write_text(grammar)
                out = root / 'gen'
                out.mkdir()
                result = generate(out, root / 'bad.lex', root / 'bad.grammar')
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(f'{root / bad}:1:', result.stderr)
                self.assertIn(message, result.stderr)
                self.assertEqual(list(out.iterdir()), [])
                # A failed regeneration must also preserve an existing result.
                sentinel = out / 'lexer.py'
                sentinel.write_bytes(b'previous valid result\n')
                result = generate(out, root / 'bad.lex', root / 'bad.grammar')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(sentinel.read_bytes(), b'previous valid result\n')

    def test_ac09_directive_location(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            grammar = root / 'bad-prefer.grammar'
            grammar.write_text('# header\n%prefer shift missing\nS -> num\n')
            result = generate(root / 'generated', 'tests/fixtures/calc.lex', grammar)
            self.assertEqual(result.returncode, 2)
            self.assertIn(f'{grammar}:2:', result.stderr)
            self.assertIn('missing', result.stderr)
            self.assertFalse((root / 'generated').exists())
