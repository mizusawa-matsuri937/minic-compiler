"""评审者独立复核脚本：不复用项目测试，直接按 spec 的 AC 断言。产物全部写入 scratchpad。"""
import itertools, json, os, re, shutil, subprocess, sys
from pathlib import Path
ROOT = Path("/Users/aqua_night/codex_project/编译原理/minic-compiler")
W = Path(sys.argv[1]); shutil.rmtree(W, ignore_errors=True); W.mkdir(parents=True)
PY = sys.executable
results = []
def check(ac, name, cond, detail=""):
    results.append((ac, name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), ac, name, ("" if cond else "  <<< " + str(detail)[:400]))
def run(args, cwd=ROOT, stdin=None):
    return subprocess.run(args, cwd=cwd, input=stdin, capture_output=True, text=True)
def gen(lex, grammar, out):
    return run([PY, "-m", "ccgen", "--lex", str(lex), "--grammar", str(grammar), "--out", str(out)])
def cc(src, out, *extra, stdin=None):
    return run([PY, "-m", "minic", str(src), "--frontend", str(W / "gen1"), "--out", str(out), *extra], stdin=stdin)
def files(d):
    return sorted(p.name for p in Path(d).iterdir()) if Path(d).exists() else []

# AC01
r1 = gen("rules/minic.lex", "rules/minic.grammar", W / "gen1"); r2 = gen("rules/minic.lex", "rules/minic.grammar", W / "gen2")
five = ["lexer.py", "lexer_tables.json", "parser.py", "parser_tables.json", "report.html"]
check("AC01", "两次退出码 0", r1.returncode == 0 and r2.returncode == 0, r1.stderr)
check("AC01", "五个文件", files(W / "gen1") == five, files(W / "gen1"))
check("AC01", "逐字节相同", all((W/"gen1"/f).read_bytes() == (W/"gen2"/f).read_bytes() for f in five))
src = (W/"gen1"/"lexer.py").read_text() + (W/"gen1"/"parser.py").read_text()
check("AC01", "无 ccgen/minic import", not re.search(r"^\s*(import|from)\s+(ccgen|minic)\b", src, re.M) and "ccgen" not in src and "__import__" not in src)
print("   统计:", r1.stdout.strip().splitlines()[-1])

# AC02
r = gen("tests/fixtures/calc.lex", "tests/fixtures/calc.grammar", W / "calc")
(W/"calc_in.txt").write_text("1+2*3")
t = run([PY, "-I", str(W/"calc"/"lexer.py"), str(W/"calc_in.txt"), "-o", str(W/"calc_tokens.json")], cwd=W)
p = run([PY, "-I", str(W/"calc"/"parser.py"), str(W/"calc_tokens.json")], cwd=W)
ok = r.returncode == 0 and t.returncode == 0 and p.returncode == 0
tree = json.loads(p.stdout) if ok else {}
def leaves(n):
    return [n["lexeme"]] if "lexeme" in n else [x for c in n["children"] for x in leaves(c)]
kids = [c["type"] for c in tree.get("children", [])]
right = tree["children"][2] if ok else {}
check("AC02", "calc 生成与分析成功", ok, r.stderr + t.stderr + p.stderr)
check("AC02", "根 E，孩子 E + T", tree.get("type") == "E" and kids == ["E", "+", "T"], kids)
check("AC02", "右 T 的孩子 T * F", [c["type"] for c in right.get("children", [])] == ["T", "*", "F"])
check("AC02", "叶子词素", leaves(tree) == ["1", "+", "2", "*", "3"] if ok else False)

# AC03 / AC04：直接用生成器内部接口造自动机
sys.path.insert(0, str(ROOT))
from ccgen import regex as rx, nfa as nf, dfa as df
def automata(pattern):
    n = nf.NFA(); n.add(rx.parse(pattern), 0); n.canonicalize(); d = df.determinize(n); return n, d, df.minimize(d)
