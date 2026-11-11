"""对抗性验证 2：mini-C 边界用例 + 随机程序与参考解释器的差分。"""
import json, os, random, re, shutil, subprocess, sys
from pathlib import Path
ROOT = Path("/Users/aqua_night/codex_project/编译原理/minic-compiler")
W = Path(sys.argv[1]); shutil.rmtree(W, ignore_errors=True); W.mkdir(parents=True)
PY = sys.executable
FE = W / "fe"
subprocess.run([PY, "-m", "ccgen", "--lex", "rules/minic.lex", "--grammar", "rules/minic.grammar", "--out", str(FE)], cwd=ROOT, check=True, capture_output=True)
def P(ok, name, detail=""):
    print("PASS" if ok else "FAIL", name, "" if ok else f"  <<< {str(detail)[:600]}")
    return ok
n = 0
def cc(text, *extra, stdin="", name=None, raw=False):
    global n; n += 1
    d = W / f"c{n}"; d.mkdir(); src = d / (name or "p.mc")
    src.write_bytes(text if raw else text.encode("utf-8"))
    r = subprocess.run([PY, "-m", "minic", str(src), "--frontend", str(FE), "--out", str(d / "o"), *extra], cwd=ROOT, input=stdin, capture_output=True, text=True)
    return r, d / "o"
def runs(text, want, stdin="", **kw):
    r, o = cc(text, "--run", stdin=stdin, **kw)
    return r.returncode == 0 and r.stdout == want, (r.returncode, r.stdout, r.stderr[-300:])
def diag(text, **kw):
    r, o = cc(text, **kw)
    return r.returncode, [re.sub(r"^.*?p\.mc:", "", l) for l in r.stderr.splitlines() if l.strip()], o

P(*runs("", ""), ) if False else None
for name, text, want in [
    ("空文件", "", ""), ("只有空白和注释", "  \n\t// 只有注释\n", ""), ("注释在文件末尾且无换行", "write(1); // end", "1\n"),
    ("CRLF 行结束", "int a = 2;\r\nwrite(a);\r\n", "2\n"), ("制表符缩进", "int a = 3;\n\twrite(a);\n", "3\n"),
    ("前导零不是八进制", "int x = 007; write(x); write(010);", "7\n10\n"),
    ("最大整数与多前导零", "write(2147483647); write(00000000002147483647);", "2147483647\n2147483647\n"),
    ("变量名与内部名字相近", "int t1 = 3; int entry = 4; int main = 5; int printf = 6; int scanf = 7; int addr = 1; write(t1 + entry + main + printf + scanf + addr);", "26\n"),
    ("关键字前缀的标识符", "int iff = 1; int int1 = 2; int whilex = 3; int readx = 4; int _ = 5; write(iff + int1 + whilex + readx + _);", "15\n"),
    ("紧凑无空格", "int a=1;int b=2;if(a<b)write(a+b*2);else write(0);", "5\n"),
    ("a/ /b 不是注释", "int a = 8; int b = 2; write(a /\n b);", "4\n"),
    ("关系结果参与运算", "write((1 < 2) + (2 < 1) * 5 + (3 == 3));", "2\n"),
    ("乘法回绕", "int a = 65536; write(a * a); write(a * a + 1); int b = 46341; write(b * b);", "0\n1\n-2147479015\n"),
    ("减法回绕", "int m = 0 - 2147483647; write(m - 2);", "2147483647\n"),
    ("负数除法向零截断", "write((0 - 7) / 2); write(7 / (0 - 2)); write((0 - 7) / (0 - 2)); write((0-1)/2);", "-3\n-3\n3\n0\n"),
    ("循环体内声明每次置 0", "int i = 0; while (i < 3) { int y; y = y + 5; write(y); i = i + 1; }", "5\n5\n5\n"),
    ("else 分支独立作用域", "int x = 1; if (0) int x = 2; else int x = 3; write(x);", "1\n"),
    ("多层遮蔽", "int x = 1; { int x = 2; { int x = 3; write(x); } write(x); } write(x);", "3\n2\n1\n"),
    ("块后同名再声明", "{ int a = 1; write(a); } { int a = 2; write(a); }", "1\n2\n"),
    ("else-if 链", "int n = 3; if (n == 1) write(10); else if (n == 2) write(20); else if (n == 3) write(30); else write(40);", "30\n"),
    ("嵌套循环", "int i = 1; while (i <= 3) { int j = 1; while (j <= i) { write(i * 10 + j); j = j + 1; } i = i + 1; }", "11\n21\n22\n31\n32\n33\n"),
    ("200 层括号", "write(" + "(" * 200 + "7" + ")" * 200 + ");", "7\n"),
    ("空块与空 if 体", "int a = 1; {} { {} } if (a) {} else {} while (0) {} write(a);", "1\n"),
]:
    P(*runs(text, want), ) if False else None
    ok, d = runs(text, want); P(ok, "运行: " + name, d)
