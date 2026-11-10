"""Lexical rule validation and construction of serializable tables."""
from pathlib import Path
from .errors import RuleError
from .regex import parse, singleton, OTHER
from .nfa import NFA
from .dfa import determinize, minimize


def build_tables(path):
    path = Path(path)
    rules, skipped, names = [], {}, set()
    for line, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        text = raw.strip()
        if not text or text.startswith('#'):
            continue
        fields = text.split(maxsplit=1)
        if fields[0] == '%skip' and len(fields) == 2:
            for name in fields[1].split():
                skipped[name] = line
            continue
        name = fields[0]
        if len(fields) != 2 or name.startswith(('%', '#')) or name in ('$', 'ε') or name in names:
            raise RuleError(path, line, '非法或重复的记号规则')
        tree = parse(fields[1], path, line)
        names.add(name)
        rules.append((name, fields[1], tree, line))
    for name, line in skipped.items():
        if name not in names:
            raise RuleError(path, line, f'%skip 引用了未定义的记号 {name}')
    if not rules:
        raise RuleError(path, 1, '没有词法规则')
    nfa, tokens, code = NFA(), [], 0
    for i, (name, regex, tree, line) in enumerate(rules):
        nfa.add(tree, i)
        skip = name in skipped
        if not skip:
            code += 1
        tokens.append(dict(code=None if skip else code, name=name, regex=regex,
                           skip=skip, fixed=singleton(tree) is not None))
    nfa.canonicalize()
    for state in sorted(nfa.closure([nfa.start])):
        if state in nfa.accept:
            name, _, _, line = rules[nfa.accept[state]]
            raise RuleError(path, line, f'记号 {name} 可匹配空串')
    dfa = determinize(nfa)
    minimal = minimize(dfa)
    return dict(tokens=tokens, stats=dict(nfa_states=len(nfa.edges), dfa_states=len(dfa.trans),
                                        min_dfa_states=len(minimal.trans)),
                start=0, accept={str(s): tokens[r]['name'] for s, r in minimal.accept.items()},
                trans={str(s): {chr(c): t for c, t in row.items() if c != OTHER}
                       for s, row in enumerate(minimal.trans)},
                other_trans={str(s): row[OTHER] for s, row in enumerate(minimal.trans) if OTHER in row})