cases = {
 r"(a|b)*abb": (["abb", "aabb", "babb"], ["ab", "abba", ""]),
 r"[0-9]+": (["0", "007"], ["", "1a"]),
 r"[a-zA-Z_][a-zA-Z0-9_]*": (["_x1", "A"], ["1x"]),
 r"a?b+": (["b", "abbb"], ["a", "aab"]),
 r"//[^\n]*": (["//", "// 中文 x"], ["/", "//a\nb"]),
 r"\+\*": (["+*"], ["+", "*+", "+**", ""]),
}
for pat, (yes, no) in cases.items():
    n, d, m = automata(pat)
    bad = [s for s in yes if not (n.accepts(s) and d.accepts(s) and m.accepts(s))] + [s for s in no if (n.accepts(s) or d.accepts(s) or m.accepts(s))]
    check("AC03", pat, not bad, bad)
n, d, m = automata(r"(a|b)*abb")
check("AC04", "最小 DFA 4 状态", len(m.trans) == 4, len(m.trans))
check("AC04", "DFA 状态数 >= 4", len(d.trans) >= 4, len(d.trans))
bad = [s for L in range(9) for s in map("".join, itertools.product("ab", repeat=L))
       if not (n.accepts(s) == d.accepts(s) == m.accepts(s) == s.endswith("abb"))]
check("AC04", "长度<=8 穷举 511 串三者一致", not bad, bad[:5])
print("   (a|b)*abb: NFA %d, DFA %d, minDFA %d" % (len(n.edges), len(d.trans), len(m.trans)))
lt = json.loads((W/"gen1"/"lexer_tables.json").read_text()); st = lt["stats"]
check("AC04", "mini-C 三个状态数且 min<=dfa", st["min_dfa_states"] <= st["dfa_states"] and st["nfa_states"] > 0, st)
print("   mini-C:", st)

# AC05
r = run([PY, str(W/"gen1"/"lexer.py"), "tests/fixtures/lex_ok.mc"]); tk = json.loads(r.stdout)
kinds = " ".join(t["kind"] for t in tk["tokens"])
check("AC05", "16 个记号与种别序列", kinds == "int IDENT = NUMBER ; if ( IDENT >= NUMBER ) write ( IDENT ) ;" and not tk["errors"], kinds)
check("AC05", "前四个二元式", [(t["code"], t["attr"]) for t in tk["tokens"][:4]] == [(1, None), (7, "integer"), (19, None), (8, "10")])
check("AC05", "位置 1:5 与 2:13", (tk["tokens"][1]["line"], tk["tokens"][1]["col"]) == (1, 5) and [(t["line"], t["col"]) for t in tk["tokens"] if t["kind"] == ">="] == [(2, 13)])
codes = {t["name"]: t["code"] for t in lt["tokens"]}
expect = dict(zip("int if else while read write IDENT NUMBER + - * / == != <= >= < > = ; , ( ) { }".split(), range(1, 26)))
check("AC05", "种别码 1..25 与附录顺序一致", {k: v for k, v in codes.items() if v is not None} == expect)

# AC06
r = cc("tests/fixtures/lex_error.mc", W/"o_lexerr")
errs = [l for l in r.stderr.splitlines() if l.strip()]
check("AC06", "退出码 1", r.returncode == 1, r.returncode)
check("AC06", "恰两条诊断及位置字符", len(errs) == 2 and errs[0].startswith("tests/fixtures/lex_error.mc:1:11: 词法错误[L001]") and "@" in errs[0]
      and errs[1].startswith("tests/fixtures/lex_error.mc:2:7: 词法错误[L001]") and "$" in errs[1], errs)
check("AC06", "只有 tokens 文件", files(W/"o_lexerr") == ["tokens.json", "tokens.txt"], files(W/"o_lexerr"))

