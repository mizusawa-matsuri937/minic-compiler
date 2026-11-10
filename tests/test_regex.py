import unittest
from ccgen.regex import parse
from ccgen.nfa import NFA
from ccgen.dfa import determinize, minimize


class RegexTests(unittest.TestCase):
    def test_ac03_acceptance(self):
        cases = [
            ('(a|b)*abb', ['abb', 'aabb', 'babb'], ['ab', 'abba', '']),
            ('[0-9]+', ['0', '007'], ['', '1a']),
            ('[a-zA-Z_][a-zA-Z0-9_]*', ['_x1', 'A'], ['1x']),
            ('a?b+', ['b', 'abbb'], ['a', 'aab']),
            (r'//[^\n]*', ['//', '// 中文 x'], ['/', '//a\nb']),
            (r'\+\*', ['+*'], ['', '+', '*', '*+', '+**']),
        ]
        for expression, yes, no in cases:
            nfa = NFA()
            nfa.add(parse(expression), 0)
            machines = [nfa, determinize(nfa), minimize(determinize(nfa))]
            for text in yes + no:
                with self.subTest(expression=expression, text=text):
                    for machine in machines:
                        self.assertEqual(machine.accepts(text), text in yes)
