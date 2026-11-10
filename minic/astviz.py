"""Dependency-free text, DOT and offline SVG tree visualization."""
import html
import json
from pathlib import Path


def children(node):
    for field, value in node.items():
        if isinstance(value, dict) and 'type' in value:
            yield field, value
        elif isinstance(value, list):
            for i, child in enumerate(value):
                if isinstance(child, dict) and 'type' in child:
                    yield f'{field}[{i}]', child


def label(node):
    scalars = [str(value) for key, value in node.items()
               if key not in ('type', 'line', 'col') and not key.startswith('_')
               and not isinstance(value, (dict, list))]
    return ' '.join([node['type']] + scalars)


def text_tree(tree):
    lines = [label(tree)]
    def walk(node, prefix):
        entries = list(children(node))
        for i, (field, child) in enumerate(entries):
            last = i == len(entries) - 1
            lines.append(prefix + ('└── ' if last else '├── ') + field + ': ' + label(child))
            walk(child, prefix + ('    ' if last else '│   '))
    walk(tree, '')
    return '\n'.join(lines) + '\n'


def layout(tree):
    """Subtrees occupy disjoint horizontal intervals at every depth."""
    nodes, edges = [], []
    def measure(node, depth):
        text = label(node)
        width = max(110, 24 + sum(8 if ord(c) < 128 else 16 for c in text))
        item = dict(id=len(nodes), text=text, width=width, y=30 + depth * 100, children=[])
        nodes.append(item)
        for field, child in children(node):
            desc = measure(child, depth + 1)
            item['children'].append(desc)
            edges.append((item['id'], desc['id'], field))
        item['span'] = max(width, sum(c['span'] for c in item['children']) + max(0, len(item['children']) - 1) * 24)
        return item
    root = measure(tree, 0)
    def position(item, left):
        item['x'] = left + item['span'] / 2
        occupied = sum(c['span'] for c in item['children']) + max(0, len(item['children']) - 1) * 24
        cursor = left + (item['span'] - occupied) / 2
        for child in item['children']:
            position(child, cursor)
            cursor += child['span'] + 24
    position(root, 20)
    return nodes, edges, root['span'] + 40, max(n['y'] for n in nodes) + 80


def html_tree(tree):
    nodes, edges, width, height = layout(tree)
    content = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
               f'viewBox="0 0 {width} {height}" role="img" aria-label="AST">']
    for source, target, field in edges:
        a, b = nodes[source], nodes[target]
        content.append(f'<line x1="{a["x"]}" y1="{a["y"] + 36}" x2="{b["x"]}" y2="{b["y"]}" stroke="#64748b"/>')
        content.append(f'<text x="{(a["x"] + b["x"]) / 2}" y="{(a["y"] + b["y"]) / 2 + 12}" '
                       f'class="edge-label">{html.escape(field)}</text>')
    for node in nodes:
        content.append(f'<g class="ast-node" id="node-{node["id"]}">'
                       f'<rect x="{node["x"] - node["width"] / 2}" y="{node["y"]}" '
                       f'width="{node["width"]}" height="36" rx="7"/>'
                       f'<text x="{node["x"]}" y="{node["y"] + 23}">{html.escape(node["text"])}</text></g>')
    content.append('</svg>')
    return ('<!doctype html>\n<html lang="zh"><head><meta charset="utf-8"><title>AST 树形图</title>'
            '<style>body{font-family:monospace;margin:24px;background:#f8fafc;color:#152d49}'
            '.tree{overflow:auto;background:white;border:1px solid #cbd5e1}'
            'text{text-anchor:middle;font-size:14px;fill:#152d49}rect{fill:#eef4fb;stroke:#2563eb}'
            '.edge-label{font-size:12px;paint-order:stroke;stroke:white;stroke-width:4px;stroke-linejoin:round}'
            '</style></head><body><h1>AST · Program</h1><div class="tree">'
            + '\n'.join(content) + '</div></body></html>\n')


def dot_tree(tree):
    nodes, edges, _, _ = layout(tree)
    lines = ['digraph AST {', '  node [shape=box];']
    lines.extend(f'  n{n["id"]} [label={json.dumps(n["text"], ensure_ascii=False)}];' for n in nodes)
    lines.extend(f'  n{a} -> n{b} [label={json.dumps(field)}];' for a, b, field in edges)
    return '\n'.join(lines + ['}']) + '\n'


def write(tree, directory):
    for suffix, render in [('txt', text_tree), ('html', html_tree), ('dot', dot_tree)]:
        (Path(directory) / f'ast.{suffix}').write_text(render(tree), encoding='utf-8')
