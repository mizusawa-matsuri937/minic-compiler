import json
from pathlib import Path
import tempfile
import unittest
from support import Frontend, generate, load


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class ParsegenTests(unittest.TestCase):
    def test_ac02_language_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            result = generate(out, 'tests/fixtures/calc.lex', 'tests/fixtures/calc.grammar')
            self.assertEqual(result.returncode, 0, result.stderr)
            lexer = load(out / 'lexer.py', 'calc_lexer')
            parser = load(out / 'parser.py', 'calc_parser')
            tokens, errors = lexer.tokenize('1+2*3')
            self.assertEqual(errors, [])
            tree = parser.parse(tokens)
            self.assertEqual(tree['type'], 'E')
            self.assertEqual([c['type'] for c in tree['children']], ['E', '+', 'T'])
            self.assertEqual([c['type'] for c in tree['children'][2]['children']], ['T', '*', 'F'])
            def leaves(node):
                if 'lexeme' in node:
                    return [node['lexeme']]
                return [v for c in node['children'] for v in leaves(c)]
            self.assertEqual(leaves(tree), ['1', '+', '2', '*', '3'])

    def test_ac07_productions_first_conflicts(self):
        tables = json.loads((frontend.frontend / 'parser_tables.json').read_text())
        expected = '''S -> Program
Program -> StatementList
StatementList -> Statement StatementList
StatementList ->
Statement -> VarDecl
Statement -> AssignStmt
Statement -> IfStmt
Statement -> WhileStmt
Statement -> ReadStmt
Statement -> WriteStmt
Statement -> CompoundStmt
VarDecl -> int IDENT ;
VarDecl -> int IDENT = Expr ;
AssignStmt -> IDENT = Expr ;
CompoundStmt -> { StatementList }
IfStmt -> if ( Expr ) Statement
IfStmt -> if ( Expr ) Statement else Statement
WhileStmt -> while ( Expr ) Statement
ReadStmt -> read ( IDENT ) ;
WriteStmt -> write ( Expr ) ;
Expr -> RelExpr
RelExpr -> AddExpr < AddExpr
RelExpr -> AddExpr > AddExpr
RelExpr -> AddExpr == AddExpr
RelExpr -> AddExpr != AddExpr
RelExpr -> AddExpr <= AddExpr
RelExpr -> AddExpr >= AddExpr
RelExpr -> AddExpr
AddExpr -> AddExpr + Term
AddExpr -> AddExpr - Term
AddExpr -> Term
Term -> Term * Factor
Term -> Term / Factor
Term -> Factor
Factor -> IDENT
Factor -> NUMBER
Factor -> ( Expr )'''
        self.assertEqual(len(tables['productions']), 38)
        self.assertEqual(tables['productions'][0]['rhs'], ['S'])
        self.assertEqual(tables['productions'][0]['id'], 0)
        for i, line in enumerate(expected.splitlines(), 1):
            lhs, rhs = line.split(' ->')
            production = tables['productions'][i]
            self.assertEqual((production['id'], production['lhs'], production['rhs']), (i, lhs, rhs.split()))
        self.assertEqual(len(tables['first']), 16)
        self.assertEqual(set(tables['first']['Expr']), {'IDENT', 'NUMBER', '('})
        self.assertGreater(len(tables['conflicts']), 0)
        for conflict in tables['conflicts']:
            self.assertEqual((conflict['lookahead'], conflict['reduce'], conflict['kind'], conflict['resolution']),
                             ('else', 16, 'shift-reduce', 'shift'))
            self.assertIsInstance(conflict['shift'], int)

    def test_ac07_nullable_start(self):
        # Nullable chains exercise FIRST(beta a) and empty-stack reductions.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            grammar = root / 'empty.grammar'
            grammar.write_text('S -> A B\nA -> %empty\nB -> num\nB -> ε\n')
            result = generate(root / 'gen', 'tests/fixtures/calc.lex', grammar)
            self.assertEqual(result.returncode, 0, result.stderr)
            parser = load(root / 'gen/parser.py', 'nullable_parser')
            self.assertEqual(parser.parse([])['type'], 'S')
            tables = json.loads((root / 'gen/parser_tables.json').read_text())
            self.assertEqual(set(tables['first']['S']), {'num', 'ε'})
