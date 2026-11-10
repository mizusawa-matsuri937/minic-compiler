"""Self-contained construction report, built from the exported table data."""
from html import escape


def table(identifier, headings, rows):
    header = '<thead><tr>' + ''.join(f'<th>{escape(str(h))}</th>' for h in headings) + '</tr></thead>'
    body = '<tbody>' + ''.join('<tr>' + ''.join(f'<td>{escape(str(c))}</td>' for c in row) + '</tr>'
                              for row in rows) + '</tbody>'
    return f'<div class="scroll"><table id="{identifier}">{header}{body}</table></div>'


def alphabet_groups(lex):
    """Merge adjacent ASCII columns iff every state has the same transitions."""
    count = lex['stats']['min_dfa_states']
    groups = []
    for code in range(128):
        signature = tuple(lex['trans'][str(state)].get(chr(code)) for state in range(count))
        if groups and groups[-1][2] == signature:
            groups[-1][1] = code
        else:
            groups.append([code, code, signature])
    return groups


def character(code):
    return 'SPACE (U+0020)' if code == 32 else repr(chr(code))[1:-1]


def generate(lex, parser):
    sections = []
    def section(identifier, title, body):
        sections.append(f'<section id="{identifier}"><h2>{len(sections) + 1}. {title}</h2>{body}</section>')

    section('tokens', '记号与正规式', table('token-table', ['记号', '种别码', '正规式', '丢弃', '固定串'],
            [[t['name'], '-' if t['code'] is None else t['code'], t['regex'], t['skip'], t['fixed']]
             for t in lex['tokens']]))
    section('automata', '三个状态数', table('stats-table', ['构造阶段', '状态数'],
            [[key, value] for key, value in lex['stats'].items()]))
    groups = alphabet_groups(lex)
    columns = [character(lo) if lo == hi else character(lo) + '–' + character(hi) for lo, hi, _ in groups]
    rows = []
    for state in range(lex['stats']['min_dfa_states']):
        row = [state, lex['accept'].get(str(state), '-')]
        row += ['-' if signature[state] is None else signature[state] for _, _, signature in groups]
        row += [lex['other_trans'].get(str(state), '-')]
        rows.append(row)
    section('dfa', '最小 DFA 转换表', table('dfa-table', ['状态', '接受记号'] + columns + ['OTHER'], rows))
    section('productions', '编号产生式', table('production-table', ['编号', '左部', '右部', '构造动作'],
            [[p['id'], p['lhs'], ' '.join(p['rhs']) or 'ε', str(p['action'])] for p in parser['productions']]))
    section('first', 'FIRST 集', table('first-table', ['非终结符', 'FIRST'],
            [[symbol, ', '.join(values)] for symbol, values in parser['first'].items()]))
    section('lr1', 'LR(1) 项目集数量', f'<p id="lr1-count">{parser["states"]}</p>')
    def action_text(value):
        if value is None:
            return '-'
        name, argument = value
        return {'shift': 's', 'reduce': 'r'}.get(name, 'acc') + (str(argument) if name != 'accept' else '')
    section('action', 'ACTION 表', table('action-table', ['状态'] + parser['terminals'],
            [[i] + [action_text(parser['action'][str(i)].get(t)) for t in parser['terminals']]
             for i in range(parser['states'])]))
    section('goto', 'GOTO 表', table('goto-table', ['状态'] + parser['nonterminals'],
            [[i] + [parser['goto'][str(i)].get(t, '-') for t in parser['nonterminals']]
             for i in range(parser['states'])]))
    section('conflicts', '冲突与消解', table('conflict-table', ['状态', '向前看', '类型', '移进', '归约', '消解'],
            [[c['state'], c['lookahead'], c['kind'], c['shift'], c['reduce'],
              'shift（移进）' if c['resolution'] == 'shift' else c['resolution']] for c in parser['conflicts']]))
    return ('<!doctype html>\n<html lang="zh"><head><meta charset="utf-8"><title>分析器构造报告</title>'
            '<style>body{font-family:system-ui,sans-serif;margin:32px;color:#152d49;background:#f8fafc}'
            'h2{margin-top:32px}.scroll{overflow:auto;max-height:600px;background:white}'
            'table{border-collapse:collapse;font:13px monospace}th,td{border:1px solid #cbd5e1;'
            'padding:7px 10px;white-space:pre}th{background:#eef4fb;position:sticky;top:0}'
            'tr:nth-child(even){background:#f8fafc}</style></head><body><h1>分析器构造报告</h1>'
            + '\n'.join(sections) + '</body></html>\n')
