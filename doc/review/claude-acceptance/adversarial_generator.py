"""对抗性验证 1：确定性、正规式差分、最小化独立核对、文法通用性。"""
import itertools, json, os, random, re, shutil, subprocess, sys
from pathlib import Path
ROOT = Path("/Users/aqua_night/codex_project/编译原理/minic-compiler")
W = Path(sys.argv[1]); shutil.rmtree(W, ignore_errors=True); W.mkdir(parents=True)
sys.path.insert(0, str(ROOT))
from ccgen import regex as rx, nfa as nf, dfa as df
def P(ok, name, detail=""):
    print("PASS" if ok else "FAIL", name, "" if ok else f"  <<< {str(detail)[:500]}")

# 1. 确定性：不同哈希种子、不同解释器
ref = None; same = True
for py, seed in [("python3", "0"), ("python3", "1"), ("python3", "12345"), ("/Users/aqua_night/.local/bin/python3.14", "7")]:
    out = W / f"gen_{Path(py).name}_{seed}"
    r = subprocess.run([py, "-m", "ccgen", "--lex", "rules/minic.lex", "--grammar", "rules/minic.grammar", "--out", str(out)],
                       cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=seed))
    if r.returncode: same = False; print("   gen fail", py, seed, r.stderr[:200]); continue
    data = {f.name: f.read_bytes() for f in sorted(out.iterdir())}
    if ref is None: ref = data
    elif data != ref:
        same = False; print("   differs:", py, seed, [k for k in data if data[k] != ref.get(k)])
P(same, "R29 生成结果在哈希种子 0/1/12345 与 Python 3.14 下逐字节相同")

# 2. 正规式引擎与 Python re 差分 + 最小化独立核对
def automata(pattern):
    n = nf.NFA(); n.add(rx.parse(pattern), 0); n.canonicalize(); d = df.determinize(n); return n, d, df.minimize(d)
def classes(d):
    """独立的填表法：统计 DFA 的不可区分等价类数（缺失转换视为死状态）。"""
    n = len(d.trans); DEAD = n
    t = lambda s, c: DEAD if s == DEAD else d.trans[s].get(c, DEAD)
    acc = lambda s: d.accept.get(s) if s != DEAD else None
    syms = sorted({c for row in d.trans for c in row})
    dist = {(a, b) for a in range(n + 1) for b in range(a) if acc(a) != acc(b)}
    changed = True
    while changed:
        changed = False
        for a in range(n + 1):
            for b in range(a):
                if (a, b) in dist: continue
                for c in syms:
                    x, y = t(a, c), t(b, c)
                    if x != y and (max(x, y), min(x, y)) in dist:
                        dist.add((a, b)); changed = True; break
    rep = []
    for s in range(n):  # 活状态的等价类数（Thompson DFA 无死状态；与 DEAD 等价的不计）
        if (DEAD, s) not in dist: continue
        if not any((max(s, r), min(s, r)) not in dist for r in rep): rep.append(s)
    return len(rep)
rng = random.Random(20261111)
def rand_re(depth):
    if depth == 0 or rng.random() < 0.25:
        return rng.choice(["a", "b", "c", "[ab]", "[^a]", "[a-c]"])
    k = rng.random()
    if k < 0.35: return rand_re(depth - 1) + rand_re(depth - 1)
    if k < 0.6: return "(" + rand_re(depth - 1) + "|" + rand_re(depth - 1) + ")"
    return "(" + rand_re(depth - 1) + ")" + rng.choice("*+?")
strings = ["".join(p) for L in range(6) for p in itertools.product("abc", repeat=L)] + ["d", "ad", "中", "a中b", "\n"]
bad = []; nonmin = []; total = 0
for _ in range(400):
    pat = rand_re(4); total += 1
    try: n, d, m = automata(pat)
    except Exception as e: bad.append((pat, "异常", repr(e))); continue
    py = re.compile(pat.replace("[^a]", "[^a]"), re.S)
    for s in strings:
        want = py.fullmatch(s) is not None
        if not (n.accepts(s) == d.accepts(s) == m.accepts(s) == want):
            bad.append((pat, s, want, n.accepts(s), d.accepts(s), m.accepts(s))); break
    if len(m.trans) != classes(d): nonmin.append((pat, len(d.trans), len(m.trans), classes(d)))
P(not bad, f"{total} 个随机正规式 × {len(strings)} 个串：NFA/DFA/最小DFA 与 Python re 一致", bad[:3])
P(not nonmin, "最小 DFA 状态数等于独立填表法求得的等价类数（即确实最小）", nonmin[:3])

# 3. 正规式语法边界
def rex(p):
    try: automata(p); return "ok"
    except Exception as e: return type(e).__name__
edge = {"(": "RuleError", "a)": "RuleError", "[]": "RuleError", "[z-a]": "RuleError", "*a": "RuleError", "a\\": "RuleError", "[abc": "RuleError",
        "a**": "ok", "(a|)": "ok", r"[\]a]": "ok", r"[a\-z]": "ok", "[-a]": "ok", "[a-]": "ok", r"\\": "ok", "a|b|c": "ok", "((a))": "ok", "中": "RuleError"}
