"""Command-line generation: validate and construct everything before writing."""
import argparse
import json
from pathlib import Path
import sys
from .errors import RuleError
from .lexspec import build_tables as lex_tables
from .grammar import read_grammar
from .lr1 import build_tables as parse_tables
from .codegen import lexer_source, parser_source
from .report import generate as render_report


def generate(lex_path, grammar_path, out):
    lex = lex_tables(lex_path)
    parser = parse_tables(read_grammar(grammar_path, lex['tokens']))
    texts = {
        'lexer.py': lexer_source(lex),
        'parser.py': parser_source(parser),
        'lexer_tables.json': json.dumps(lex, ensure_ascii=False, indent=2) + '\n',
        'parser_tables.json': json.dumps(parser, ensure_ascii=False, indent=2) + '\n',
        'report.html': render_report(lex, parser),
    }
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in texts.items():
        path = out / name
        path.write_text(text, encoding='utf-8')
        print(path)
    stats = lex['stats']
    print(f"记号 {len(lex['tokens'])}；NFA {stats['nfa_states']}；DFA {stats['dfa_states']}；"
          f"最小 DFA {stats['min_dfa_states']}；产生式 {len(parser['productions'])}；"
          f"LR(1) 状态 {parser['states']}；已消解冲突 {len(parser['conflicts'])}")
    return lex, parser


def main():
    ap = argparse.ArgumentParser(description='Lexical and canonical LR(1) analyzer generator')
    ap.add_argument('--lex', required=True)
    ap.add_argument('--grammar', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    try:
        generate(args.lex, args.grammar, args.out)
        return 0
    except (RuleError, OSError, UnicodeError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
