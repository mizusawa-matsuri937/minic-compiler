import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from minic.astviz import html_tree
from support import Frontend


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class VisualizationTests(unittest.TestCase):
    def test_ac18_offline_svg_and_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            result = frontend.compile('examples/demo.mc', out, '--stop-after', 'ast')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({p.name for p in out.iterdir()},
                             {'tokens.json', 'tokens.txt', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot'})
            tree = json.loads((out / 'ast.json').read_text())
            def count(value):
                if isinstance(value, dict):
                    return int('type' in value) + sum(count(v) for v in value.values())
                if isinstance(value, list):
                    return sum(count(v) for v in value)
                return 0
            html = (out / 'ast.html').read_text()
            self.assertEqual(html.count('<svg'), 1)
            for forbidden in ('<link', '<script src', 'src="http', 'href="http'):
                self.assertNotIn(forbidden, html)
            self.assertEqual(html.count('class="ast-node"'), count(tree))
            svg = ET.fromstring(html[html.index('<svg'):html.index('</svg>') + 6])
            ns = {'s': 'http://www.w3.org/2000/svg'}
            groups = svg.findall('s:g', ns)
            self.assertEqual(len(groups), count(tree))
            self.assertEqual(groups[0].find('s:text', ns).text, 'Program')
            rects = [g.find('s:rect', ns) for g in groups]
            boxes = [tuple(float(r.attrib[k]) for k in ('x', 'y', 'width', 'height')) for r in rects]
            for i, (x, y, w, h) in enumerate(boxes):
                for xx, yy, ww, hh in boxes[i + 1:]:
                    self.assertFalse(x < xx + ww and xx < x + w and y < yy + hh and yy < y + h)
            self.assertEqual(len(svg.findall('s:line', ns)), count(tree) - 1)
            fields = [text.text for text in svg.findall('s:text', ns)]
            self.assertIn('body[0]', fields)
            self.assertIn('cond', fields)
            self.assertTrue((out / 'ast.txt').read_text().startswith('Program\n'))
            self.assertIn('├── body[0]: VarDecl n', (out / 'ast.txt').read_text())
            self.assertTrue((out / 'ast.dot').read_text().startswith('digraph AST {'))

    def test_ac18_html_escaping(self):
        tree = {'type': 'BinaryOp', 'line': 1, 'col': 1, 'op': '<&"'}
        html = html_tree(tree)
        self.assertIn('&lt;&amp;&quot;', html)
        svg = ET.fromstring(html[html.index('<svg'):html.index('</svg>') + 6])
        self.assertEqual(svg.find('{*}g/{*}text').text, 'BinaryOp <&"')