got = {p: rex(p) for p in edge}
P(got == edge, "正规式语法边界（非法式报 RuleError，合法式可构造）", {p: (got[p], edge[p]) for p in edge if got[p] != edge[p]})
n, d, m = automata(r"[a\-z]+"); P(m.accepts("a-z") and not m.accepts("b"), r"[a\-z] 中转义的 - 是字面字符")
n, d, m = automata(r"[a-]+"); P(m.accepts("a-") and not m.accepts("b"), "[a-] 末尾的 - 是字面字符")

# 4. 文法通用性：LR(1) 但非 LALR(1)；ε 产生式；归约-归约冲突
def gen(tag, lex, gram):
    (W/f"{tag}.lex").write_text(lex); (W/f"{tag}.grammar").write_text(gram)
    return subprocess.run([sys.executable, "-m", "ccgen", "--lex", str(W/f"{tag}.lex"), "--grammar", str(W/f"{tag}.grammar"), "--out", str(W/tag)], cwd=ROOT, capture_output=True, text=True)
def parse(tag, text):
    (W/f"{tag}.in").write_text(text)
    t = subprocess.run([sys.executable, "-I", str(W/tag/"lexer.py"), str(W/f"{tag}.in"), "-o", str(W/f"{tag}.tok")], capture_output=True, text=True)
    p = subprocess.run([sys.executable, "-I", str(W/tag/"parser.py"), str(W/f"{tag}.tok")], capture_output=True, text=True)
    return t.returncode, p.returncode, p.stdout, p.stderr
lex = "a a\nb b\ne e\n"
r = gen("nonlalr", lex, "S -> a E a\nS -> b E b\nS -> a F b\nS -> b F a\nE -> e\nF -> e\n")
P(r.returncode == 0, "LR(1) 但非 LALR(1) 的文法生成成功（证明是规范 LR(1) 而非 LALR/SLR）", r.stderr[:300])
ok = all(parse("nonlalr", s)[1] == 0 for s in ["aea", "beb", "aeb", "bea"]) and all(parse("nonlalr", s)[1] == 1 for s in ["aee", "ae", "eea", ""])
P(ok, "该文法接受 aea/beb/aeb/bea，拒绝 aee/ae/eea/空")
r = gen("rr", lex, "S -> E\nS -> F\nE -> e\nF -> e\n")
P(r.returncode == 2 and "归约-归约" in r.stderr and not (W/"rr").exists(), "归约-归约冲突被拒绝并说明类型", r.stderr[:200])
r = gen("rrprefer", lex, "%prefer shift e\nS -> E\nS -> F\nE -> e\nF -> e\n")
P(r.returncode == 2, "%prefer shift 不能消解归约-归约冲突", r.stderr[:200])
r = gen("eps", "a a\nb b\n", "S -> A B\nA -> ε\nA -> a A\nB -> %empty\nB -> b B\n")
ok = r.returncode == 0 and all(parse("eps", s)[1] == 0 for s in ["", "a", "b", "aabbb"]) and parse("eps", "ba")[1] == 1
P(ok, "含 ε 产生式与可空链的文法：接受 空/a/b/aabbb，拒绝 ba", r.stderr[:200])
pt = json.loads((W/"eps"/"parser_tables.json").read_text())
P(pt["first"]["S"] == ["a", "b", "ε"] and pt["first"]["A"] == ["a", "ε"], "FIRST(S)={a,b,ε}, FIRST(A)={a,ε}", pt["first"])
# 动作语言：列表展开、嵌套结点、缺省动作混用
r = gen("act", "%skip W\nW [ ]+\nn [0-9]+\n, ,\n", "L -> n , L => [$1, *$3]\nL -> n => [$1]\n")
rc = parse("act", "1, 2, 3")
P(r.returncode == 0 and json.loads(rc[2]) == ["1", "2", "3"], "列表动作 [$1, *$3] 得到 ['1','2','3']", rc)
for tag, g, needle in [("e1", "S -> a => Node(x=$1, x=$1)\n", "重复"), ("e2", "S -> a => Node(type=$1)\n", "保留"), ("e3", "S -> a => $0\n", "越界"), ("e4", "S -> a => [$1\n", ""), ("e5", "S -> a b\n", "b"), ("e6", "S -> a => \n", ""), ("e7", "S a\n", "->"), ("e8", "%start X\nS -> a\n", "X"), ("e9", "S -> a\na -> a\n", "重名")]:
    r = gen(tag, "a a\n", g)
    P(r.returncode == 2 and f"{tag}.grammar:" in r.stderr and not (W/tag).exists(), f"语法规则错误 {tag}: {g.strip()!r} 被拒绝", (r.returncode, r.stderr[:150]))
for tag, l in [("l1", "a a\na b\n"), ("l2", "%skip Z\na a\n"), ("l3", "$ a\n"), ("l4", "a\n"), ("l5", "")]:
    r = gen(tag, l, "S -> a\n")
    P(r.returncode == 2 and not (W/tag).exists(), f"词法规则错误 {tag}: {l.strip()!r} 被拒绝", (r.returncode, r.stderr[:150]))