# AC07
pt = json.loads((W/"gen1"/"parser_tables.json").read_text())
appendix = """S -> Program
Program -> StatementList
StatementList -> Statement StatementList
StatementList ->
Statement -> VarDecl
Statement -> AssignStmt
Statement -> IfStmt
Statement -> WhileStmt
Statement -> ReadStmt
Statement -> WriteStmt
Statement -> CompoundStmt
VarDecl -> int IDENT ;
VarDecl -> int IDENT = Expr ;
AssignStmt -> IDENT = Expr ;
CompoundStmt -> { StatementList }
IfStmt -> if ( Expr ) Statement
IfStmt -> if ( Expr ) Statement else Statement
WhileStmt -> while ( Expr ) Statement
ReadStmt -> read ( IDENT ) ;
WriteStmt -> write ( Expr ) ;
Expr -> RelExpr
RelExpr -> AddExpr < AddExpr
RelExpr -> AddExpr > AddExpr
RelExpr -> AddExpr == AddExpr
RelExpr -> AddExpr != AddExpr
RelExpr -> AddExpr <= AddExpr
RelExpr -> AddExpr >= AddExpr
RelExpr -> AddExpr
AddExpr -> AddExpr + Term
AddExpr -> AddExpr - Term
AddExpr -> Term
Term -> Term * Factor
Term -> Term / Factor
Term -> Factor
Factor -> IDENT
Factor -> NUMBER
Factor -> ( Expr )""".splitlines()
got = [f"{p['lhs']} -> {' '.join(p['rhs'])}".rstrip() for p in pt["productions"][1:]]
check("AC07", "38 条且 1-37 与附录一致", len(pt["productions"]) == 38 and got == [a.rstrip() for a in appendix] and pt["productions"][0]["id"] == 0 and [p["id"] for p in pt["productions"]] == list(range(38)), [x for x in zip(got, appendix) if x[0] != x[1].rstrip()][:3])
check("AC07", "16 个 FIRST，FIRST(Expr)", len(pt["first"]) == 16 and set(pt["first"]["Expr"]) == {"IDENT", "NUMBER", "("}, pt["first"].get("Expr"))
cf = pt["conflicts"]
check("AC07", "冲突全为 else/归约16/移进", cf and all(c["lookahead"] == "else" and c["reduce"] == 16 and c["kind"] == "shift-reduce" and c["resolution"] == "shift" for c in cf), cf)
print("   LR(1) 状态数:", pt["states"], "冲突:", len(cf))

# AC08
r = gen("tests/fixtures/calc.lex", "tests/fixtures/ambiguous.grammar", W/"amb")
check("AC08", "(a) 退出 2、无输出、指出 + 冲突", r.returncode == 2 and not (W/"amb").exists() and "+" in r.stderr and "移进-归约" in r.stderr and "E -> E + E ·" in r.stderr, r.stderr[:300])
g = "\n".join(l for l in (ROOT/"rules/minic.grammar").read_text().splitlines() if not l.startswith("%prefer"))
(W/"noprefer.grammar").write_text(g + "\n")
r = gen("rules/minic.lex", W/"noprefer.grammar", W/"nopref")
check("AC08", "(b) 退出 2、无输出、指出 else 冲突", r.returncode == 2 and not (W/"nopref").exists() and "'else'" in r.stderr and "移进-归约" in r.stderr, r.stderr[:200])

# AC09
def bad_rules(tag, lex_text, gram_text, needle, where):
    (W/f"{tag}.lex").write_text(lex_text); (W/f"{tag}.grammar").write_text(gram_text)
    r = gen(W/f"{tag}.lex", W/f"{tag}.grammar", W/f"bad_{tag}")
    check("AC09", f"({tag}) 退出 2、文件名行号、无输出", r.returncode == 2 and where in r.stderr and needle in r.stderr and not (W/f"bad_{tag}").exists(), r.stderr[:200])
bad_rules("a", "A a\nX (ab\n", "S -> A\n", "", "a.lex:2:")
bad_rules("b", "A a\n", "S -> A\nS -> foo\n", "foo", "b.grammar:2:")
bad_rules("c", "A a\n", "S -> A A A => N(x=$5)\n", "", "c.grammar:1:")
bad_rules("d", "A a\nX a*\n", "S -> A\n", "空串", "d.lex:2:")