ok, d = runs("int a; int b; int c; read(a); read(b); read(c); write(a + b + c);", "-4\n", stdin="1\n-2147483648\n   2147483643"); P(ok, "read: 多行输入与边界值", d)
r, o = cc("int a; read(a); write(a);", "--run", stdin="42\n"); P(r.returncode == 0 and r.stdout == "42\n" and "42" not in r.stderr, "--run 的标准输出只有程序输出", (r.stdout, r.stderr[-200:]))

for name, text, rc, want in [
    ("数字紧跟字母", "int x = 123abc;", 1, ["1:12: 语法错误[P001]"]),
    ("逗号进入语法分析被拒", "int x = 1, y;", 1, ["1:10: 语法错误[P001]"]),
    ("关键字不能作变量名", "int if;", 1, ["1:5: 语法错误[P001]"]),
    ("else 无 if", "else write(1);", 1, ["1:1: 语法错误[P001]"]),
    ("缺右括号", "write((1 + 2);", 1, ["1:14: 语法错误[P001]"]),
    ("一元负号不支持", "int x = -1;", 1, ["1:9: 语法错误[P001]"]),
    ("=== 被切成 == 与 =", "int x = 1 === 2;", 1, ["1:13: 语法错误[P001]"]),
    ("赋值不是表达式", "int a; int b; a = b = 1;", 1, ["1:21: 语法错误[P001]"]),
    ("未闭合的块", "{ int a;", 1, ["1:9: 语法错误[P001]"]),
    ("初值引用自身", "int x = x;", 1, ["1:9: 语义错误[S001]"]),
    ("块外使用块内变量", "{ int a = 1; }\na = 2;", 1, ["2:1: 语义错误[S001]"]),
    ("if 体内声明不外泄", "if (1) int z = 1;\nwrite(z);", 1, ["2:7: 语义错误[S001]"]),
    ("同一块内重复声明", "{ int a; int a; }", 1, ["1:10: 语义错误[S002]"]),
    ("2147483648 越界而 2147483647 合法", "int a = 2147483647;\nint b = 2147483648;\nint c = 99999999999999999999;", 1, ["2:9: 语义错误[S003]", "3:9: 语义错误[S003]"]),
    ("非 ASCII 标识符", "int 变量;", 1, ["1:5: 词法错误[L001]", "1:6: 词法错误[L001]"]),
    ("词法错误后不再报语法错误", "int a = 1 @ ;;;", 1, ["1:11: 词法错误[L001]"]),
    ("单独的 ! 非法", "int a = 1 ! 2;", 1, ["1:11: 词法错误[L001]"]),
]:
    code, lines, o = diag(text)
    P(code == rc and len(lines) == len(want) and all(l.startswith(w) for l, w in zip(lines, want)), "诊断: " + name, (code, lines))

r, o = cc("int a = 1;", "--stop-after", "tokens"); P(r.returncode == 0 and sorted(p.name for p in o.iterdir()) == ["tokens.json", "tokens.txt"], "--stop-after tokens 只产生记号文件")
rows = (o / "tokens.txt").read_text().splitlines(); P(len(rows) == 5 and all(len(x.split("\t")) == 4 for x in rows) and rows[1].split("\t")[1] == "(7, a)" and rows[0].split("\t")[1] == "(1, -)", "tokens.txt 每行四列、二元式格式", rows)
r = subprocess.run([PY, "-m", "minic", str(W / "nope.mc"), "--frontend", str(FE), "--out", str(W / "x1")], cwd=ROOT, capture_output=True, text=True); P(r.returncode == 2 and not (W / "x1").exists(), "源文件不存在 → 退出 2 且不建目录", (r.returncode, r.stderr[:100]))
r, o = cc("write(1);"); r2 = subprocess.run([PY, "-m", "minic", str(o.parent / "p.mc"), "--frontend", str(W / "nofe"), "--out", str(W / "x2")], cwd=ROOT, capture_output=True, text=True); P(r2.returncode == 2 and "ccgen" in r2.stderr, "分析器目录不存在 → 退出 2 并提示运行 ccgen", r2.stderr[:100])
r, o = cc(b"int a = 1; // \xff\xfe", raw=True); P(r.returncode == 2, "非 UTF-8 源文件 → 退出 2", (r.returncode, r.stderr[:100]))
r, o = cc("﻿int a = 1; write(a);"); print("INFO 带 BOM 的源文件：退出码", r.returncode, "|", r.stderr.strip()[:90])
r = subprocess.run([PY, "-m", "minic"], cwd=ROOT, capture_output=True, text=True); P(r.returncode == 2, "缺少参数 → 退出 2")
for lvl in "13":
    ok, d = runs("int a = 6; write(a * 7);", "42\n") if False else (None, None)
    r, o = cc("int a = 6; write(a * 7);", f"-O{lvl}", "--run"); P(r.returncode == 0 and r.stdout == "42\n", f"-O{lvl} 可用")
