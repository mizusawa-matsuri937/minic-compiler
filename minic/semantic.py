"""Lexical scopes, declaration checks, and deterministic storage-slot binding."""


def check(tree):
    scopes, counts, errors = [{}], {}, []

    def error(node, code, message):
        errors.append(dict(code=code, line=node['line'], col=node['col'], message=message))

    def lookup(node, name):
        for scope in reversed(scopes):
            if name in scope:
                node['_slot'] = scope[name]
                return
        error(node, 'S001', f'变量 {name!r} 未声明')

    def scoped(node):
        scopes.append({})
        visit(node)
        scopes.pop()

    def visit(node):
        kind = node['type']
        if kind == 'Program':
            for child in node['body']:
                visit(child)
        elif kind == 'Block':
            scopes.append({})
            for child in node['body']:
                visit(child)
            scopes.pop()
        elif kind == 'VarDecl':
            if 'init' in node:
                visit(node['init'])
            name = node['name']
            if name in scopes[-1]:
                error(node, 'S002', f'变量 {name!r} 重复声明')
            else:
                count = counts.get(name, 0)
                slot = name + '.addr' + (f'.{count}' if count else '')
                counts[name] = count + 1
                scopes[-1][name] = node['_slot'] = slot
        elif kind == 'Identifier':
            lookup(node, node['name'])
        elif kind in ('Assign', 'Read'):
            lookup(node, node['target'])
            if kind == 'Assign':
                visit(node['value'])
        elif kind == 'Number':
            normalized = node['value'].lstrip('0') or '0'
            if len(normalized) > 10 or (len(normalized) == 10 and normalized > '2147483647'):
                error(node, 'S003', '整型常数超过 2147483647')
        elif kind == 'BinaryOp':
            visit(node['left'])
            visit(node['right'])
        elif kind == 'Write':
            visit(node['value'])
        elif kind == 'If':
            visit(node['cond'])
            scoped(node['then'])
            if 'else' in node:
                scoped(node['else'])
        elif kind == 'While':
            visit(node['cond'])
            scoped(node['body'])
        else:
            raise ValueError(f'未知 AST 结点 {kind}')

    visit(tree)
    return sorted(errors, key=lambda e: (e['line'], e['col']))
