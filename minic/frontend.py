"""Generated modules are loaded by file path, without importing ccgen."""
import importlib.util
from pathlib import Path


def load(directory):
    modules = []
    for name in ('lexer', 'parser'):
        path = Path(directory) / f'{name}.py'
        if not path.is_file():
            raise ValueError(f'缺少 {path}；请先运行 python3 -m ccgen 生成分析器')
        spec = importlib.util.spec_from_file_location('generated_' + name, path)
        module = importlib.util.module_from_spec(spec)
        # Regeneration may preserve both size and integer-second mtime. Compile
        # the current source directly rather than trusting a timestamp .pyc.
        code = compile(path.read_bytes(), str(path), 'exec')
        exec(code, module.__dict__)
        modules.append(module)
    return tuple(modules)
