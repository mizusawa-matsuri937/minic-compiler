"""Subset construction and partition refinement (partial transition tables)."""
from .regex import ALPHABET, OTHER


class DFA:
    def __init__(self, trans, accept):
        self.start, self.trans, self.accept = 0, trans, accept

    def accepts(self, text):
        state = self.start
        for char in text:
            state = self.trans[state].get(min(ord(char), OTHER))
            if state is None:
                return False
        return state in self.accept


def determinize(nfa):
    states = [nfa.closure([nfa.start])]
    ids, trans, accept = {states[0]: 0}, [], {}
    for i, subset in enumerate(states):
        rules = [nfa.accept[s] for s in subset if s in nfa.accept]
        if rules:
            accept[i] = min(rules)
        row = {}
        for symbol in ALPHABET:
            target = nfa.move(subset, symbol)
            if target:
                if target not in ids:
                    ids[target] = len(states)
                    states.append(target)
                row[symbol] = ids[target]
        trans.append(row)
    return DFA(trans, accept)


def minimize(dfa):
    initial = {}
    for state in range(len(dfa.trans)):
        initial.setdefault(dfa.accept.get(state), []).append(state)
    groups = list(initial.values())
    while True:
        membership = {s: i for i, group in enumerate(groups) for s in group}
        refined = []
        for group in groups:
            splits = {}
            for state in group:
                signature = tuple(membership.get(dfa.trans[state].get(c), -1) for c in ALPHABET)
                splits.setdefault(signature, []).append(state)
            refined.extend(splits.values())
        if len(refined) == len(groups):
            break
        groups = refined
    # Canonical BFS numbering of quotient states, with the start always zero.
    start = membership[0]
    order, ids, trans, accept = [start], {start: 0}, [], {}
    for i, group_id in enumerate(order):
        representative = groups[group_id][0]
        if representative in dfa.accept:
            accept[i] = dfa.accept[representative]
        row = {}
        for symbol, target in sorted(dfa.trans[representative].items()):
            dest = membership[target]
            if dest not in ids:
                ids[dest] = len(order)
                order.append(dest)
            row[symbol] = ids[dest]
        trans.append(row)
    return DFA(trans, accept)
