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
    pending = [(tree, '', None)]
    while pending:
        node, prefix, entry = pending.pop()
        if entry is not None:
            field, last = entry
            lines.append(prefix + ('└── ' if last else '├── ') + field + ': ' + label(node))
            prefix += '    ' if last else '│   '
        entries = list(children(node))
        pending.extend((child, prefix, (field, i == len(entries) - 1))
                       for i, (field, child) in reversed(list(enumerate(entries))))
    return '\n'.join(lines) + '\n'


def layout(tree):
    """Iterative subtree layout; HTML refines estimates with actual glyph bounds."""
    nodes, edges = [], []
    pending = [(tree, 0, None, None)]
    while pending:
        node, depth, parent, field = pending.pop()
        text = label(node)
        width = max(110, 24 + sum(10 if ord(c) < 128 else 18 for c in text))
        item = dict(id=len(nodes), text=text, width=width, y=30 + depth * 100, children=[])
        nodes.append(item)
        if parent is not None:
            parent['children'].append(item)
            edges.append((parent['id'], item['id'], field))
        pending.extend((child, depth + 1, item, name)
                       for name, child in reversed(list(children(node))))
    for item in reversed(nodes):
        occupied = sum(c['span'] for c in item['children']) + max(0, len(item['children']) - 1) * 24
        item['span'] = max(item['width'], occupied)
    pending = [(nodes[0], 20)]
    while pending:
        item, left = pending.pop()
        item['x'] = left + item['span'] / 2
        occupied = sum(c['span'] for c in item['children']) + max(0, len(item['children']) - 1) * 24
        cursor = left + (item['span'] - occupied) / 2
        for child in item['children']:
            pending.append((child, cursor))
            cursor += child['span'] + 24
    return nodes, edges, nodes[0]['span'] + 40, max(n['y'] for n in nodes) + 80


# Only local SVG/DOM APIs are used. Measuring the rendered glyphs also handles
# a platform choosing a different monospace font; no font/network dependency.
_REFLOW = r"""
<script>
(() => {
  const svg = document.querySelector('svg');
  const container = document.getElementById('ast-tree');
  const fit = document.getElementById('ast-fit'), actual = document.getElementById('ast-actual');
  let mode = 'actual';
  function applyView() {
    const natural = svg.viewBox.baseVal;
    const width = mode === 'fit' ? container.clientWidth : natural.width;
    svg.setAttribute('width', width);
    svg.setAttribute('height', natural.height * width / natural.width);
    if (mode === 'fit') {
      container.scrollLeft = 0;
    } else {
      const root = svg.querySelector('.ast-node rect');
      const center = Number(root.getAttribute('x')) + Number(root.getAttribute('width')) / 2;
      container.scrollLeft = Math.max(0, Math.min(center - container.clientWidth / 2,
                                                container.scrollWidth - container.clientWidth));
    }
    fit.setAttribute('aria-pressed', String(mode === 'fit'));
    actual.setAttribute('aria-pressed', String(mode === 'actual'));
  }
  fit.addEventListener('click', () => { mode = 'fit'; applyView(); });
  actual.addEventListener('click', () => { mode = 'actual'; applyView(); });
  function reflow() {
    const nodes = Array.from(svg.querySelectorAll('.ast-node'), group => {
      const text = group.querySelector('text'), rect = group.querySelector('rect');
      text.setAttribute('x', 0); text.setAttribute('y', 0);
      const box = text.getBBox();
      return {text, rect, box, width: Math.max(110, box.width + 24),
              height: Math.max(36, box.height + 16), children: [], depth: 0};
    });
    const edges = Array.from(svg.querySelectorAll('line'), line => {
      const source = Number(line.dataset.source), target = Number(line.dataset.target);
      const text = line.nextElementSibling;
      text.setAttribute('x', 0); text.setAttribute('y', 0);
      const box = text.getBBox();
      nodes[source].children.push(target);
      // A midpoint label has half the separation of the child centers.
      nodes[target].width = Math.max(nodes[target].width, box.width * 2 + 24);
      return {line, text, box, source, target};
    });
    const heights = [];
    for (const node of nodes) {
      heights[node.depth] = Math.max(heights[node.depth] || 0, node.height);
      for (const child of node.children) nodes[child].depth = node.depth + 1;
    }
    const gap = edges.reduce((value, edge) => Math.max(value, edge.box.height + 32), 64);
    const rows = [30];
    for (let depth = 1; depth < heights.length; depth++)
      rows[depth] = rows[depth - 1] + heights[depth - 1] + gap;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const node = nodes[i];
      node.occupied = node.children.reduce((sum, child) => sum + nodes[child].span, 0)
                      + Math.max(0, node.children.length - 1) * 24;
      node.span = Math.max(node.width, node.occupied);
    }
    nodes[0].left = 20;
    for (const node of nodes) {
      node.x = node.left + node.span / 2;
      node.y = rows[node.depth];
      let cursor = node.left + (node.span - node.occupied) / 2;
      for (const child of node.children) {
        nodes[child].left = cursor;
        cursor += nodes[child].span + 24;
      }
      node.rect.setAttribute('x', node.x - node.width / 2);
      node.rect.setAttribute('y', node.y);
      node.rect.setAttribute('width', node.width);
      node.rect.setAttribute('height', node.height);
      node.text.setAttribute('x', node.x - node.box.x - node.box.width / 2);
      node.text.setAttribute('y', node.y + node.height / 2 - node.box.y - node.box.height / 2);
    }
    for (const edge of edges) {
      const a = nodes[edge.source], b = nodes[edge.target];
      const top = a.y + a.height, bottom = b.y;
      edge.line.setAttribute('x1', a.x); edge.line.setAttribute('y1', top);
      edge.line.setAttribute('x2', b.x); edge.line.setAttribute('y2', bottom);
      edge.text.setAttribute('x', (a.x + b.x) / 2 - edge.box.x - edge.box.width / 2);
      edge.text.setAttribute('y', (top + bottom) / 2 - edge.box.y - edge.box.height / 2);
    }
    const width = nodes[0].span + 40;
    const height = rows[rows.length - 1] + heights[heights.length - 1] + 30;
    svg.setAttribute('width', width); svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.dataset.layout = 'measured';
    applyView();
  }
  reflow();
  if (document.fonts) document.fonts.ready.then(reflow);
})();
</script>
"""