# 旧产物清理：先成功编译，再放入语法错误的同名源文件，后阶段旧产物应消失
d = W / "stale"; d.mkdir(); s = d / "p.mc"; s.write_text("write(1);")
a = subprocess.run([PY, "-m", "minic", str(s), "--frontend", str(FE), "--out", str(d / "o")], cwd=ROOT, capture_output=True, text=True)
before = sorted(p.name for p in (d / "o").iterdir()); s.write_text("write(1;")
b = subprocess.run([PY, "-m", "minic", str(s), "--frontend", str(FE), "--out", str(d / "o")], cwd=ROOT, capture_output=True, text=True)
after = sorted(p.name for p in (d / "o").iterdir())
P(a.returncode == 0 and len(before) == 10 and b.returncode == 1 and after == ["tokens.json", "tokens.txt"], "出错后旧的 AST/IR/可执行文件被清除", (before, after))

# ---------- 随机程序差分 ----------
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 2026)
def wrap(v): return (v + 2**31) % 2**32 - 2**31
PREC = {"<": 0, ">": 0, "==": 0, "!=": 0, "<=": 0, ">=": 0, "+": 1, "-": 1, "*": 2, "/": 2}
def gen_expr(vars_, depth):
    if depth == 0 or rng.random() < 0.3:
        return ("var", rng.choice(vars_)) if vars_ and rng.random() < 0.6 else ("num", rng.choice([0, 1, 2, 3, 7, 10, 100, 65535, 2147483647, rng.randrange(0, 1000)]))
    op = rng.choice(list(PREC))
    if op == "/": return ("bin", op, gen_expr(vars_, depth - 1), ("num", rng.randrange(1, 12)))
    return ("bin", op, gen_expr(vars_, depth - 1), gen_expr(vars_, depth - 1))
def show(e, parent=-1, right=False):
    if e[0] == "var": return e[1]
    if e[0] == "num": return str(e[1])
    _, op, l, r = e; p = PREC[op]
    s = f"{show(l, p, False)} {op} {show(r, p, True)}"
    need = p < parent or (p == parent and (right or p == 0))
    return f"({s})" if need or rng.random() < 0.1 else s
def ev(e, env):
    if e[0] == "var":
        for sc in reversed(env):
            if e[1] in sc: return sc[e[1]]
        raise KeyError(e[1])
    if e[0] == "num": return e[1]
    _, op, l, r = e; a, b = ev(l, env), ev(r, env)
    if op == "+": return wrap(a + b)
    if op == "-": return wrap(a - b)
    if op == "*": return wrap(a * b)
    if op == "/": q = abs(a) // abs(b); return wrap(q if (a < 0) == (b < 0) else -q)
    return int({"<": a < b, ">": a > b, "==": a == b, "!=": a != b, "<=": a <= b, ">=": a >= b}[op])
