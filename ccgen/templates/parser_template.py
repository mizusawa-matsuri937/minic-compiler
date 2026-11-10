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
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def is_token(value):
    return isinstance(value, dict) and 'kind' in value and 'lexeme' in value


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
            values.append(token)
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
