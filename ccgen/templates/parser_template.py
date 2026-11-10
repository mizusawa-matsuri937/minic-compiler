"""Standalone LR driver with a small interpreter for validated actions."""
import argparse
import json
import sys
from pathlib import Path


class ParseError(Exception):
    def __init__(self, token, expected):
        self.line, self.col = token['line'], token['col']
        self.actual_kind, self.actual_lexeme = token['kind'], token['lexeme']
        self.expected = expected
        actual = '输入结束' if self.actual_kind == '$' else repr(self.actual_lexeme)
        names = ' '.join('输入结束' if t == '$' else repr(t) for t in expected)
        super().__init__(f'遇到 {actual}，期望 {names} 之一')


def json_text(value):
    """Serialize the AST without Python recursion, using the usual JSON layout."""
    parts, active = [], set()
    pending = [('value', value, 0)]
    while pending:
        event, item, depth = pending.pop()
        if event == 'text':
            parts.append(item)
        elif event == 'close':
            active.remove(id(item))
            parts.append('\n' + '  ' * depth + ('}' if isinstance(item, dict) else ']'))
        elif isinstance(item, (dict, list)):
            opening, closing = ('{', '}') if isinstance(item, dict) else ('[', ']')
            if not item:
                parts.append(opening + closing)
                continue
            if id(item) in active:
                raise ValueError('Circular reference detected')
            active.add(id(item))
            parts.append(opening + '\n')
            pending.append(('close', item, depth))
            entries = list(item.items()) if isinstance(item, dict) else list(enumerate(item))
            for index in range(len(entries) - 1, -1, -1):
                key, child = entries[index]
                if index < len(entries) - 1:
                    pending.append(('text', ',\n', depth))
                pending.append(('value', child, depth + 1))
                prefix = '  ' * (depth + 1)
                if isinstance(item, dict):
                    # AST keys are strings, as are keys in the public JSON data.
                    if not isinstance(key, str):
                        raise TypeError('AST JSON object keys must be strings')
                    prefix += json.dumps(key, ensure_ascii=False) + ': '
                pending.append(('text', prefix, depth))
        else:
            parts.append(json.dumps(item, ensure_ascii=False))
    return ''.join(parts) + '\n'


class _Token(dict):
    """Private value-stack tag; user AST fields never determine token identity."""


def is_token(value):
    return isinstance(value, _Token)


def scalar(value):
    return value['lexeme'] if is_token(value) else value


def construct(production, values, line, col):
    action = production['action']
    kind = action[0]
    if kind == 'pass':
        return values[action[1] - 1]
    if kind == 'list':
        result = []
        for spread, index in action[1]:
            value = scalar(values[index - 1])
            if spread:
                if not isinstance(value, list):
                    raise ValueError('构造动作展开值不是列表')
                result.extend(value)
            else:
                result.append(value)
        return result
    if kind == 'node':
        node = dict(type=action[1], line=line, col=col)
        for field, index in action[2]:
            node[field] = scalar(values[index - 1])
        return node
    children = [dict(type=v['kind'], lexeme=v['lexeme'], line=v['line'], col=v['col'])
                if is_token(v) else v for v in values]
    return dict(type=production['lhs'], line=line, col=col, children=children)


def parse(tokens):
    if tokens:
        last = tokens[-1]
        line, col = last['line'], last['col']
        for char in last['lexeme']:
            if char == '\n':
                line, col = line + 1, 1
            else:
                col += 1
    else:
        line, col = 1, 1
    eof = dict(code=0, kind='$', attr=None, lexeme='', line=line, col=col)
    states, values, positions = [0], [], []
    cursor = 0
    while True:
        token = tokens[cursor] if cursor < len(tokens) else eof
        row = ACTION[states[-1]]
        action = row.get(token['kind'])
        if action is None:
            raise ParseError(token, [t for t in TERMINALS if t in row])
        kind, argument = action
        if kind == 'shift':
            states.append(argument)
            values.append(_Token(token))
            positions.append((token['line'], token['col']))
            cursor += 1
        elif kind == 'reduce':
            production = PRODUCTIONS[argument]
            count = len(production['rhs'])
            location = positions[-count] if count else (token['line'], token['col'])
            args = values[-count:] if count else []
            value = construct(production, args, *location)
            if count:
                del states[-count:]
                del values[-count:]
                del positions[-count:]
            states.append(GOTO[states[-1]][production['lhs']])
            values.append(value)
            positions.append(location)
        else:
            return scalar(values[-1])


def main():
    ap = argparse.ArgumentParser(description='Generated LR(1) analyzer')
    ap.add_argument('tokens')
    ap.add_argument('-o', '--output')
    args = ap.parse_args()
    try:
        payload = json.loads(Path(args.tokens).read_text(encoding='utf-8'))
        if payload['errors']:
            print(f'{args.tokens}: 词法分析有错误，拒绝语法分析', file=sys.stderr)
            return 1
        output = json_text(parse(payload['tokens']))
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
        else:
            sys.stdout.write(output)
        return 0
    except ParseError as error:
        print(f'{args.tokens}:{error.line}:{error.col}: 语法错误[P001]: {error}', file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        print(f'{args.tokens}: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
