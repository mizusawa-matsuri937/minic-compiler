"""Source diagnostics have one stable, shared rendering."""
import sys

CATEGORIES = {'L': '词法错误', 'P': '语法错误', 'S': '语义错误'}


def emit(path, diagnostics):
    for item in diagnostics:
        category = CATEGORIES[item['code'][0]]
        print(f"{path}:{item['line']}:{item['col']}: {category}[{item['code']}]: {item['message']}",
              file=sys.stderr)


def parse_diagnostic(error):
    return dict(code='P001', line=error.line, col=error.col, message=str(error))
