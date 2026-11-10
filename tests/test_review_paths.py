"""Input protection and complete artifact preservation at CLI boundaries."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from support import Frontend, python


def setUpModule():
    global frontend
    frontend = Frontend()


def tearDownModule():
    frontend.cleanup()


class ReviewPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def compile(self, source, out, *options, selected=None):
        return python('-m', 'minic', source, '--frontend', selected or frontend.frontend,
                      '--out', out, *options)

    def assert_rejected_unchanged(self, source, out, protected, selected=None):
        before = {path: path.read_bytes() for path in protected}
        result = self.compile(source, out, '--stop-after', 'tokens', selected=selected)
        observed = {str(path): 'unchanged' if path.exists() and path.read_bytes() == before[path]
                    else 'changed' if path.exists() else 'missing' for path in protected}
        self.assertEqual(result.returncode, 2,
                         f'expected conflict rejection; got {result.returncode}; '
                         f'stderr={result.stderr!r}; protected_after={observed!r}')
        self.assertIn('路径冲突', result.stderr)
        for path, content in before.items():
            self.assertTrue(path.exists(), f'deleted input: {path}')
            self.assertEqual(path.read_bytes(), content, f'changed input: {path}')

    def test_ac06_rv01_source_in_output_is_preserved(self):
        for alias in ('direct', 'directory_symlink', 'source_symlink', 'hardlink'):
            with self.subTest(alias=alias):
                base = self.root / alias
                base.mkdir()
                out = base / 'outputs'
                out.mkdir()
                source = out / 'demo'
                source.write_text('write(1);\n', encoding='utf-8')
                sentinel = out / 'tokens.txt'
                sentinel.write_text('previous output', encoding='utf-8')
                if alias == 'directory_symlink':
                    link = base / 'alias'
                    link.symlink_to(out, target_is_directory=True)
                    out = link / '..' / 'alias'
                elif alias == 'source_symlink':
                    link = base / 'demo'
                    link.symlink_to(source)
                    source = link
                elif alias == 'hardlink':
                    external = base / 'external.mc'
                    os.link(source, external)
                    (out / 'tokens.json').hardlink_to(external)
                    source = external
                self.assert_rejected_unchanged(source, out, [source, sentinel])

    def test_ac20_rv01_selected_analyzers_are_preserved(self):
        for name in ('lexer', 'parser'):
            with self.subTest(analyzer=name):
                selected = self.root / name
                shutil.copytree(frontend.frontend, selected)
                source = self.root / f'{name}.py.mc'
                source.write_text('write(1);\n', encoding='utf-8')
                sentinel = selected / 'tokens.txt'
                sentinel.write_text('previous output', encoding='utf-8')
                self.assert_rejected_unchanged(source, selected,
                                               [source, selected / f'{name}.py', sentinel], selected)

    def test_ac20_rv01_analyzer_alias_is_preserved(self):
        selected = self.root / 'frontend'
        shutil.copytree(frontend.frontend, selected)
        source = self.root / 'input.mc'
        source.write_text('write(1);\n', encoding='utf-8')
        out = self.root / 'outputs'
        out.mkdir()
        (out / 'ast.json').symlink_to(selected / 'parser.py')
        sentinel = out / 'tokens.txt'
        sentinel.write_text('previous output', encoding='utf-8')
        self.assert_rejected_unchanged(source, out, [source, selected / 'parser.py', sentinel], selected)

    def test_ac18_rv01_output_aliases_rejected_before_cleanup(self):
        source = self.root / 'input.mc'
        source.write_text('write(1);\n', encoding='utf-8')
        out = self.root / 'outputs'
        out.mkdir()
        tokens = out / 'tokens.json'
        tokens.write_text('previous output', encoding='utf-8')
        (out / 'ast.json').hardlink_to(tokens)
        self.assert_rejected_unchanged(source, out, [source, tokens, out / 'ast.json'])

    def test_ac06_rv01_output_parent_conflict_precedes_cleanup(self):
        out = self.root / 'outputs'
        out.mkdir()
        directory = out / 'ast.json'
        directory.mkdir()
        source = directory / 'input.mc'
        source.write_text('write(1);\n', encoding='utf-8')
        sentinel = out / 'tokens.txt'
        sentinel.write_text('previous output', encoding='utf-8')
        self.assert_rejected_unchanged(source, out, [source, sentinel])

    def test_ac06_ac14_rv04_case_variant_repeated_cleanup(self):
        source = self.root / 'AST.JSON.mc'
        source.write_text('write(1);\n', encoding='utf-8')
        out = self.root / 'outputs'
        for attempt in range(2):
            result = self.compile(source, out, '--stop-after', 'ir')
            self.assertEqual(result.returncode, 0, f'attempt={attempt}: {result.stderr}')
            self.assertEqual(json.loads((out / 'ast.json').read_text())['type'], 'Program')
            self.assertTrue((out / 'AST.JSON.program.ll').is_file())
        source.write_text('@', encoding='utf-8')
        result = self.compile(source, out)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual({path.name for path in out.iterdir()}, {'tokens.txt', 'tokens.json'})

    @unittest.skipUnless(shutil.which('clang'), 'clang 不在 PATH 中，RV04 完整编译未验证')
    def test_ac15_ac18_rv04_reserved_stems_preserve_all_artifacts(self):
        fixed = {'tokens.txt', 'tokens.json', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot'}
        for stem in sorted(fixed):
            with self.subTest(stem=stem):
                source = self.root / f'{stem}.mc'
                source.write_text('write(1);\n', encoding='utf-8')
                out = self.root / f'{stem}-outputs'
                result = self.compile(source, out, '--run')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, '1\n')
                # Verify data before naming: the original bug reports success but replaces JSON.
                for name in ('tokens.json', 'ast.json'):
                    data = (out / name).read_bytes()
                    self.assertTrue(data.startswith(b'{'), f'{name} overwritten: {data[:16].hex()}')
                    json.loads(data)
                self.assertIn('<svg', (out / 'ast.html').read_text(encoding='utf-8'))
                self.assertIn('digraph', (out / 'ast.dot').read_text(encoding='utf-8'))
                self.assertIn('Program', (out / 'ast.txt').read_text(encoding='utf-8'))
                self.assertIn('NUMBER', (out / 'tokens.txt').read_text(encoding='utf-8'))
                backend_stem = stem + '.program'
                expected = fixed | {backend_stem + suffix for suffix in
                                    ('.ll', '.opt.ll', '.s', '.exe' if os.name == 'nt' else '')}
                self.assertEqual({path.name for path in out.iterdir()}, expected)

    @unittest.skipUnless(shutil.which('clang'), 'clang 不在 PATH 中，RV05 完整编译未验证')
    def test_ac14_ac15_rv05_option_like_names_and_determinism(self):
        for stem in ('-demo', '@demo'):
            with self.subTest(stem=stem):
                source = self.root / f'{stem}.mc'
                source.write_text('write(1);\n', encoding='utf-8')
                outputs = [self.root / (stem + suffix) for suffix in ('-one', '-two')]
                for out in outputs:
                    result = self.compile(source, out, '--run')
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, '1\n')
                for name in ('tokens.json', 'ast.json', 'ast.html', stem + '.ll',
                             stem + '.opt.ll', stem + '.s'):
                    self.assertEqual((outputs[0] / name).read_bytes(), (outputs[1] / name).read_bytes())

    def test_ac06_ac17_rv01_rv04_stale_cleanup_remains_precise(self):
        source = self.root / 'tokens.json.mc'
        source.write_text('@ $', encoding='utf-8')
        out = self.root / 'outputs'
        out.mkdir()
        for name in ('tokens.txt', 'tokens.json', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot',
                     'tokens.json.program.ll', 'tokens.json.program.opt.ll',
                     'tokens.json.program.s', 'tokens.json.program', 'tokens.json.program.exe',
                     'tokens.json.ll', 'tokens.json.opt.ll', 'tokens.json.s', 'tokens.json.exe'):
            (out / name).write_text('stale', encoding='utf-8')
        (out / 'unrelated.txt').write_text('keep', encoding='utf-8')
        result = self.compile(source, out)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual({path.name for path in out.iterdir()}, {'tokens.txt', 'tokens.json', 'unrelated.txt'})
        self.assertEqual((out / 'unrelated.txt').read_text(), 'keep')
        self.assertEqual(len(json.loads((out / 'tokens.json').read_text())['errors']), 2)

    def test_ac13_ac20_rv06_cr_positions_match_api(self):
        source = self.root / 'carriage.mc'
        text = 'int x;\rwrite(y);'
        source.write_bytes(text.encode('utf-8'))
        expected_tokens, expected_errors = frontend.lexer.tokenize(text)
        out = self.root / 'outputs'
        result = self.compile(source, out, '--stop-after', 'ir')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(':1:14: 语义错误[S001]', result.stderr)
        self.assertEqual(json.loads((out / 'tokens.json').read_text(encoding='utf-8')),
                         {'tokens': expected_tokens, 'errors': expected_errors})