# AC10 / AC11
def B(n):
    return n["value"] if n["type"] == "Number" else n["name"] if n["type"] == "Identifier" else f"{n['op']}({B(n['left'])}, {B(n['right'])})"
r = cc("tests/fixtures/expr.mc", W/"o_expr", "--stop-after", "ast"); ast = json.loads((W/"o_expr"/"ast.json").read_text())
b = ast["body"]
check("AC10", "Program 三项", ast["type"] == "Program" and len(b) == 3 and r.returncode == 0)
check("AC10", "三个表达式结构", b[0]["type"] == "VarDecl" and b[0]["name"] == "x" and B(b[0]["init"]) == "-(+(1, *(2, 3)), 4)" and b[1]["type"] == "Assign" and B(b[1]["value"]) == "*(+(1, 2), 3)" and B(b[2]["value"]) == "/(/(8, 4), 2)", [B(b[0]["init"]), B(b[1]["value"]), B(b[2]["value"])])
r = cc("tests/fixtures/dangling_else.mc", W/"o_dang", "--stop-after", "ast"); ast = json.loads((W/"o_dang"/"ast.json").read_text())
outer = ast["body"][3]
check("AC11", "外层 If 无 else，内层有 else", outer["type"] == "If" and "else" not in outer and outer["then"]["type"] == "If" and "else" in outer["then"])

# AC12
r = cc("tests/fixtures/syntax_chain.mc", W/"o_chain"); e = [l for l in r.stderr.splitlines() if l.strip()]
exp = re.findall(r"'([^']+)'", e[0].split("期望")[1]) if e and "期望" in e[0] else None
check("AC12", "chain: 退出1、1:15、实际 <、期望恰为 + - * / ;", r.returncode == 1 and len(e) == 1 and e[0].startswith("tests/fixtures/syntax_chain.mc:1:15: 语法错误[P001]") and "遇到 '<'" in e[0] and exp == ["+", "-", "*", "/", ";"], e)
check("AC12", "chain: 只有 tokens", files(W/"o_chain") == ["tokens.json", "tokens.txt"], files(W/"o_chain"))
r = cc("tests/fixtures/syntax_eof.mc", W/"o_eof"); e = [l for l in r.stderr.splitlines() if l.strip()]
check("AC12", "eof: 退出1、1:10、输入结束、期望含 ;", r.returncode == 1 and len(e) == 1 and e[0].startswith("tests/fixtures/syntax_eof.mc:1:10: 语法错误[P001]") and "遇到 输入结束" in e[0] and "';'" in e[0], e)
check("AC12", "eof: 只有 tokens", files(W/"o_eof") == ["tokens.json", "tokens.txt"])

# AC13
r = cc("tests/fixtures/semantic_error.mc", W/"o_sem"); e = [l for l in r.stderr.splitlines() if l.strip()]
want = [("2:1", "S002", "a"), ("3:1", "S001", "b"), ("4:9", "S003", ""), ("6:1", "S001", "d")]
ok = r.returncode == 1 and len(e) == 4 and all(l.startswith(f"tests/fixtures/semantic_error.mc:{pos}: 语义错误[{code}]") and name in l.split("]: ")[1] for l, (pos, code, name) in zip(e, want))
check("AC13", "四条诊断顺序/位置/代码", ok, e)
fs = files(W/"o_sem")
check("AC13", "有 tokens.* ast.*，无 .ll", {"tokens.json", "tokens.txt", "ast.json"} <= set(fs) and not any(f.endswith(".ll") for f in fs), fs)

