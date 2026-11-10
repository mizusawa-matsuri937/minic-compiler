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

    # Continuations preserve initializer-before-declaration and scope lifetimes
    # without tying valid source nesting to the Python call stack.
    pending = [('visit', tree)]
    while pending:
        action, node = pending.pop()
        if action == 'leave':
            scopes.pop()
            continue
        if action == 'scoped':
            scopes.append({})
            pending.extend([('leave', None), ('visit', node)])
            continue
        if action == 'declare':
            name = node['name']
            if name in scopes[-1]:
                error(node, 'S002', f'变量 {name!r} 重复声明')
            else:
                count = counts.get(name, 0)
                slot = name + '.addr' + (f'.{count}' if count else '')
                counts[name] = count + 1
                scopes[-1][name] = node['_slot'] = slot
            continue
        kind = node['type']
        if kind in ('Program', 'Block'):
            if kind == 'Block':
                scopes.append({})
                pending.append(('leave', None))
            pending.extend(('visit', child) for child in reversed(node['body']))
        elif kind == 'VarDecl':
            pending.append(('declare', node))
            if 'init' in node:
                pending.append(('visit', node['init']))
        elif kind == 'Identifier':
            lookup(node, node['name'])
        elif kind in ('Assign', 'Read'):
            lookup(node, node['target'])
            if kind == 'Assign':
                pending.append(('visit', node['value']))
        elif kind == 'Number':
            normalized = node['value'].lstrip('0') or '0'
            if len(normalized) > 10 or (len(normalized) == 10 and normalized > '2147483647'):
                error(node, 'S003', '整型常数超过 2147483647')
        elif kind == 'BinaryOp':
            pending.extend([('visit', node['right']), ('visit', node['left'])])
        elif kind == 'Write':
            pending.append(('visit', node['value']))
        elif kind == 'If':
            if 'else' in node:
                pending.append(('scoped', node['else']))
            pending.extend([('scoped', node['then']), ('visit', node['cond'])])
        elif kind == 'While':
            pending.extend([('scoped', node['body']), ('visit', node['cond'])])
        else:
            raise ValueError(f'未知 AST 结点 {kind}')

    return sorted(errors, key=lambda e: (e['line'], e['col']))
