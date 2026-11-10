"""Canonical LR(1), including explicit, recorded conflict resolution."""
from collections import defaultdict, deque
from .errors import RuleError


def build_tables(grammar):
    productions = grammar['productions']
    nonterminals = grammar['nonterminals']
    terminals = grammar['terminals']
    first = {s: {s} for s in terminals}
    first.update({p['lhs']: set() for p in productions})
    nullable = set()
    changed = True
    while changed:
        changed = False
        for p in productions:
            old = len(first[p['lhs']])
            for symbol in p['rhs']:
                first[p['lhs']].update(first[symbol])
                if symbol not in nullable:
                    break
            else:
                if p['lhs'] not in nullable:
                    nullable.add(p['lhs'])
                    changed = True
            changed |= len(first[p['lhs']]) != old

    def first_sequence(sequence):
        found = set()
        for symbol in sequence:
            found.update(first[symbol])
            if symbol not in nullable:
                break
        return found

    by_lhs = defaultdict(list)
    for p in productions:
        by_lhs[p['lhs']].append(p['id'])

    def closure(seed):
        found, todo = set(seed), deque(sorted(seed))
        while todo:
            pid, dot, lookahead = todo.popleft()
            rhs = productions[pid]['rhs']
            if dot == len(rhs) or rhs[dot] not in by_lhs:
                continue
            for next_pid in by_lhs[rhs[dot]]:
                for terminal in sorted(first_sequence(rhs[dot + 1:] + [lookahead])):
                    item = next_pid, 0, terminal
                    if item not in found:
                        found.add(item)
                        todo.append(item)
        return frozenset(found)

    states = [closure([(0, 0, '$')])]
    ids, transitions = {states[0]: 0}, []
    for state in states:
        seeds = defaultdict(set)
        for pid, dot, lookahead in sorted(state):
            rhs = productions[pid]['rhs']
            if dot < len(rhs):
                seeds[rhs[dot]].add((pid, dot + 1, lookahead))
        row = {}
        for symbol in grammar['symbols']:
            if symbol not in seeds:
                continue
            target = closure(seeds[symbol])
            if target not in ids:
                ids[target] = len(states)
                states.append(target)
            row[symbol] = ids[target]
        transitions.append(row)

    def item_text(item):
        pid, dot, lookahead = item
        p = productions[pid]
        symbols = p['rhs'][:dot] + ['·'] + p['rhs'][dot:]
        return f"{p['lhs']} -> {' '.join(symbols)}, {lookahead}"

    action, goto, conflicts, unresolved = {}, {}, [], []
    for i, state in enumerate(states):
        candidates = defaultdict(set)
        for symbol, target in transitions[i].items():
            if symbol in terminals:
                candidates[symbol].add(('shift', target))
        for pid, dot, lookahead in sorted(state):
            if dot == len(productions[pid]['rhs']):
                candidates[lookahead].add(('accept', 0) if pid == 0 else ('reduce', pid))
        row = {}
        for terminal in terminals:
            choices = candidates[terminal]
            if not choices:
                continue
            shifts = sorted(c for c in choices if c[0] == 'shift')
            reductions = sorted(c for c in choices if c[0] == 'reduce')
            selected = sorted(choices)[0]
            if len(choices) > 1:
                resolved = len(shifts) == 1 and len(reductions) == 1 and terminal in grammar['prefer']
                kind = 'shift-reduce' if shifts else 'reduce-reduce'
                conflict = dict(state=i, lookahead=terminal, kind=kind,
                                shift=shifts[0][1] if shifts else None,
                                reduce=reductions[0][1], resolution='shift' if resolved else None)
                conflicts.append(conflict)
                if resolved:
                    selected = shifts[0]
                else:
                    label = '移进-归约' if shifts else '归约-归约'
                    detail = '\n  '.join(item_text(item) for item in sorted(state))
                    unresolved.append(f'状态 {i} 向前看符号 {terminal!r} 上的{label}冲突 ({kind})\n  {detail}')
            row[terminal] = list(selected)
        action[str(i)] = row
        goto[str(i)] = {s: t for s, t in transitions[i].items() if s in nonterminals}
    if unresolved:
        raise RuleError(grammar['path'], 1, '\n'.join(unresolved))
    return dict(productions=[{k: v for k, v in p.items() if k != 'line'} for p in productions],
                terminals=terminals, nonterminals=nonterminals,
                first={s: [t for t in terminals if t in first[s]] + (['ε'] if s in nullable else [])
                       for s in nonterminals},
                states=len(states), action=action, goto=goto, conflicts=conflicts,
                items=[[item_text(item) for item in sorted(state)] for state in states])
