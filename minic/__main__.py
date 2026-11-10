"""Compiler command-line driver. Source diagnostics always go to stderr."""
import argparse
import json
from pathlib import Path
import sys
from . import frontend, semantic, astviz, irgen, backend
from .diagnostics import emit, parse_diagnostic


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def plan_outputs(out, stem):
    """Reserve fixed stage names, then select one stable backend basename."""
    paths = {name: out / name for name in
             ('tokens.txt', 'tokens.json', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot')}
    reserved = {name.casefold() for name in paths}
    original_stem = stem
    while True:
        ir = out / (stem + '.ll')
        generated = dict(ir=ir, **backend.output_paths(ir))
        # Include both executable spellings in cleanup, as in earlier releases.
        cleanup = list(dict.fromkeys([*generated.values(), out / stem, out / (stem + '.exe')]))
        if not any(path.name.casefold() in reserved for path in cleanup):
            break
        stem += '.program'
    paths.update(generated)
    # Remove previous-release filenames too, after the same input/alias checks.
    legacy_ir = out / (original_stem + '.ll')
    legacy = [legacy_ir, *backend.output_paths(legacy_ir).values(),
              out / original_stem, out / (original_stem + '.exe')]
    return paths, list(dict.fromkeys([*paths.values(), *cleanup, *legacy]))


def same_path(left, right):
    """Resolve lexical/symlink aliases and compare existing hard-link identities."""
    if left.resolve() == right.resolve():
        return True
    try:
        return left.samefile(right)
    except FileNotFoundError:
        return False


def validate_outputs(outputs, inputs, *, distinct=True):
    """Reject the whole operation before loading, removing or writing any files."""
    for index, path in enumerate(outputs):
        if path.exists() and not path.is_file():
            raise ValueError(f'路径冲突：输出 {path} 不是普通文件')
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError(f'路径冲突：输出目录 {parent} 不是目录')
        resolved = path.resolve()
        for other in [*inputs, *(outputs[:index] if distinct else [])]:
            other_resolved = other.resolve()
            if (same_path(path, other) or resolved in other_resolved.parents
                    or other_resolved in resolved.parents):
                raise ValueError(f'路径冲突：输出 {path} 与 {other} 不能共存')


def clean_outputs(outputs):
    for path in outputs:
        if path.is_file() or path.is_symlink():
            path.unlink()


def compile_source(args):
    source = Path(args.source)
    out = Path(args.out or Path('out') / source.stem)
    paths, cleanup = plan_outputs(out, source.stem)
    inputs = [source, *(Path(args.frontend) / name for name in ('lexer.py', 'parser.py'))]
    validate_outputs(list(paths.values()), inputs)
    # Historical cleanup spellings may alias a current output on a case-insensitive
    # filesystem. They are not distinct stage outputs, but still protect all inputs.
    validate_outputs(cleanup, inputs, distinct=False)
    with source.open(encoding='utf-8', newline='') as stream:
        text = stream.read()
    lexer, parser = frontend.load(args.frontend)
    out.mkdir(parents=True, exist_ok=True)
    clean_outputs(cleanup)
    tokens, errors = lexer.tokenize(text)
    paths['tokens.json'].write_text(json_text(dict(tokens=tokens, errors=errors)), encoding='utf-8')
    paths['tokens.txt'].write_text(lexer.tokens_text(tokens), encoding='utf-8')
    if errors:
        emit(args.source, errors)
        return 1
    if args.stop_after == 'tokens':
        return 0
    try:
        tree = parser.parse(tokens)
    except parser.ParseError as error:
        emit(args.source, [parse_diagnostic(error)])
        return 1
    paths['ast.json'].write_text(parser.json_text(tree), encoding='utf-8')
    astviz.write(tree, out)
    if args.stop_after == 'ast':
        return 0
    errors = semantic.check(tree)
    if errors:
        emit(args.source, errors)
        return 1
    ir = paths['ir']
    ir.write_text(irgen.generate(tree, source.name), encoding='utf-8')
    if args.stop_after == 'ir':
        return 0
    executable = backend.build(ir, args.O, args.clang)
    for path in sorted(out.iterdir()):
        if path.is_file():
            print(path, file=sys.stderr)
    return backend.run(executable) if args.run else 0


def main():
    ap = argparse.ArgumentParser(description='mini-C compiler')
    ap.add_argument('source')
    ap.add_argument('--frontend', default='build/minic')
    ap.add_argument('--out')
    ap.add_argument('--stop-after', choices=('tokens', 'ast', 'ir'))
    ap.add_argument('-O', type=int, choices=(0, 1, 2, 3), default=2)
    ap.add_argument('--clang', default='clang')
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    if args.run and args.stop_after:
        ap.error('--run 不能与 --stop-after 一起使用')
    try:
        return compile_source(args)
    except backend.BackendError as error:
        print(f'后端错误: {error}', file=sys.stderr)
        return 3
    except (OSError, UnicodeError, ValueError, ImportError, SyntaxError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
