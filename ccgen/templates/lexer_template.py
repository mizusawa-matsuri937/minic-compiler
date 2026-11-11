"""Standalone maximal-munch scanner; tables are prepended by the generator."""
import argparse
import json
import sys
from pathlib import Path


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def tokens_text(tokens):
    return ''.join(f"{i}\t({t['code']}, {escape_attr(t['attr']) if t['attr'] is not None else '-'})"
                   f"\t{t['kind']}\t{t['line']}:{t['col']}\n" for i, t in enumerate(tokens, 1))


def escape_attr(value):
    """Keep each token on one line with exactly four tab-separated columns."""
    escapes = {'\\': r'\\', '\n': r'\n', '\r': r'\r', '\t': r'\t',
               '\b': r'\b', '\f': r'\f', '\v': r'\v'}
    parts = []
    for char in value:
        if char in escapes:
            parts.append(escapes[char])
        elif char.isprintable():
            parts.append(char)
        else:
            code = ord(char)
            parts.append(f'\\x{code:02x}' if code <= 0xff else
                         f'\\u{code:04x}' if code <= 0xffff else f'\\U{code:08x}')
    return ''.join(parts)


def tokenize(text):
    tokens, errors = [], []
    position, line, col = 0, 1, 1
    metadata = {t['name']: t for t in TOKENS}
    while position < len(text):
        state, cursor, last = START, position, None
        while cursor < len(text):
            char = text[cursor]
            state = TRANS.get(state, {}).get(char) if ord(char) < 128 else OTHER_TRANS.get(state)
            if state is None:
                break
            cursor += 1
            if state in ACCEPT:
                last = cursor, ACCEPT[state]
        if last is None:
            end = position + 1
            errors.append(dict(code='L001', line=line, col=col,
                               message=f'非法字符 {text[position]!r}'))
        else:
            end, name = last
            rule = metadata[name]
            lexeme = text[position:end]
            if not rule['skip']:
                tokens.append(dict(code=rule['code'], kind=name,
                                   attr=None if rule['fixed'] else lexeme,
                                   lexeme=lexeme, line=line, col=col))
        for char in text[position:end]:
            if char == '\n':
                line, col = line + 1, 1
            else:
                col += 1
        position = end
    return tokens, errors


def main():
    ap = argparse.ArgumentParser(description='Generated lexical analyzer')
    ap.add_argument('source')
    ap.add_argument('-o', '--output')
    ap.add_argument('--text', action='store_true')
    args = ap.parse_args()
    try:
        with Path(args.source).open(encoding='utf-8-sig', newline='') as source:
            tokens, errors = tokenize(source.read())
        output = tokens_text(tokens) if args.text else json_text(dict(tokens=tokens, errors=errors))
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
        else:
            sys.stdout.write(output)
        for error in errors:
            print(f"{args.source}:{error['line']}:{error['col']}: 词法错误[L001]: {error['message']}",
                  file=sys.stderr)
        return 1 if errors else 0
    except (OSError, UnicodeError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
