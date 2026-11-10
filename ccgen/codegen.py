"""Serialize tables into independent, standard-library-only drivers."""
from pathlib import Path
from pprint import pformat


def lexer_source(tables):
    values = dict(TOKENS=tables['tokens'], START=tables['start'],
                  ACCEPT={int(k): v for k, v in tables['accept'].items()},
                  TRANS={int(k): v for k, v in tables['trans'].items()},
                  OTHER_TRANS={int(k): v for k, v in tables['other_trans'].items()})
    return render('lexer', values)


def render(name, values):
    template = Path(__file__).with_name('templates') / f'{name}_template.py'
    header = '# Generated analyzer. Tables and driver are self-contained.\n'
    assignments = '\n'.join(f'{k} = {pformat(v, sort_dicts=False, width=100)}' for k, v in values.items())
    return header + assignments + '\n\n' + template.read_text(encoding='utf-8')
