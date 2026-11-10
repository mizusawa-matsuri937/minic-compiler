"""Review regressions for deep AST traversal and offline visualization."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from ccgen.report import alphabet_groups, character
from minic import astviz, irgen, semantic
from support import Frontend, python


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


def parse(source):
    tokens, errors = frontend.lexer.tokenize(source)
    if errors:
        raise AssertionError(errors)
    return frontend.parser.parse(tokens)


LONG_EXPRESSION = 'write(' + '+'.join(['1'] * 1000) + ');'
DEEP_CONTROL = ('int x=7;' + 'if(1){' * 550
                + 'int x=x+1; write(x); while(0) write(99);'
                + '}' * 550 + 'write(x);')


class ReviewAstTests(unittest.TestCase):
    def test_ac13_rv07_deep_expression_semantics(self):
        limit = sys.getrecursionlimit()
        self.assertEqual(semantic.check(parse(LONG_EXPRESSION)), [])
        self.assertEqual(sys.getrecursionlimit(), limit)

    def test_ac13_rv07_deep_control_scope(self):
        tree = parse(DEEP_CONTROL)
        self.assertEqual(semantic.check(tree), [])
        node = tree['body'][1]
        for _ in range(549):
            node = node['then']['body'][0]
        inner = node['then']['body']
        self.assertEqual(inner[0]['init']['left']['_slot'], 'x.addr')
        self.assertEqual(inner[0]['_slot'], 'x.addr.1')
        self.assertEqual(inner[1]['value']['_slot'], 'x.addr.1')
        self.assertEqual(tree['body'][-1]['value']['_slot'], 'x.addr')

    def test_ac14_rv07_ir_expression_without_semantic_gate(self):
        code = irgen.generate(parse(LONG_EXPRESSION), 'long.mc')
        self.assertEqual(code.count(' = add i32 '), 999)
        self.assertIn('%t1 = add i32 1, 1', code)
        self.assertIn('%t999 = add i32 %t998, 1', code)
        self.assertIn('@printf(ptr @.fmt.write, i32 %t999)', code)

    def test_ac14_rv07_ir_statement_without_semantic_gate(self):
        tree = parse('if(1)' * 1050 + 'while(0) write(2); else write(3);')
        code = irgen.generate(tree, 'deep.mc')
        self.assertEqual(code.count('if.then.'), 2100)
        self.assertEqual(code.count('call i32 (ptr, ...) @printf'), 2)
        self.assertIn('while.cond.1051:', code)
        self.assertIn('if.else.1050:', code)

    def test_ac18_rv07_all_deep_renderers(self):
        tree = parse(LONG_EXPRESSION)
        for render in (astviz.text_tree, astviz.layout, astviz.html_tree, astviz.dot_tree):
            with self.subTest(renderer=render.__name__):
                result = render(tree)
                if render is astviz.layout:
                    self.assertEqual(len(result[0]), 2001)
                    self.assertEqual(len(result[1]), 2000)
                elif render is astviz.html_tree:
                    self.assertEqual(result.count('class="ast-node"'), 2001)
                elif render is astviz.text_tree:
                    self.assertEqual(len(result.splitlines()), 2001)
                else:
                    self.assertEqual(result.count(' -> '), 2000)

    def test_ac20_rv07_long_pipeline_and_standalone_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'long.mc'
            source.write_text(LONG_EXPRESSION)
            out = root / 'out'
            result = frontend.compile(source, out, '--stop-after', 'ir')
            self.assertEqual(result.returncode, 0, result.stderr)
            standalone = root / 'ast.json'
            result = python('-I', '-B', frontend.frontend / 'parser.py',
                            out / 'tokens.json', '-o', standalone, cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(standalone.read_bytes(), (out / 'ast.json').read_bytes())
            for name in ('ast.json', 'ast.txt', 'ast.html', 'ast.dot', 'long.ll'):
                self.assertGreater((out / name).stat().st_size, 0)
            self.assertNotIn('_slot', standalone.read_text())

    @unittest.skipUnless(shutil.which('clang'), 'clang is required for execution')
    def test_ac16_rv07_long_expression_and_nested_control_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, source, expected in [('long', LONG_EXPRESSION, '1000\n'),
                                           ('deep', DEEP_CONTROL, '8\n7\n')]:
                with self.subTest(program=name):
                    path = root / (name + '.mc')
                    path.write_text(source)
                    result = frontend.compile(path, root / name, '-O0', '--run')
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, expected)

    def test_ac18_rv08_actual_glyph_measurement_and_full_labels(self):
        name = 'a' * 200
        page = astviz.html_tree(parse(f'int {name}; write({name}+{name});'))
        svg = ET.fromstring(page[page.index('<svg'):page.index('</svg>') + 6])
        labels = [g.find('{*}text').text for g in svg.findall('{*}g')]
        self.assertEqual(labels.count('Identifier ' + name), 2)
        self.assertIn('VarDecl ' + name, labels)
        for forbidden in ('<link', '<script src', 'src="http', 'href="http'):
            self.assertNotIn(forbidden, page)
        # The browser must use actual glyph bounds; estimated rectangles alone
        # cannot establish that text is contained. Browser evidence checks geometry.
        self.assertIn('getBBox()', page)
        self.assertIn('document.fonts.ready', page)

    def test_ac19_rv10_visible_space_preserves_dfa_groups(self):
        self.assertTrue(character(32).strip(), 'SPACE header must be visible')
        self.assertIn('SPACE', character(32))
        data = json.loads((frontend.frontend / 'lexer_tables.json').read_text())
        groups = alphabet_groups(data)
        self.assertEqual(sum(hi - lo + 1 for lo, hi, _ in groups), 128)
        for lo, hi, signature in groups:
            for code in range(lo, hi + 1):
                expected = tuple(data['trans'][str(state)].get(chr(code))
                                 for state in range(data['stats']['min_dfa_states']))
                self.assertEqual(signature, expected)
        page = (frontend.frontend / 'report.html').read_text()
        self.assertIn('<th>SPACE (U+0020)</th>', page)
