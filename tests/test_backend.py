from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from minic import backend
from support import Frontend, run


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    @unittest.skipUnless(shutil.which('clang'), 'clang 不在 PATH 中，AC15 未验证')
    def test_ac15_demo_optimization_equivalence(self):
        results = []
        for level in (0, 2):
            out = self.root / f'O{level}'
            result = frontend.compile('examples/demo.mc', out, f'-O{level}')
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ('demo.opt.ll', 'demo.s', 'demo'):
                self.assertTrue((out / name).is_file())
                self.assertGreater((out / name).stat().st_size, 0)
            output = []
            for stdin, expected in [('5\n', '15\n120\n1\n'), ('10\n', '55\n3628800\n0\n')]:
                execution = run(out / 'demo', input=stdin)
                self.assertEqual(execution.returncode, 0, execution.stderr)
                self.assertEqual(execution.stdout, expected)
                output.append(execution.stdout)
            results.append(output)
        self.assertEqual(results[0], results[1])
        # Backend text also stays stable when the output directory changes.
        result = frontend.compile('examples/demo.mc', self.root / 'again', '-O2')
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ('demo.opt.ll', 'demo.s'):
            self.assertEqual((self.root / 'O2' / name).read_bytes(), (self.root / 'again' / name).read_bytes())

    @unittest.skipUnless(shutil.which('clang'), 'clang 不在 PATH 中，AC15 --run 未验证')
    def test_ac15_run_forwards_stdio(self):
        from support import python
        result = python('-m', 'minic', 'examples/demo.mc', '--frontend', frontend.frontend,
                        '--out', self.root, '--run', input='5\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '15\n120\n1\n')

    def test_ac17_missing_clang_keeps_frontend(self):
        result = frontend.compile('examples/demo.mc', self.root, '--clang', '/nonexistent/clang')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn('无法运行 clang', result.stderr)
        self.assertEqual({p.name for p in self.root.iterdir()},
                         {'tokens.txt', 'tokens.json', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot', 'demo.ll'})

    def test_ac17_failed_clang_keeps_frontend(self):
        tool = self.root / 'failing-clang'
        tool.write_text(f'#!{sys.executable}\nimport sys\nprint("test clang diagnostic", file=sys.stderr)\nsys.exit(7)\n')
        tool.chmod(0o755)
        out = self.root / 'compiled'
        result = frontend.compile('examples/demo.mc', out, '--clang', str(tool))
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn('test clang diagnostic', result.stderr)
        self.assertIn('退出码 7', result.stderr)
        self.assertTrue((out / 'demo.ll').is_file())
        self.assertFalse((out / 'demo').exists())

    def test_ac17_clang_commands(self):
        ir = self.root / 'source.ll'
        ir.write_text('')
        with patch('minic.backend.subprocess.run', return_value=subprocess.CompletedProcess([], 0, '', '')) as mocked:
            backend.build(ir, 1, 'clang')
        self.assertEqual([c.args[0] for c in mocked.call_args_list], [
            ['clang', '-Wno-override-module', '-O1', '-S', '-emit-llvm', 'source.ll', '-o', 'source.opt.ll'],
            ['clang', '-Wno-override-module', '-O1', '-S', 'source.ll', '-o', 'source.s'],
            ['clang', '-Wno-override-module', '-O1', 'source.ll', '-o', 'source'],
        ])


@unittest.skipUnless(shutil.which('clang'), 'clang 不在 PATH 中，AC16 运行语义未验证')
class RuntimeTests(unittest.TestCase):
    def check_program(self, name, expected, stdin=None):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            source = 'tests/fixtures/dangling_else.mc' if name == 'dangling_else' else f'tests/fixtures/run/{name}.mc'
            for optimization in (0, 2):
                result = frontend.compile(source, out, f'-O{optimization}')
                self.assertEqual(result.returncode, 0, result.stderr)
                execution = run(out / name, input=stdin)
                self.assertEqual(execution.returncode, 0, execution.stderr)
                self.assertEqual(execution.stdout, expected)

    def test_ac16_arith(self):
        self.check_program('arith', '3\n-3\n-3\n14\n20\n5\n')

    def test_ac16_rel(self):
        self.check_program('rel', '1\n0\n1\n0\n1\n0\n1\n')

    def test_ac16_scope(self):
        self.check_program('scope', '2\n1\n1\n0\n')

    def test_ac16_control(self):
        self.check_program('control', '0\n100\n2\n3\n')

    def test_ac16_wrap(self):
        self.check_program('wrap', '-2147483648\n')

    def test_ac16_io(self):
        self.check_program('io', '13\n', '3 -10\n')

    def test_ac16_dangling_else(self):
        self.check_program('dangling_else', '2\n')