def html_tree(tree):
    nodes, edges, width, height = layout(tree)
    content = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
               f'viewBox="0 0 {width} {height}" role="img" aria-label="AST">']
    for source, target, field in edges:
        a, b = nodes[source], nodes[target]
        content.append(f'<line data-source="{source}" data-target="{target}" x1="{a["x"]}" y1="{a["y"] + 36}" x2="{b["x"]}" y2="{b["y"]}" stroke="#64748b"/>')
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
            '.tree svg{display:block;margin:0 auto}'
            '.toolbar{display:flex;gap:8px;margin-bottom:12px}'
            'button{font:inherit;padding:6px 12px;border:1px solid #cbd5e1;border-radius:5px;cursor:pointer}'
            'button[aria-pressed="true"]{background:#152d49;color:white}'
            'text{text-anchor:middle;font-size:14px;fill:#152d49}rect{fill:#eef4fb;stroke:#2563eb}'
            '.edge-label{font-size:12px;paint-order:stroke;stroke:white;stroke-width:4px;stroke-linejoin:round}'
            '</style></head><body><h1>AST · Program</h1><div class="toolbar" role="group" aria-label="树形图显示方式">'
            '<button type="button" id="ast-fit" aria-pressed="false">适应宽度</button>'
            '<button type="button" id="ast-actual" aria-pressed="true">原始大小</button>'
            '</div><div class="tree" id="ast-tree">'
            + '\n'.join(content) + '</div>' + _REFLOW + '</body></html>\n')


def dot_tree(tree):
    nodes, edges, _, _ = layout(tree)
    lines = ['digraph AST {', '  node [shape=box];']
    lines.extend(f'  n{n["id"]} [label={json.dumps(n["text"], ensure_ascii=False)}];' for n in nodes)
    lines.extend(f'  n{a} -> n{b} [label={json.dumps(field)}];' for a, b, field in edges)
    return '\n'.join(lines + ['}']) + '\n'


def write(tree, directory):
    for suffix, render in [('txt', text_tree), ('html', html_tree), ('dot', dot_tree)]:
        (Path(directory) / f'ast.{suffix}').write_text(render(tree), encoding='utf-8')
