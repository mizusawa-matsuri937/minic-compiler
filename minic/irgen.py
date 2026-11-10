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
        kind = node['type']
        if kind == 'Number':
            return node['value'].lstrip('0') or '0'
        if kind == 'Identifier':
            return self.value(f"load i32, ptr %{node['_slot']}")
        left = self.expression(node['left'])
        right = self.expression(node['right'])
        arithmetic = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'sdiv'}
        op = node['op']
        if op in arithmetic:
            return self.value(f'{arithmetic[op]} i32 {left}, {right}')
        predicate = {'<': 'slt', '>': 'sgt', '==': 'eq', '!=': 'ne', '<=': 'sle', '>=': 'sge'}[op]
        comparison = self.value(f'icmp {predicate} i32 {left}, {right}')
        return self.value(f'zext i1 {comparison} to i32')

    def condition(self, node):
        value = self.expression(node)
        return self.value(f'icmp ne i32 {value}, 0')

    def statement(self, node):
        kind = node['type']
        if kind in ('Program', 'Block'):
            for child in node['body']:
                self.statement(child)
        elif kind in ('VarDecl', 'Assign'):
            if kind == 'VarDecl':
                self.allocas.append(f"  %{node['_slot']} = alloca i32")
                value = self.expression(node['init']) if 'init' in node else '0'
            else:
                value = self.expression(node['value'])
            self.emit(f"store i32 {value}, ptr %{node['_slot']}")
        elif kind == 'Read':
            self.emit(f"call i32 (ptr, ...) @scanf(ptr @.fmt.read, ptr %{node['_slot']})")
        elif kind == 'Write':
            value = self.expression(node['value'])
            self.emit(f'call i32 (ptr, ...) @printf(ptr @.fmt.write, i32 {value})')
        elif kind == 'If':
            self.control += 1
            number = self.control
            then, otherwise, end = [f'if.{part}.{number}' for part in ('then', 'else', 'end')]
            condition = self.condition(node['cond'])
            self.emit(f'br i1 {condition}, label %{then}, label %{otherwise if "else" in node else end}')
            self.label(then)
            self.statement(node['then'])
            self.emit(f'br label %{end}')
            if 'else' in node:
                self.label(otherwise)
                self.statement(node['else'])
                self.emit(f'br label %{end}')
            self.label(end)
        elif kind == 'While':
            self.control += 1
            number = self.control
            cond, body, end = [f'while.{part}.{number}' for part in ('cond', 'body', 'end')]
            self.emit(f'br label %{cond}')
            self.label(cond)
            condition = self.condition(node['cond'])
            self.emit(f'br i1 {condition}, label %{body}, label %{end}')
            self.label(body)
            self.statement(node['body'])
            self.emit(f'br label %{cond}')
            self.label(end)
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
