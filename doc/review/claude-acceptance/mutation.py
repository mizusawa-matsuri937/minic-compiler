"""变异测试：在仓库副本中逐个植入缺陷，看项目自带测试能否发现。不改动原仓库。"""
import re, shutil, subprocess, sys
from pathlib import Path
ROOT = Path("/Users/aqua_night/codex_project/编译原理/minic-compiler"); W = Path(sys.argv[1])
MUTANTS = [
 ("最小化不做细分", "ccgen/dfa.py", "        if len(refined) == len(groups):\n            break", "        break"),
 ("规则优先级取反", "ccgen/dfa.py", "accept[i] = min(rules)", "accept[i] = max(rules)"),
 ("取消最长匹配", "ccgen/templates/lexer_template.py", "                last = cursor, ACCEPT[state]", "                last = cursor, ACCEPT[state]\n                break"),
 ("词法错误不跳过整字符而停止", "ccgen/templates/lexer_template.py", "            end = position + 1\n", "            end = len(text)\n"),
 ("else 冲突改取归约", "ccgen/lr1.py", "                    selected = shifts[0]", "                    selected = reductions[0]"),
 ("闭包忽略向前看传播", "ccgen/lr1.py", "first_sequence(rhs[dot + 1:] + [lookahead])", "first_sequence([lookahead])"),
 ("FIRST 不处理可空符号", "ccgen/lr1.py", "                if symbol not in nullable:\n                    break\n            else:", "                break\n            else:"),
 ("期望集合取全部终结符", "ccgen/templates/parser_template.py", "[t for t in TERMINALS if t in row]", "list(TERMINALS)"),
 ("结点位置取最后一个记号", "ccgen/templates/parser_template.py", "location = positions[-count] if count", "location = positions[-1] if count"),
 ("块不建立作用域", "minic/semantic.py", "            if kind == 'Block':\n                scopes.append({})\n                pending.append(('leave', None))\n", ""),
 ("先声明后查初值", "minic/semantic.py", "            pending.append(('declare', node))\n            if 'init' in node:\n                pending.append(('visit', node['init']))", "            if 'init' in node:\n                pending.append(('visit', node['init']))\n            pending.append(('declare', node))"),
 ("越界判断差一", "minic/semantic.py", "normalized > '2147483647'", "normalized > '2147483648'"),
 ("除法改无符号", "minic/irgen.py", "'/': 'sdiv'", "'/': 'udiv'"),
 ("减法操作数颠倒", "minic/irgen.py", "f'{arithmetic[op]} i32 {left}, {right}'", "f'{arithmetic[op]} i32 {right}, {left}'"),
 ("<= 误作 <", "minic/irgen.py", "'<=': 'sle'", "'<=': 'slt'"),
 ("未初始化不置 0", "minic/irgen.py", "self.emit(f\"store i32 {value}, ptr %{current['_slot']}\")", "('init' in current or kind == 'Assign') and self.emit(f\"store i32 {value}, ptr %{current['_slot']}\")"),
 ("加法带 nsw", "minic/irgen.py", "'+': 'add'", "'+': 'add nsw'"),
 ("clang 失败仍返回成功", "minic/__main__.py", "        return 3", "        return 0"),
 ("语法错误仍写 AST", "minic/__main__.py", "        emit(args.source, [parse_diagnostic(error)])\n        return 1", "        emit(args.source, [parse_diagnostic(error)])\n        paths['ast.json'].write_text('{}')\n        return 1"),
 ("规则出错仍写文件", "ccgen/__main__.py", "    lex = lex_tables(lex_path)\n", "    Path(out).mkdir(parents=True, exist_ok=True)\n    (Path(out) / 'lexer.py').write_text('')\n    lex = lex_tables(lex_path)\n"),
]
only = set(sys.argv[2:])
for i, (name, rel, old, new) in enumerate(MUTANTS):
    if only and str(i) not in only: continue
    d = W / f"m{i}"; shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(ROOT, d, ignore=shutil.ignore_patterns(".git", "build", "out", "__pycache__", ".idea", "doc"))
    p = d / rel; text = p.read_text(encoding="utf-8")
    if text.count(old) != 1: print(f"[{i}] {name}: 变异点未唯一匹配（{text.count(old)}）"); continue
    p.write_text(text.replace(old, new), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=d, capture_output=True, text=True)
    tail = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""
    failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+)", r.stderr, re.M)))
    print(f"[{i}] {'发现' if r.returncode else '漏过!!'}  {name}  -> {tail}  {', '.join(failed[:4])}{' …' if len(failed) > 4 else ''}", flush=True)
    shutil.rmtree(d, ignore_errors=True)
