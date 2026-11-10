"""Thompson fragments with one entry and one exit each."""
from .regex import OTHER


class NFA:
    def __init__(self):
        self.edges = []
        self.accept = {}
        self.start = self.state()

    def state(self):
        self.edges.append([])
        return len(self.edges) - 1

    def edge(self, source, target, chars=None):
        self.edges[source].append((chars, target))

    def fragment(self, tree):
        op, *parts = tree
        start, end = self.state(), self.state()
        if op == 'chars':
            self.edge(start, end, parts[0])
        elif op == 'seq':
            tail = start
            for part in parts:
                a, b = self.fragment(part)
                self.edge(tail, a)
                tail = b
            self.edge(tail, end)
        elif op == 'or':
            for part in parts:
                a, b = self.fragment(part)
                self.edge(start, a)
                self.edge(b, end)
        elif op == '+':
            a, b = self.fragment(('seq', parts[0], ('*', parts[0])))
            self.edge(start, a)
            self.edge(b, end)
        elif op == '?':
            a, b = self.fragment(('or', parts[0], ('seq',)))
            self.edge(start, a)
            self.edge(b, end)
        elif op == '*':
            a, b = self.fragment(parts[0])
            self.edge(start, a)
            self.edge(start, end)
            self.edge(b, a)
            self.edge(b, end)
        else:
            raise ValueError(op)
        return start, end

    def add(self, tree, rule):
        start, end = self.fragment(tree)
        self.edge(self.start, start)
        self.accept[end] = rule

    def canonicalize(self):
        """Renumber reachable states in BFS order, epsilon before characters."""
        def ordered(edges):
            return sorted(edges, key=lambda edge: (
                () if edge[0] is None else tuple(sorted(edge[0])), edge[1]))

        order, ids = [self.start], {self.start: 0}
        for source in order:
            for _, target in ordered(self.edges[source]):
                if target not in ids:
                    ids[target] = len(order)
                    order.append(target)
        self.edges = [[(chars, ids[target]) for chars, target in ordered(self.edges[source])]
                      for source in order]
        self.accept = {ids[state]: rule for state, rule in sorted(self.accept.items())}
        self.start = 0

    def closure(self, states):
        found, todo = set(states), list(states)
        while todo:
            for chars, target in self.edges[todo.pop()]:
                if chars is None and target not in found:
                    found.add(target)
                    todo.append(target)
        return frozenset(found)

    def move(self, states, symbol):
        return self.closure({target for state in states for chars, target in self.edges[state]
                             if chars is not None and symbol in chars})

    def accepts(self, text):
        states = self.closure([self.start])
        for char in text:
            states = self.move(states, min(ord(char), OTHER))
        return any(s in self.accept for s in states)
