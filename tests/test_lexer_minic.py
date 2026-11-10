import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from ccgen.lexspec import build_tables
from ccgen.codegen import lexer_source


class LexerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def generate(self, path):
        generated = self.path / 'lexer.py'
        generated.write_text(lexer_source(build_tables(path)), encoding='utf-8')
        spec = importlib.util.spec_from_file_location('generated_lexer', generated)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_ac05_minic_tokens(self):
        lexer = self.generate('rules/minic.lex')
        tokens, errors = lexer.tokenize(Path('tests/fixtures/lex_ok.mc').read_text())
        self.assertEqual(errors, [])
        self.assertEqual(len(tokens), 16)
        self.assertEqual([t['kind'] for t in tokens],
                         'int IDENT = NUMBER ; if ( IDENT >= NUMBER ) write ( IDENT ) ;'.split())
        self.assertEqual([(t['code'], t['attr']) for t in tokens[:4]],
                         [(1, None), (7, 'integer'), (19, None), (8, '10')])
        self.assertEqual((tokens[1]['line'], tokens[1]['col']), (1, 5))
        self.assertEqual((tokens[8]['line'], tokens[8]['col']), (2, 13))
        result = subprocess.run([sys.executable, '-I', str(self.path / 'lexer.py'),
                                 str(Path('tests/fixtures/lex_ok.mc').resolve())],
                                cwd=self.path, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(tokens=tokens, errors=[]))
        text = lexer.tokens_text(tokens).splitlines()
        self.assertEqual(len(text), 16)
        self.assertEqual(text[1], '2\t(7, integer)\tIDENT\t1:5')

    def test_ac05_fixed_and_priority(self):
        rules = self.path / 'custom.lex'
        rules.write_text('%skip WS\nWS [ \\t\\n]+\nA [a]\nB b|b\nKW if\nID [a-z]+\nGE >=\nGT >\n')
        lexer = self.generate(rules)
        tokens, errors = lexer.tokenize('a b if ifx >= >\n\tx')
        self.assertEqual(errors, [])
        self.assertEqual([t['kind'] for t in tokens], ['A', 'B', 'KW', 'ID', 'GE', 'GT', 'ID'])
        self.assertEqual([t['attr'] for t in tokens], [None, None, None, 'ifx', None, None, 'x'])
        self.assertEqual((tokens[-1]['line'], tokens[-1]['col']), (2, 2))