# AC14
ra = cc("examples/demo.mc", W/"o_ir1", "--stop-after", "ir"); rb = cc("examples/demo.mc", W/"o_ir2", "--stop-after", "ir")
ll = (W/"o_ir1"/"demo.ll").read_text(); lines = ll.splitlines()
entry = lines[lines.index("entry:"):]; first_br = next(i for i, l in enumerate(entry) if l.strip().startswith("br "))
allocas = [i for i, l in enumerate(entry) if "alloca i32" in l]
check("AC14", "退出 0，define main，ret", ra.returncode == 0 and rb.returncode == 0 and "define i32 @main()" in ll and lines[-2].strip() == "ret i32 0" and lines[-1] == "}")
check("AC14", "4 条 alloca 且在首个 br 前", len(allocas) == 4 and max(allocas) < first_br, allocas)
check("AC14", "指令种类", all(k in ll for k in ["icmp sle", "icmp eq", "mul i32", "sdiv i32", "sub i32", "add i32"]))
check("AC14", "1 scanf 调用 4 printf 调用", len(re.findall(r"call i32 \(ptr, \.\.\.\) @scanf", ll)) == 1 and len(re.findall(r"call i32 \(ptr, \.\.\.\) @printf", ll)) == 4)
check("AC14", "while/if 标号与条件跳转", all(k in ll for k in ["while.cond.", "while.body.", "while.end.", "if.then.", "if.else.", "if.end."]) and ll.count("br i1") == 2)
check("AC14", "四个文件两次相同", all((W/"o_ir1"/f).read_bytes() == (W/"o_ir2"/f).read_bytes() for f in ["tokens.json", "ast.json", "ast.html", "demo.ll"]))
check("AC14", "无可执行文件", not any(f in files(W/"o_ir1") for f in ["demo", "demo.s", "demo.opt.ll"]), files(W/"o_ir1"))

# AC15
outs = {}
for lvl in ("0", "2"):
    r = cc("examples/demo.mc", W/f"o_demo{lvl}", f"-O{lvl}")
    check("AC15", f"-O{lvl} 编译退出 0 且产物齐全", r.returncode == 0 and {"demo.opt.ll", "demo.s", "demo"} <= set(files(W/f"o_demo{lvl}")), r.stderr[-300:])
    for inp in ("5", "10"):
        x = subprocess.run([str(W/f"o_demo{lvl}"/"demo")], input=inp + "\n", capture_output=True, text=True)
        outs[(lvl, inp)] = (x.returncode, x.stdout)
check("AC15", "输入 5 → 15 120 1", outs[("2", "5")] == (0, "15\n120\n1\n"), outs[("2", "5")])
check("AC15", "输入 10 → 55 3628800 0", outs[("2", "10")] == (0, "55\n3628800\n0\n"), outs[("2", "10")])
check("AC15", "-O0 与 -O2 输出相同", outs[("0", "5")] == outs[("2", "5")] and outs[("0", "10")] == outs[("2", "10")])

# AC16
table = [("tests/fixtures/run/arith.mc", "", "3 -3 -3 14 20 5"), ("tests/fixtures/run/rel.mc", "", "1 0 1 0 1 0 1"),
         ("tests/fixtures/run/scope.mc", "", "2 1 1 0"), ("tests/fixtures/run/control.mc", "", "0 100 2 3"),
         ("tests/fixtures/run/wrap.mc", "", "-2147483648"), ("tests/fixtures/run/io.mc", "3 -10", "13"),
         ("tests/fixtures/dangling_else.mc", "", "2")]
for path, stdin, want in table:
    for lvl in ("0", "2"):
        d = W/("o_run_" + Path(path).stem + lvl); r = cc(path, d, f"-O{lvl}")
        x = subprocess.run([str(d/Path(path).stem)], input=stdin, capture_output=True, text=True) if r.returncode == 0 else None
        check("AC16", f"{Path(path).name} -O{lvl}", x is not None and x.returncode == 0 and x.stdout == want.replace(" ", "\n") + "\n", (r.stderr[-200:], x and x.stdout))

# AC17
r = cc("examples/demo.mc", W/"o_noclang", "--clang", "/nonexistent/clang"); fs = files(W/"o_noclang")
check("AC17", "退出 3、说明 clang、保留前端产物", r.returncode == 3 and "clang" in r.stderr and {"tokens.json", "tokens.txt", "ast.json", "demo.ll"} <= set(fs) and not {"demo", "demo.s", "demo.opt.ll"} & set(fs), (r.returncode, fs))

