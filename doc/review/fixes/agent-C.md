# 修复 C：深 AST、实际字形布局与 DFA 空格表头

日期：2026-11-11（客户端 Asia/Taipei；原始环境探针为 2026-11-10 UTC）。基线 `main / 2fa29b29440069881b91735e13c9a870450ef918`。实际解释器 Python 3.11.15，Apple clang 21.0.0，macOS arm64。仅修改指定文件，未执行 Git 写操作；原审查证据保留。本次按主对话先写入 design §14 的方案实施。

## 结果与修改范围

| 问题 | 根因与修改 | 证据/状态 |
|---|---|---|
| RV07 | JSON 之后的 semantic.visit/scoped、IR expression/statement、AST text/measure/position 都把 AST 深度映射为 Python 调用深度。`minic/semantic.py` 使用进入/退出作用域、初始化后声明的事件栈；`minic/irgen.py` 使用后序表达式值栈、语句/分支续延事件栈；`minic/astviz.py` 使用预序收集、逆序求 span、显式定位与文本栈。保留左右顺序、声明初值引用外层、双层块/语句作用域及原控制流编号。 | 已修复并通过以下 7 项新回归；A 的驱动与 B 的 parser.json_text 接口共同完成 JSON 链。 |
| RV08 | 原 8px 字宽估算与浏览器 14px monospace 实际字形不一致。`minic/astviz.py` 保留保守静态 SVG 回退，内嵌无依赖原生 JS，用 SVG `getBBox()` 实测节点/字段文字宽高，重算子树区间、行高、矩形、文字、连线与 viewBox；字体 ready 后重新测量。完整标签保留，不引入外部字体、资源或自动化依赖。 | Python 回归只确认完整标签、自包含性与实际度量入口；它不冒充浏览器几何证明。真实浏览器修前/修后证据由 D 独立采集，见下文。 |
| RV10 | `repr(chr(32))[1:-1]` 返回裸空格，使 DFA 表头不可辨认。`ccgen/report.py` 只把显示值改为 `SPACE (U+0020)`。 | 新回归验证可见表头，并对 128 个字符、全部状态展开核对分组转换签名；转换数据/分组算法不变。 |

新增测试：`tests/test_review_ast.py`，9 个方法全部含 AC 编号；不改旧测试、规则、fixture 或原 AC。相关 AC：AC10、AC13、AC14、AC16、AC18、AC19、AC20。没有调高递归上限、吞 RecursionError、增加语言限制或新业务模块。

## 失败先行及同用例修后结果

工作目录均为 `/Users/aqua_night/codex_project/编译原理/minic-compiler`，shell zsh；分析器、源文件、编译产物均为临时目录，禁用源码字节码写入。

下面相同命令在业务修改前后实际运行：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_review_ast.py -v
```

- 修前：[before.log](evidence/C/before.log)，9 tests，5 failures、8 errors，退出 **1**。子测试单独计入失败/错误数，因此两者之和超过方法数；这是真实失败，不是“复现成功退出 0”。
- 修后：[after.log](evidence/C/after.log)，9 tests，0 failures/errors/skips，退出 **0**。初次修后记录也保留在 [after-initial.log](evidence/C/after-initial.log)。

各回归具体断言：

| 输入/入口 | 修前观察 | 修后观察 |
|---|---|---|
| 1000 项 `1` 相加，直接 semantic.check | RecursionError | 无语义错误，递归上限未改变 |
| 550 层 `if(1){…}`，内层 `int x=x+1`，外层 `x=7` | RecursionError | 初值读取 `x.addr`，内层绑定 `x.addr.1`，块退出后仍为 `x.addr` |
| 1000 项表达式直接生成 IR，避开语义入口 | RecursionError | 999 条 add，左结合从 `%t1` 到 `%t999`，printf 使用 `%t999` |
| 1050 层 if，内含 while/else，直接生成 IR | RecursionError | 控制标号与两条输出语句完整，while.cond.1051 / if.else.1050 存在 |
| 同一棵 1000 项表达式，分别调用 text/layout/HTML/DOT | 四个入口各 RecursionError | 2001 节点、2000 边；文本 2001 行；每种产物完整 |
| 同一长式真实驱动到 IR，再 `python -I -B parser.py tokens.json -o ast.json` | 驱动在 JSON 阶段 traceback，退出 1 | 驱动与独立 parser 均退出 0，AST JSON 逐字节一致，JSON/text/HTML/DOT/IR 均非空，无语义内部 `_slot` 落盘 |
| 真实 clang `-O0 --run` 执行长式与 550 层控制程序 | 两程序均在 JSON 阶段失败 | 长式 stdout 恰为 `1000\n`；深控制 stdout 恰为 `8\n7\n`；均退出 0 |
| 两处使用 200 字符标识符的 6 节点 HTML | 无实际字形度量入口；D 同时实测越框/重叠/裁切 | 标签全文与离线资源断言通过；实际几何以 D 的浏览器记录为准 |
| DFA character(32) 与生成表头 | 只有不可见空格，断言失败 | `SPACE (U+0020)` 可见，全部 ASCII 转换分组核对通过 |

## 既有行为验证

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -k ac13 -k ac14 -k ac18 -k ac19 -v
```

