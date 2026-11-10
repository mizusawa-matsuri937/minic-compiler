"""Compiler command-line driver. Source diagnostics always go to stderr."""
import argparse
import json
from pathlib import Path
import sys
from . import frontend, semantic, astviz
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
    return 0


def main():
    ap = argparse.ArgumentParser(description='mini-C compiler')
    ap.add_argument('source')
    ap.add_argument('--frontend', default='build/minic')
    ap.add_argument('--out')
    ap.add_argument('--stop-after', choices=('tokens', 'ast', 'ir'))
    args = ap.parse_args()
    try:
        return compile_source(args)
    except (OSError, UnicodeError, ValueError, ImportError, SyntaxError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
