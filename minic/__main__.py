"""Compiler command-line driver. Source diagnostics always go to stderr."""
import argparse
import json
from pathlib import Path
import sys
from . import frontend, semantic, astviz, irgen, backend
from .diagnostics import emit, parse_diagnostic


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def clean_outputs(out, stem):
    for name in ['tokens.txt', 'tokens.json', 'ast.json', 'ast.txt', 'ast.html', 'ast.dot',
                 stem + '.ll', stem + '.opt.ll', stem + '.s', stem, stem + '.exe']:
        path = out / name
        if path.is_file() or path.is_symlink():
            path.unlink()


def compile_source(args):
    source = Path(args.source)
    text = source.read_text(encoding='utf-8')
    lexer, parser = frontend.load(args.frontend)
    out = Path(args.out or Path('out') / source.stem)
    out.mkdir(parents=True, exist_ok=True)
    clean_outputs(out, source.stem)
    tokens, errors = lexer.tokenize(text)
    (out / 'tokens.json').write_text(json_text(dict(tokens=tokens, errors=errors)), encoding='utf-8')
    (out / 'tokens.txt').write_text(lexer.tokens_text(tokens), encoding='utf-8')
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
    (out / 'ast.json').write_text(json_text(tree), encoding='utf-8')
    astviz.write(tree, out)
    if args.stop_after == 'ast':
        return 0
    errors = semantic.check(tree)
    if errors:
        emit(args.source, errors)
        return 1
    ir = out / (source.stem + '.ll')
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
