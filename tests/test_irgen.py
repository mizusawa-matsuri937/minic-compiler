from pathlib import Path
import re
import tempfile
import unittest
from support import Frontend


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class IRTests(unittest.TestCase):
    def test_ac14_ir_features_and_determinism(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('one', 'two'):
                result = frontend.compile('examples/demo.mc', root / name, '--stop-after', 'ir',
                                          '--clang', '/nonexistent/clang')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse((root / name / 'demo').exists())
                self.assertFalse((root / name / 'demo.opt.ll').exists())
            ir = (root / 'one/demo.ll').read_text()
            self.assertIn('define i32 @main()', ir)
            self.assertEqual(ir.count('alloca i32'), 4)
            self.assertEqual(ir.split('entry:\n', 1)[1].split('  br ', 1)[0].count('alloca i32'), 4)
            for instruction in ['icmp sle', 'icmp eq', 'mul i32', 'sdiv i32', 'sub i32', 'add i32']:
                self.assertIn(instruction, ir)
            self.assertNotIn('nsw', ir)
            self.assertNotIn('nuw', ir)
            self.assertEqual(len(re.findall(r'call .*@scanf\(', ir)), 1)
            self.assertEqual(len(re.findall(r'call .*@printf\(', ir)), 4)
            self.assertRegex(ir, r'while\.cond\.\d+:')
            self.assertRegex(ir, r'br i1 %t\d+, label %while\.body\.\d+, label %while\.end\.\d+')
            self.assertRegex(ir, r'br i1 %t\d+, label %if\.then\.\d+, label %if\.else\.\d+')
            self.assertTrue(ir.endswith('  ret i32 0\n}\n'))
            for name in ['tokens.json', 'tokens.txt', 'ast.json', 'ast.html', 'ast.txt', 'ast.dot', 'demo.ll']:
                self.assertEqual((root / 'one' / name).read_bytes(), (root / 'two' / name).read_bytes())
