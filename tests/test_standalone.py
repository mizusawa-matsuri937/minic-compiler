from pathlib import Path
import tempfile
import unittest
from support import Frontend, ROOT, python


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class StandaloneTests(unittest.TestCase):
    def test_ac20_isolated_cli_byte_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = root / 'compiled'
            result = frontend.compile('examples/demo.mc', expected, '--stop-after', 'ast')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(root.is_relative_to(ROOT))
            result = python('-I', frontend.frontend / 'lexer.py', ROOT / 'examples/demo.mc', '-o',
                            root / 'tokens.json', cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = python('-I', frontend.frontend / 'parser.py', root / 'tokens.json', '-o',
                            root / 'ast.json', cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ('tokens.json', 'ast.json'):
                self.assertEqual((root / name).read_bytes(), (expected / name).read_bytes())

    def test_ac20_refuses_lexical_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = python('-I', frontend.frontend / 'lexer.py', ROOT / 'tests/fixtures/lex_error.mc',
                            '-o', root / 'tokens.json', cwd=root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(len(result.stderr.splitlines()), 2)
            result = python('-I', frontend.frontend / 'parser.py', root / 'tokens.json', '-o',
                            root / 'ast.json', cwd=root)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((root / 'ast.json').exists())