counter = [0]
def gen_stmt(scopes, depth, loop_depth):
    """返回 (源码, AST)。scopes 是可见变量名的列表栈；循环计数器以 k 开头且不被赋值。"""
    visible = [v for sc in scopes for v in sc]; assignable = [v for v in visible if not v.startswith("k")]
    k = rng.random()
    if k < 0.22 or not visible:
        name = rng.choice("abcdefg")
        if name in scopes[-1]: name = None
        if name:
            scopes[-1].append(name)
            if rng.random() < 0.25: return f"int {name};", ("decl", name, None)
            e = gen_expr(visible, 2); return f"int {name} = {show(e)};", ("decl", name, e)
    if k < 0.45 and assignable:
        v = rng.choice(assignable); e = gen_expr(visible, 3); return f"{v} = {show(e)};", ("assign", v, e)
    if k < 0.65:
        e = gen_expr(visible, 3); return f"write({show(e)});", ("write", e)
    if k < 0.72 and assignable:
        v = rng.choice(assignable); return f"read({v});", ("read", v)
    if depth > 0 and k < 0.86:
        c = gen_expr(visible, 2)
        def body():
            if rng.random() < 0.5: return gen_block(scopes, depth - 1, loop_depth)
            scopes.append([]); s = gen_stmt(scopes, depth - 1, loop_depth); scopes.pop(); return s
        ts, ta = body()
        if rng.random() < 0.5: return f"if ({show(c)}) {ts}", ("if", c, ta, None)
        es, ea = body(); return f"if ({show(c)}) {ts} else {es}", ("if", c, ta, ea)
    if depth > 0 and loop_depth < 2 and k < 0.95:
        counter[0] += 1; kv = f"k{counter[0]}"; bound = rng.randrange(0, 5)
        scopes.append([kv]); inner_s, inner_a = [], []
        for _ in range(rng.randrange(1, 4)):
            s, a = gen_stmt(scopes, depth - 1, loop_depth + 1); inner_s.append(s); inner_a.append(a)
        scopes.pop()
        src = f"{{ int {kv} = 0; while ({kv} < {bound}) {{ {' '.join(inner_s)} {kv} = {kv} + 1; }} }}"
        return src, ("block", [("decl", kv, ("num", 0)), ("while", ("bin", "<", ("var", kv), ("num", bound)), ("block", inner_a + [("assign", kv, ("bin", "+", ("var", kv), ("num", 1)))]))])
    return gen_block(scopes, depth - 1, loop_depth) if depth > 0 else ("write(0);", ("write", ("num", 0)))
def gen_block(scopes, depth, loop_depth):
    scopes.append([]); ss, aa = [], []
    for _ in range(rng.randrange(0, 4)):
        s, a = gen_stmt(scopes, depth, loop_depth); ss.append(s); aa.append(a)
    scopes.pop(); return "{ " + " ".join(ss) + " }", ("block", aa)
def interp(stmts, inputs):
    out, env, it = [], [{}], iter(inputs)
    def setv(name, v):
        for sc in reversed(env):
            if name in sc: sc[name] = v; return
        raise KeyError(name)
    def ex(a):
        t = a[0]
        if t == "decl": v = ev(a[2], env) if a[2] else 0; env[-1][a[1]] = v
        elif t == "assign": setv(a[1], ev(a[2], env))
        elif t == "write": out.append(str(ev(a[1], env)))
        elif t == "read": setv(a[1], next(it))
        elif t == "block":
            env.append({}); [ex(x) for x in a[1]]; env.pop()
        elif t == "if":
            branch = a[2] if ev(a[1], env) != 0 else a[3]
            if branch: env.append({}); ex(branch); env.pop()
        elif t == "while":
            while ev(a[1], env) != 0: env.append({}); ex(a[2]); env.pop()
    for a in stmts: ex(a)
    return "".join(x + "\n" for x in out)
N = int(sys.argv[3]) if len(sys.argv) > 3 else 60
fails = 0; total_out = 0
for i in range(N):
    counter[0] = 0; scopes = [[]]; ss, aa = [], []
    for _ in range(rng.randrange(4, 14)):
        s, a = gen_stmt(scopes, 3, 0); ss.append(s); aa.append(a)
    src = "\n".join(ss) + "\n"; inputs = [rng.choice([0, 1, -1, 5, -17, 2147483647, -2147483648, rng.randrange(-999, 999)]) for _ in range(200)]
    want = interp(aa, inputs); total_out += want.count("\n"); stdin = "\n".join(map(str, inputs)) + "\n"
    for lvl in ("-O0", "-O2"):
        r, o = cc(src, lvl, "--run", stdin=stdin)
        if r.returncode != 0 or r.stdout != want:
            fails += 1; print("FAIL 差分", i, lvl, "rc", r.returncode, "\n--- src\n" + src[:1500], "\n--- want", want[:200], "\n--- got", r.stdout[:200], r.stderr[-300:]); break
P(fails == 0, f"{N} 个随机程序（-O0 与 -O2）与参考解释器输出一致，共比对 {total_out} 行输出")
