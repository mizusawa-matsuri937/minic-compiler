"""Acceptance regressions for T1-07 (CR01/CR02). Browser geometry is separate."""
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest

from support import Frontend, ROOT, python


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class PageStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = {}
        self.buttons = {}
        self.button = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.setdefault(attrs['id'], []).append((tag, attrs))
        if tag == 'button':
            self.button = attrs.get('id')
            self.buttons[self.button] = ''

    def handle_data(self, data):
        if self.button is not None:
            self.buttons[self.button] += data

    def handle_endtag(self, tag):
        if tag == 'button':
            self.button = None


class ReviewCRTests(unittest.TestCase):
    def test_ac23_leading_bom_is_ignored_by_both_file_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'leading.mc'
            source.write_bytes(b'\xef\xbb\xbfint a = 1;\nwrite(a);\n')
            out = root / 'compiled'
            compiled = frontend.compile(source, out, '--stop-after', 'ast')
            standalone = python('-I', frontend.frontend / 'lexer.py', source,
                                '-o', root / 'tokens.json', cwd=root)
            self.assertFalse(root.is_relative_to(ROOT))
            for result in (compiled, standalone):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
            tokens = json.loads((out / 'tokens.json').read_text(encoding='utf-8'))
            self.assertEqual(tokens['errors'], [])
            self.assertEqual(len(tokens['tokens']), 10)
            first = tokens['tokens'][0]
            self.assertEqual((first['kind'], first['line'], first['col']), ('int', 1, 1))
            self.assertEqual((root / 'tokens.json').read_bytes(), (out / 'tokens.json').read_bytes())
            self.assertEqual(json.loads((out / 'ast.json').read_text(encoding='utf-8'))['type'], 'Program')

    def check_illegal_bom(self, payload, line, col):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'illegal.mc'
            source.write_bytes(payload)
            out = root / 'compiled'
            compiled = frontend.compile(source, out, '--stop-after', 'ast')
            standalone = python('-I', frontend.frontend / 'lexer.py', source,
                                '-o', root / 'tokens.json', cwd=root)
            for result in (compiled, standalone):
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stderr.splitlines(),
                                 [f"{source}:{line}:{col}: 词法错误[L001]: 非法字符 '\\ufeff'"])
            self.assertEqual((root / 'tokens.json').read_bytes(), (out / 'tokens.json').read_bytes())
            data = json.loads((out / 'tokens.json').read_text(encoding='utf-8'))
            self.assertEqual(len(data['errors']), 1)
            self.assertEqual(len(data['tokens']), 10)
            self.assertEqual({p.name for p in out.iterdir()}, {'tokens.json', 'tokens.txt'})

    def test_ac23_interior_bom_remains_a_lexical_error(self):
        self.check_illegal_bom(b'int a = 1;\n\xef\xbb\xbfwrite(a);\n', 2, 1)

    def test_ac23_only_one_initial_bom_is_removed(self):
        self.check_illegal_bom(b'\xef\xbb\xbf\xef\xbb\xbfint a = 1;\nwrite(a);\n', 1, 1)

    def test_ac24_controls_offline_nodes_and_deterministic_html(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / 'first', Path(directory) / 'second'
            for out in (first, second):
                result = frontend.compile('examples/demo.mc', out, '--stop-after', 'ast')
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((first / 'ast.html').read_bytes(), (second / 'ast.html').read_bytes())
            html = (first / 'ast.html').read_text(encoding='utf-8')
            page = PageStructure()
            page.feed(html)
            self.assertIn('ast-tree', page.ids)
            self.assertEqual(len(page.ids['ast-tree']), 1)
            self.assertEqual(page.ids['ast-tree'][0][0], 'div')
            for name, label, pressed in [('ast-fit', '适应宽度', 'false'),
                                         ('ast-actual', '原始大小', 'true')]:
                self.assertIn(name, page.ids)
                self.assertEqual(len(page.ids[name]), 1)
                tag, attrs = page.ids[name][0]
                self.assertEqual((tag, attrs.get('type')), ('button', 'button'))
                self.assertEqual(attrs.get('aria-pressed'), pressed)
                self.assertEqual(page.buttons[name], label)
            self.assertEqual(html.count('<svg'), 1)
            for forbidden in ('<link', '<script src', 'src="http', 'href="http'):
                self.assertNotIn(forbidden, html)
            pending = [json.loads((first / 'ast.json').read_text(encoding='utf-8'))]
            count = 0
            while pending:
                value = pending.pop()
                if isinstance(value, dict):
                    count += 'type' in value
                    pending.extend(value.values())
                elif isinstance(value, list):
                    pending.extend(value)
            self.assertEqual(html.count('class="ast-node"'), count)
