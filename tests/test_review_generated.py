"""Regression cases for reviewed generated-analyzer interfaces (temporary files only)."""
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import shutil
import struct
import tempfile
import unittest

from minic.frontend import load as load_frontend
from support import ROOT, generate, load, python


class GeneratedReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.assertFalse(self.root.is_relative_to(ROOT))

    def make_frontend(self, lex, grammar, name='generated'):
        lex_path, grammar_path = self.root / 'input.lex', self.root / 'input.grammar'
        lex_path.write_text(lex, encoding='utf-8')
        grammar_path.write_text(grammar, encoding='utf-8')
        out = self.root / name
        result = generate(out, lex_path, grammar_path)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        return out

    def isolated(self, generated):
        target = self.root / 'isolated'
        target.mkdir(exist_ok=True)
        for name in ('lexer.py', 'parser.py'):
            shutil.copyfile(generated / name, target / name)
        self.assertEqual(sorted(p.name for p in target.iterdir()), ['lexer.py', 'parser.py'])
        return target

    def scan_cli(self, directory, text, *options):
        source = self.root / 'source.txt'
        source.write_bytes(text.encode('utf-8'))
        return python('-I', '-B', directory / 'lexer.py', source, *options, cwd=self.root)

    def test_ac20_rv02_same_second_same_size_pyc_ignored(self):
        generated = self.make_frontend('X x\n', 'S -> X => Past(value=$1)\n')
        old = {}
        second = 1700000000
        for name in ('lexer', 'parser'):
            path = generated / (name + '.py')
            os.utime(path, ns=(second * 10**9 + 100, second * 10**9 + 100))
            cache = Path(py_compile.compile(str(path), doraise=True,
                         invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP))
            flags, mtime, size = struct.unpack('<III', cache.read_bytes()[4:16])
            self.assertEqual((flags, mtime, size), (0, second, path.stat().st_size))
            old[name] = path.read_bytes(), cache.read_bytes()
        self.make_frontend('X y\n', 'S -> X => Next(value=$1)\n')
        for name in ('lexer', 'parser'):
            path = generated / (name + '.py')
            os.utime(path, ns=(second * 10**9 + 900, second * 10**9 + 900))
            self.assertNotEqual(path.read_bytes(), old[name][0])
            self.assertEqual(path.stat().st_size, len(old[name][0]))
            self.assertEqual(int(path.stat().st_mtime), second)
            self.assertEqual(Path(importlib.util.cache_from_source(str(path))).read_bytes(), old[name][1])
        # Prove that ordinary cached loading really sees the old versions under these conditions.
        stale_lexer = load(generated / 'lexer.py', 'cache_control_lexer')
        stale_parser = load(generated / 'parser.py', 'cache_control_parser')
        old_tokens, errors = stale_lexer.tokenize('x')
        self.assertEqual(errors, [])
        self.assertEqual(stale_parser.parse(old_tokens)['type'], 'Past')
        result = self.scan_cli(generated, 'y')
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        payload = json.loads(result.stdout)
        token_path = self.root / 'tokens.json'
        token_path.write_text(result.stdout, encoding='utf-8')
        result = python('-I', '-B', generated / 'parser.py', token_path, cwd=self.root)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        current_tree = json.loads(result.stdout)
        self.assertEqual(current_tree['type'], 'Next')
        lexer, parser = load_frontend(generated)
        with self.subTest(module='lexer'):
            self.assertEqual(lexer.tokenize('y'), (payload['tokens'], []))
        with self.subTest(module='parser'):
            self.assertEqual(parser.parse(payload['tokens']), current_tree)

    def test_ac02_ac20_rv03_ast_token_field_collision(self):
        node = dict(type='Node', line=1, col=1, kind='x', lexeme='x')
        variants = [
            ('S -> X => Node(kind=$1, lexeme=$1)\n', node),
            ('S -> A => Root(value=$1)\nA -> X => Node(kind=$1, lexeme=$1)\n',
             dict(type='Root', line=1, col=1, value=node)),
            ('S -> A => [$1]\nA -> X => Node(kind=$1, lexeme=$1)\n', [node]),
            ('S -> A\nA -> X => Node(kind=$1, lexeme=$1)\n',
             dict(type='S', line=1, col=1, children=[node])),
            ('S -> A => $1\nA -> X => Node(kind=$1, lexeme=$1)\n', node),
            ('S -> X => $1\n', 'x'),
            ('S -> X\n', dict(type='S', line=1, col=1,
                              children=[dict(type='X', lexeme='x', line=1, col=1)])),
        ]
        for index, (grammar, expected) in enumerate(variants):
            with self.subTest(variant=index):
                generated = self.make_frontend('X x\n', grammar, 'generated' + str(index))
                # Only the two standalone sources enter this external runtime directory.
                isolated = self.root / ('runtime' + str(index))
                isolated.mkdir()
                for name in ('lexer.py', 'parser.py'):
                    shutil.copyfile(generated / name, isolated / name)
                result = self.scan_cli(isolated, 'x')
                self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
                payload = json.loads(result.stdout)
                token_path = self.root / 'tokens.json'
                token_path.write_text(result.stdout, encoding='utf-8')
                result = python('-I', '-B', isolated / 'parser.py', token_path, cwd=self.root)
                self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
                self.assertEqual(json.loads(result.stdout), expected)
                _, parser = load_frontend(generated)
                original = json.dumps(payload)
                actual = parser.parse(payload['tokens'])
                self.assertEqual(actual, expected)
                self.assertEqual(json.dumps(payload), original)
                pending = [actual]
                while pending:
                    value = pending.pop()
                    self.assertIn(type(value), (dict, list, str, int))
                    if isinstance(value, dict):
                        pending.extend(value.values())
                    elif isinstance(value, list):
                        pending.extend(value)

    def test_ac05_ac20_rv06_raw_cr_crlf_lf(self):
        generated = self.make_frontend('CR \\r\nLF \\n\nX x\n', 'S -> X\n')
        isolated = self.isolated(generated)
        lexer, _ = load_frontend(generated)
        for text, positions in [('\rx', [(1, 1), (1, 2)]),
                                ('\r\nx', [(1, 1), (1, 2), (2, 1)]),
                                ('\nx', [(1, 1), (2, 1)])]:
            with self.subTest(source=repr(text)):
                expected, errors = lexer.tokenize(text)
                self.assertEqual(errors, [])
                self.assertEqual([(t['line'], t['col']) for t in expected], positions)
                result = self.scan_cli(isolated, text)
                self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
                self.assertEqual(json.loads(result.stdout), dict(tokens=expected, errors=[]))

    def test_ac05_ac20_rv09_text_escapes_control_characters(self):
        generated = self.make_frontend('T [^z]+\n', 'S -> T\n')
        isolated = self.isolated(generated)
        source = 'a\n\t\r\b\f\v\0\x1f\x7f\\n中文\u0085\u2028'
        expected_attr = r'a\n\t\r\b\f\v\x00\x1f\x7f\\n中文\x85\u2028'
        lexer, _ = load_frontend(generated)
        tokens, errors = lexer.tokenize(source)
        self.assertEqual(errors, [])
        self.assertEqual(len(tokens), 1)
        expected_text = '1\t(1, ' + expected_attr + ')\tT\t1:1\n'
        result = self.scan_cli(isolated, source, '--text')
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.assertEqual(result.stdout, expected_text)
        self.assertEqual(lexer.tokens_text(tokens), expected_text)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertEqual(len(result.stdout.rstrip('\n').split('\t')), 4)
        result = self.scan_cli(isolated, source)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.assertEqual(json.loads(result.stdout), dict(tokens=tokens, errors=[]))
        self.assertEqual(tokens[0]['attr'], source)
        self.assertEqual(tokens[0]['lexeme'], source)

    def test_ac02_ac20_rv07_deep_standalone_json(self):
        generated = self.root / 'generated'
        result = generate(generated, 'tests/fixtures/calc.lex', 'tests/fixtures/calc.grammar')
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        isolated = self.isolated(generated)
        source = '+'.join(['1'] * 495)
        tokens = self.root / 'tokens.json'
        result = self.scan_cli(isolated, source, '-o', tokens)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        tree_file = self.root / 'ast.json'
        result = python('-I', '-B', isolated / 'parser.py', tokens, '-o', tree_file, cwd=self.root)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        # Independently validate JSON syntax and leaf order. Only this test reader
        # gets a higher decoder limit; the generated parser runs at its default.
        reader = '''import json, pathlib, sys
sys.setrecursionlimit(10000)
tree = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
pending, leaves = [tree], []
while pending:
    node = pending.pop()
    if 'lexeme' in node:
        leaves.append(node['lexeme'])
    else:
        pending.extend(reversed(node['children']))
print(json.dumps({'type': tree['type'], 'source': ''.join(leaves)}))
'''
        result = python('-I', '-B', '-c', reader, tree_file, cwd=self.root)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.assertEqual(json.loads(result.stdout), dict(type='E', source=source))
        # Compare runtime interfaces without recursive Python object equality.
        text = tree_file.read_text(encoding='utf-8')
        self.assertEqual(text.count('"type": "E"'), 495)
        self.assertEqual(text.count('"type": "+"'), 494)
        self.assertEqual(text.count('"lexeme": "1"'), 495)
        lexer, parser = load_frontend(generated)
        current_tokens, errors = lexer.tokenize(source)
        self.assertEqual(errors, [])
        tree = parser.parse(current_tokens)
        self.assertEqual(text, parser.json_text(tree))
        self.assertTrue(text.endswith('}\n'))

    def test_ac10_ac20_rv07_json_format_compatibility(self):
        generated = self.make_frontend('X x\n', 'S -> X\n')
        _, parser = load_frontend(generated)
        values = [None, True, False, 0, -17, 1.25, '中文\\\n\t"', [], {},
                  {'empty': [], 'map': {}, 'values': [1, {'中文': 'x'}, None]},
                  [[], {}, [1, 2], {'a': [False, True]}]]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(parser.json_text(value), json.dumps(value, ensure_ascii=False, indent=2) + '\n')