# AC18（自动部分）
r = cc("examples/demo.mc", W/"o_ast", "--stop-after", "ast"); fs = files(W/"o_ast")
h = (W/"o_ast"/"ast.html").read_text(); a = (W/"o_ast"/"ast.json").read_text()
def count(n):
    return (1 if isinstance(n, dict) and "type" in n else 0) + sum(count(v) for v in (n.values() if isinstance(n, dict) else n if isinstance(n, list) else []))
check("AC18", "四个 AST 文件", {"ast.json", "ast.txt", "ast.html", "ast.dot"} <= set(fs), fs)
check("AC18", "自包含且含 svg", h.count("<svg") == 1 and not any(k in h for k in ["<link", "<script src", 'src="http', 'href="http']))
check("AC18", "ast-node 数 = 结点数", h.count('class="ast-node"') == count(json.loads(a)), (h.count('class="ast-node"'), count(json.loads(a))))

# AC19
rep = (W/"gen1"/"report.html").read_text()
titles = re.findall(r"<h2>(.*?)</h2>", rep)
check("AC19", "自包含", not any(k in rep for k in ["<link", "<script", 'src="http', 'href="http']))
print("   报告小节:", titles)
check("AC19", "九项内容依次出现", len(titles) == 9, titles)
def rows(tid):
    m = re.search(rf'<table id="{tid}">.*?<tbody>(.*?)</tbody>', rep, re.S); return m.group(1).count("<tr>")
check("AC19", "状态数与表一致", all(f"<td>{st[k]}</td>" in rep for k in st))
check("AC19", "产生式 38 行、ACTION/GOTO 行数=状态数", rows("production-table") == 38 and rows("action-table") == pt["states"] == rows("goto-table"), (rows("production-table"), rows("action-table")))
check("AC19", "冲突节写明 else 移进", "else" in rep.split('id="conflicts"')[1] and "移进" in rep.split('id="conflicts"')[1])

# AC20
ext = W/"outside"; ext.mkdir()
t = run([PY, "-I", str(W/"gen1"/"lexer.py"), str(ROOT/"examples/demo.mc"), "-o", "tokens.json"], cwd=ext)
p = run([PY, "-I", str(W/"gen1"/"parser.py"), "tokens.json", "-o", "ast.json"], cwd=ext)
check("AC20", "独立运行退出 0", t.returncode == 0 and p.returncode == 0, t.stderr + p.stderr)
check("AC20", "与 minic 产物逐字节相同", (ext/"tokens.json").read_bytes() == (W/"o_ast"/"tokens.json").read_bytes() and (ext/"ast.json").read_bytes() == (W/"o_ast"/"ast.json").read_bytes())

# AC22
ast = json.loads(a); kinds = set(re.findall(r'"type": "(\w+)"', a))
has_else = any(True for m in re.finditer(r'"type": "If"', a)) and '"else"' in a
check("AC22", "六种语句结点", {"VarDecl", "Assign", "If", "While", "Read", "Write"} <= kinds and has_else, kinds)
env = dict(os.environ, MINIC_BUILD_DIR=str(W/"demo_build"), MINIC_OUT_DIR=str(W/"demo_out"))
r = subprocess.run(["bash", "scripts/demo.sh"], cwd=ROOT, input="5\n", capture_output=True, text=True, env=env)
check("AC22", "演示脚本退出 0，末三行 15 120 1，之前列出产物", r.returncode == 0 and r.stdout.splitlines()[-3:] == ["15", "120", "1"] and "ast.html" in r.stdout and "demo.ll" in r.stdout, r.stdout[-300:] + r.stderr[-300:])

fails = [x for x in results if not x[2]]
print(f"\n合计 {len(results)} 项断言，失败 {len(fails)} 项")
