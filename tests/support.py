"""All generated analyzers and compiled artifacts live in TemporaryDirectory."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, input=None, env=None):
    return subprocess.run([str(a) for a in args], cwd=cwd, input=input, env=env,
                          capture_output=True, text=True, timeout=30)


def python(*args, **kwargs):
    return run(sys.executable, *args, **kwargs)


def generate(out, lex='rules/minic.lex', grammar='rules/minic.grammar'):
    return python('-m', 'ccgen', '--lex', lex, '--grammar', grammar, '--out', out)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Frontend:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.frontend = self.root / 'frontend'
        result = generate(self.frontend)
        if result.returncode:
            self.temp.cleanup()
            raise RuntimeError(result.stderr)
        self.lexer = load(self.frontend / 'lexer.py', 'test_generated_lexer')
        self.parser = load(self.frontend / 'parser.py', 'test_generated_parser')

    def cleanup(self):
        self.temp.cleanup()

    def compile(self, source, out, *options):
        return python('-m', 'minic', source, '--frontend', self.frontend, '--out', out, *options)
