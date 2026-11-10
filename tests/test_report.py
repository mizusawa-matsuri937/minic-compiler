from html.parser import HTMLParser
import json
import unittest
from support import Frontend


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class ReportReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections, self.tables = [], {}
        self.table, self.row, self.cell = None, None, None
        self.body = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section':
            self.sections.append(attrs['id'])
        elif tag == 'table':
            self.table = attrs['id']
            self.tables[self.table] = []
        elif tag == 'tbody':
            self.body = True
        elif tag == 'tr' and self.body:
            self.row = []
        elif tag == 'td':
            self.cell = ''

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag == 'td':
            self.row.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.body:
            self.tables[self.table].append(self.row)
            self.row = None
        elif tag == 'tbody':
            self.body = False
        elif tag == 'table':
            self.table = None


class ReportTests(unittest.TestCase):
    def test_ac19_complete_consistent_report(self):
        html = (frontend.frontend / 'report.html').read_text()
        for forbidden in ('<link', '<script src', 'src="http', 'href="http'):
            self.assertNotIn(forbidden, html)
        reader = ReportReader()
        reader.feed(html)
        self.assertEqual(reader.sections, ['tokens', 'automata', 'dfa', 'productions', 'first', 'lr1', 'action', 'goto', 'conflicts'])
        lex = json.loads((frontend.frontend / 'lexer_tables.json').read_text())
        parser = json.loads((frontend.frontend / 'parser_tables.json').read_text())
        self.assertEqual(dict(reader.tables['stats-table']), {k: str(v) for k, v in lex['stats'].items()})
        self.assertEqual(len(reader.tables['production-table']), 38)
        for row, production in zip(reader.tables['production-table'], parser['productions']):
            self.assertEqual(row[:3], [str(production['id']), production['lhs'], ' '.join(production['rhs']) or 'ε'])
        self.assertEqual(len(reader.tables['action-table']), parser['states'])
        self.assertEqual(len(reader.tables['goto-table']), parser['states'])
        self.assertIn(f'<p id="lr1-count">{parser["states"]}</p>', html)
        self.assertEqual(len(reader.tables['dfa-table']), lex['stats']['min_dfa_states'])
        self.assertLess(len(reader.tables['dfa-table'][0]), 128)
        self.assertEqual(dict(reader.tables['first-table']), {s: ', '.join(v) for s, v in parser['first'].items()})
        self.assertEqual(len(reader.tables['token-table']), len(lex['tokens']))
        self.assertEqual(len(reader.tables['conflict-table']), len(parser['conflicts']))
        for row in reader.tables['conflict-table']:
            self.assertEqual(row[1], 'else')
            self.assertEqual(row[-1], 'shift（移进）')
        for i, row in enumerate(reader.tables['action-table']):
            for terminal, cell in zip(parser['terminals'], row[1:]):
                action = parser['action'][str(i)].get(terminal)
                expected = '-' if action is None else ('acc' if action[0] == 'accept' else action[0][0] + str(action[1]))
                self.assertEqual(cell, expected)
        for i, row in enumerate(reader.tables['goto-table']):
            self.assertEqual(row[1:], [str(parser['goto'][str(i)].get(n, '-')) for n in parser['nonterminals']])