实际 **17 tests，0 failures/errors/skips，退出 0**，见 [targeted.log](evidence/C/targeted.log)。全量只由 D 统一执行，C 没有自行全量重跑。

另做只读基线对照，11 个现有合法语法样例的全部语义诊断、绑定槽、AST 文本与修前基线相同；其中 10 个无语义错误样例的 LLVM IR 逐字节相同。完整实际输出：[compatibility.log](evidence/C/compatibility.log)，退出 0。可直接复核的已执行命令如下（只读取指定 Git 对象，不做 Git 写操作）：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B - <<'PY'
import copy
import subprocess
import sys
import types
from pathlib import Path
sys.path.insert(0, 'tests')
from support import Frontend
from minic import semantic, irgen, astviz
baseline = {}
for name in ('semantic','irgen','astviz'):
    source = subprocess.run(['git','show',f'2fa29b29440069881b91735e13c9a870450ef918:minic/{name}.py'], check=True,capture_output=True,text=True).stdout
    module=types.ModuleType('baseline_'+name)
    exec(compile(source, 'baseline_'+name, 'exec'), module.__dict__)
    baseline[name]=module
front=Frontend()
counts={'valid_syntax':0,'valid_semantics':0}
for source in [Path('examples/demo.mc'), *sorted(Path('tests/fixtures').rglob('*.mc'))]:
    tokens, errors=front.lexer.tokenize(source.read_text())
    if errors: continue
    try: tree=front.parser.parse(tokens)
    except front.parser.ParseError: continue
    before=copy.deepcopy(tree)
    old_errors=baseline['semantic'].check(before)
    new_errors=semantic.check(tree)
    assert old_errors == new_errors, source
    assert tree == before, source
    assert baseline['astviz'].text_tree(tree)==astviz.text_tree(tree), source
    counts['valid_syntax']+=1
    if not new_errors:
        assert baseline['irgen'].generate(before, source.name)==irgen.generate(tree,source.name), source
        counts['valid_semantics']+=1
    print(source, 'semantic diagnostics/slots/text identical', 'IR identical' if not new_errors else '(semantic errors)')
front.cleanup()
print(counts)
PY
```

## 浏览器技术复核与剩余范围

D 已独立确认修前 Safari 26.5 的 200 字符标识符反例：node-1/4/5 文字越框，node-1/5 超出 SVG，node-4/5 文字重叠 42.46875px；原始图中 VarDecl 开头被裁切。修后原始文件交 D：`/tmp/minic-rv08-D-fixed/long_identifier/ast.html` 与 `/tmp/minic-rv08-D-fixed/demo/ast.html`。D 回传修后结果：Safari 26.5 / 14px monospace；长标识符图为 6 节点/5 边、viewBox 5470.125 × 396；demo 为 46 节点/45 边、viewBox 3321.34375 × 696。两图均为 `data-layout=measured`，文字越框、节点文字重叠、字段文字重叠、全部文字超 SVG 视口均为 0。长 Identifier 实测文字宽 1778.46875px、矩形宽 1802.46875px，左右各 12px 内边距，相邻文字间隔 48px。D 直接查看原始 HTML 确认 VarDecl 开头完整；demo 可见部分层级可辨。完整浏览器技术步骤见 [D/browser-observations.txt](evidence/D/browser-observations.txt)，探针为 [D/geometry.js](evidence/D/geometry.js)，原始文件摘要见 [browser-baseline-sha256.json](evidence/D/browser-baseline-sha256.json) 与 [browser-fixed-sha256.json](evidence/D/browser-fixed-sha256.json)。这些证据由 D 独立维护。

没有代勾用户 AC18。技术浏览器检查不等于用户亲自离线目视验收。未验证所有浏览器、答辩电脑、任意规模 AST；深缩进 JSON/文本与简单子树布局仍会产生较大文件/视图，这是完整数据表示的成本，不宣称无限规模保证。Graphviz 未安装，不声称实际 DOT 渲染已验。没有更改或决定 `INT_MIN / -1` 行为。
