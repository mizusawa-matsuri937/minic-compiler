import itertools
import unittest
from ccgen.regex import parse
from ccgen.nfa import NFA
from ccgen.dfa import determinize, minimize
from ccgen.lexspec import build_tables


class LexgenTests(unittest.TestCase):
    def test_ac04_algorithms(self):
        nfa = NFA()
        nfa.add(parse('(a|b)*abb'), 0)
        nfa.canonicalize()
        discovered = [nfa.start]
        for state in discovered:
            for _, target in nfa.edges[state]:
                if target not in discovered:
                    discovered.append(target)
        self.assertEqual(discovered, list(range(len(nfa.edges))))
        dfa = determinize(nfa)
        minimal = minimize(dfa)
        self.assertEqual(len(minimal.trans), 4)
        self.assertGreaterEqual(len(dfa.trans), 4)
        for length in range(9):
            for chars in itertools.product('ab', repeat=length):
                text = ''.join(chars)
                with self.subTest(text=text):
                    for machine in [nfa, dfa, minimal]:
                        self.assertEqual(machine.accepts(text), text.endswith('abb'))

    def test_ac04_minic_counts(self):
        stats = build_tables('rules/minic.lex')['stats']
        self.assertEqual(set(stats), {'nfa_states', 'dfa_states', 'min_dfa_states'})
        self.assertGreater(stats['nfa_states'], 0)
        self.assertGreater(stats['min_dfa_states'], 0)
        self.assertLessEqual(stats['min_dfa_states'], stats['dfa_states'])
