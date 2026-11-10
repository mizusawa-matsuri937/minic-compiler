"""Grammar and declarative action parser. Actions are data, never Python code."""
from pathlib import Path
import re
from .errors import RuleError


def action_parse(text, arity, path, line):
    def fail(message):
        raise RuleError(path, line, '构造动作: ' + message)

    def reference(value):
        match = re.fullmatch(r'\$(\d+)', value.strip())
        if not match or not 1 <= int(match[1]) <= arity:
            fail(f'非法或越界引用 {value}')
        return int(match[1])

    if text is None:
        return ['default']
    text = text.strip()
    if text.startswith('$'):
        return ['pass', reference(text)]
    if text.startswith('[') and text.endswith(']'):
        inner = text[1:-1].strip()
        entries = []
        if inner:
            for value in inner.split(','):
                value = value.strip()
                spread = value.startswith('*')
                entries.append([spread, reference(value[1:] if spread else value)])
        return ['list', entries]
    match = re.fullmatch(r'([A-Za-z_][A-Za-z_0-9]*)\s*\((.*)\)', text)
    if not match:
        fail('语法错误')
    fields, names = [], set()
    if match[2].strip():
        for item in match[2].split(','):
            pair = re.fullmatch(r'\s*([A-Za-z_][A-Za-z_0-9]*)\s*=\s*(\$\d+)\s*', item)
            if not pair or pair[1] in names or pair[1] in ('type', 'line', 'col'):
                fail('非法、重复或保留字段')
            names.add(pair[1])
            fields.append([pair[1], reference(pair[2])])
    return ['node', match[1], fields]


def read_grammar(path, tokens):
    path = Path(path)
    productions, nonterminals, symbols, prefer = [], [], [], set()
    prefer_lines = {}
    start, start_line = None, 1
    for line, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        text = raw.strip()
        if not text or text.startswith('#'):
            continue
        if text.startswith('%'):
            parts = text.split()
            if parts[0] == '%start' and len(parts) == 2 and start is None:
                start, start_line = parts[1], line
            elif parts[:2] == ['%prefer', 'shift'] and len(parts) >= 3:
                prefer.update(parts[2:])
                prefer_lines.update({name: line for name in parts[2:]})
            else:
                raise RuleError(path, line, '非法或重复的文法指令')
            continue
        body, separator, action = text.partition('=>')
        pieces = body.split('->')
        if len(pieces) != 2 or len(pieces[0].split()) != 1:
            raise RuleError(path, line, '产生式需要一个左部和 ->')
        lhs, rhs = pieces[0].strip(), pieces[1].split()
        if rhs in (['ε'], ['%empty']):
            rhs = []
        if not pieces[1].strip() or any(s in ('$', 'ε', '%empty', '=>') or s.startswith('%') for s in [lhs] + rhs):
            raise RuleError(path, line, '非法符号；空串请写 ε 或 %empty')
        if lhs not in nonterminals:
            nonterminals.append(lhs)
        for symbol in [lhs] + rhs:
            if symbol not in symbols:
                symbols.append(symbol)
        productions.append(dict(id=len(productions) + 1, lhs=lhs, rhs=rhs,
                                action=action_parse(action if separator else None, len(rhs), path, line),
                                line=line))
    if not productions:
        raise RuleError(path, 1, '没有产生式')
    start = start or productions[0]['lhs']
    if start not in nonterminals:
        raise RuleError(path, start_line, f'开始符号 {start} 没有产生式')
    terminals = [t['name'] for t in tokens if not t['skip']]
    for production in productions:
        if production['lhs'] in terminals:
            raise RuleError(path, production['line'], '非终结符与词法记号重名')
        for symbol in production['rhs']:
            if symbol not in nonterminals and symbol not in terminals:
                raise RuleError(path, production['line'], f'未定义的终结符 {symbol}')
    for name in sorted(prefer - set(terminals)):
        raise RuleError(path, prefer_lines[name], f'冲突声明引用了未定义的终结符 {name}')
    augmented = "S'"
    while augmented in symbols or augmented in terminals:
        augmented += "'"
    productions.insert(0, dict(id=0, lhs=augmented, rhs=[start], action=['pass', 1], line=1))
    return dict(path=str(path), productions=productions, nonterminals=nonterminals,
                terminals=terminals + ['$'], symbols=symbols, prefer=prefer)
