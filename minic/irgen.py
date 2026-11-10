"""Direct textual LLVM IR generation from the semantically bound mini-C AST."""
from pathlib import Path


def llvm_string(text):
    return ''.join(chr(b) if 32 <= b < 127 and b not in (34, 92) else f'\\{b:02X}'
                   for b in text.encode('utf-8'))


class Generator:
    def __init__(self):
        self.temporary, self.control = 0, 0
        self.instructions, self.allocas = [], []

    def emit(self, instruction):
        self.instructions.append('  ' + instruction)

    def value(self, instruction):
        self.temporary += 1
        name = f'%t{self.temporary}'
        self.emit(f'{name} = {instruction}')
        return name

    def label(self, name):
        self.instructions.append(name + ':')

    def expression(self, node):
        pending, values = [(node, False)], []
        arithmetic = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'sdiv'}
        predicates = {'<': 'slt', '>': 'sgt', '==': 'eq', '!=': 'ne', '<=': 'sle', '>=': 'sge'}
        while pending:
            current, ready = pending.pop()
            kind = current['type']
            if kind == 'Number':
                values.append(current['value'].lstrip('0') or '0')
            elif kind == 'Identifier':
                values.append(self.value(f"load i32, ptr %{current['_slot']}"))
            elif not ready:
                pending.extend([(current, True), (current['right'], False),
                                (current['left'], False)])
            else:
                right, left = values.pop(), values.pop()
                op = current['op']
                if op in arithmetic:
                    values.append(self.value(f'{arithmetic[op]} i32 {left}, {right}'))
                else:
                    comparison = self.value(f'icmp {predicates[op]} i32 {left}, {right}')
                    values.append(self.value(f'zext i1 {comparison} to i32'))
        return values[0]

    def condition(self, node):
        value = self.expression(node)
        return self.value(f'icmp ne i32 {value}, 0')

    def statement(self, node):
        # Deferred label/branch events keep source order and the original DFS
        # numbering, including continuations after arbitrarily nested bodies.
        pending = [('statement', node)]
        while pending:
            action, current = pending.pop()
            if action == 'label':
                self.label(current)
                continue
            if action == 'emit':
                self.emit(current)
                continue
            kind = current['type']
            if kind in ('Program', 'Block'):
                pending.extend(('statement', child) for child in reversed(current['body']))
            elif kind in ('VarDecl', 'Assign'):
                if kind == 'VarDecl':
                    self.allocas.append(f"  %{current['_slot']} = alloca i32")
                    value = self.expression(current['init']) if 'init' in current else '0'
                else:
                    value = self.expression(current['value'])
                self.emit(f"store i32 {value}, ptr %{current['_slot']}")
            elif kind == 'Read':
                self.emit(f"call i32 (ptr, ...) @scanf(ptr @.fmt.read, ptr %{current['_slot']})")
            elif kind == 'Write':
                value = self.expression(current['value'])
                self.emit(f'call i32 (ptr, ...) @printf(ptr @.fmt.write, i32 {value})')
            elif kind == 'If':
                self.control += 1
                then, otherwise, end = [f'if.{part}.{self.control}' for part in ('then', 'else', 'end')]
                condition = self.condition(current['cond'])
                self.emit(f'br i1 {condition}, label %{then}, label %{otherwise if "else" in current else end}')
                self.label(then)
                continuation = [('statement', current['then']), ('emit', f'br label %{end}')]
                if 'else' in current:
                    continuation.extend([('label', otherwise), ('statement', current['else']),
                                         ('emit', f'br label %{end}')])
                continuation.append(('label', end))
                pending.extend(reversed(continuation))
            elif kind == 'While':
                self.control += 1
                cond, body, end = [f'while.{part}.{self.control}' for part in ('cond', 'body', 'end')]
                self.emit(f'br label %{cond}')
                self.label(cond)
                condition = self.condition(current['cond'])
                self.emit(f'br i1 {condition}, label %{body}, label %{end}')
                self.label(body)
                pending.extend([('label', end), ('emit', f'br label %{cond}'),
                                ('statement', current['body'])])
            else:
                raise ValueError(f'未知语句 {kind}')


def generate(tree, source_name):
    generator = Generator()
    generator.statement(tree)
    generator.emit('ret i32 0')
    name = llvm_string(Path(source_name).name)
    header = [f"; ModuleID = '{name}'", f'source_filename = "{name}"', '',
              '@.fmt.read = private unnamed_addr constant [3 x i8] c"%d\\00"',
              '@.fmt.write = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"', '',
              'declare i32 @printf(ptr, ...)', 'declare i32 @scanf(ptr, ...)', '',
              'define i32 @main() {', 'entry:']
    return '\n'.join(header + generator.allocas + generator.instructions + ['}', ''])
