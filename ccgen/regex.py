"""Recursive descent for the documented regular-expression language.

Character sets use integers 0..127 and 128 (OTHER). Python's re engine is
deliberately not used to recognize source programs.
"""
from .errors import RuleError

OTHER = 128
ALPHABET = range(129)


class RegexParser:
    def __init__(self, text, path='<regex>', line=1):
        self.text, self.path, self.line, self.pos = text, path, line, 0

    def fail(self, message):
        raise RuleError(self.path, self.line, f"正规式第 {self.pos + 1} 列: {message}")

    def peek(self):
        return self.text[self.pos:self.pos + 1]

    def parse(self):
        tree = self.choice()
        if self.peek():
            self.fail('多余的元字符')
        return tree

    def choice(self):
        terms = [self.concat()]
        while self.peek() == '|':
            self.pos += 1
            terms.append(self.concat())
        return terms[0] if len(terms) == 1 else ('or', *terms)

    def concat(self):
        terms = []
        while self.peek() and self.peek() not in '|)':
            term = self.atom()
            while self.peek() and self.peek() in '*+?':
                op = self.peek()
                self.pos += 1
                term = (op, term)
            terms.append(term)
        return ('seq', *terms)

    def character(self):
        char = self.peek()
        if not char:
            self.fail('缺少字符')
        self.pos += 1
        if char == '\\':
            char = self.peek()
            if not char:
                self.fail('转义不完整')
            self.pos += 1
            char = {'n': '\n', 't': '\t', 'r': '\r'}.get(char, char)
        if ord(char) >= OTHER:
            self.fail('字面字符必须是 ASCII；非 ASCII 仅由取反字符类匹配')
        return ord(char)

    def atom(self):
        char = self.peek()
        if char == '(':
            self.pos += 1
            tree = self.choice()
            if self.peek() != ')':
                self.fail('缺少右括号 )')
            self.pos += 1
            return tree
        if char == '[':
            self.pos += 1
            negate = self.peek() == '^'
            if negate:
                self.pos += 1
            chars = set()
            while self.peek() and self.peek() != ']':
                lo = self.character()
                if self.peek() == '-' and self.text[self.pos + 1:self.pos + 2] not in ('', ']'):
                    self.pos += 1
                    hi = self.character()
                    if hi < lo:
                        self.fail('字符范围倒置')
                    chars.update(range(lo, hi + 1))
                else:
                    chars.add(lo)
            if self.peek() != ']' or not chars:
                self.fail('字符类为空或缺少 ]')
            self.pos += 1
            if negate:
                chars = set(ALPHABET) - chars
            return ('chars', frozenset(chars))
        if char in '*+?)]':
            self.fail('元字符缺少操作数或未转义')
        return ('chars', frozenset([self.character()]))


def parse(text, path='<regex>', line=1):
    return RegexParser(text, path, line).parse()


def singleton(tree):
    """Return the only accepted string, or None if there are several."""
    op, *parts = tree
    if op == 'chars':
        chars = parts[0]
        return chr(next(iter(chars))) if len(chars) == 1 and OTHER not in chars else None
    values = [singleton(p) for p in parts]
    if op == 'seq':
        return ''.join(values) if all(v is not None for v in values) else None
    if op == 'or':
        return values[0] if all(v == values[0] for v in values) else None
    return '' if values[0] == '' else None
