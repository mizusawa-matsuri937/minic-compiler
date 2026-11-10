# mini-C 编译器生成器与编译器成品 AC 完成情况

状态（2026-11-10）：AC00、AC01–AC17、AC19–AC22 已通过；AC18 自动化通过、人工目视未执行，未勾选。全部测试 41 个通过，无失败、错误或跳过。

所有命令块的工作目录是 `/Users/aqua_night/codex_project/编译原理/minic-compiler`，shell 为 zsh，每个块可以单独复制执行。已验证的单项命令显式选择 Python 3.11.15；标“计划，未执行”的手工复核命令未运行，不作为已完成证据。测试方法名含 AC 编号，所以 `-k acNN` 只运行该 AC 的用例；测试自己在临时目录中生成分析器，不依赖 `build/`。

## AC00 计划文件规范

- [x] 已验证（2026-11-10，AI 检查）。方法：用 `scripts/check_plan.py` 核对 spec 标题顺序、规则依据、R 与 AC 与任务的相互引用、checklist 同编号、勾选状态和残留占位符；再由 Claude 通读四文件，核对范围、关键未决项和实施授权的表述。

```bash
# 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 scripts/check_plan.py doc/task1; echo "退出码 $?"
```

复核观测：输出列出五个规定标题、29 条规则、23 项 AC、23 个 checklist 小节、7 个任务阶段，末行为“结构检查通过”，退出码 0。实际结果/日期/证据：2026-11-10 实测与上述一致，已勾选项只有 AC00。脚本只核对结构；内容层面，当时范围为仅规划（见 [项目配置](../project-config.md)），语言与 IR 路线已由用户确认，待验证项为 spec 的 H10、H11，均不阻塞实施。人工审阅：未记录，用户尚未审阅本计划。

本轮实施复核（2026-11-10）：重新运行结构检查，29 条规则、23 项 AC、7 个阶段对应完整，退出码 0；当前只保留 AC18 未勾选。证据：[AC00.log](evidence/AC00.log)。当前实施授权来自用户本轮指令，旧“仅规划”记录是历史快照。

## AC01 生成分析器且结果确定

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：自动化测试在两个临时目录各生成一次并逐字节比较；也可用下面第二条命令手工复核。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac01 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic 和 build/minic2
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic2 && diff -r build/minic build/minic2 && echo "两次生成一致" ; grep -nE "^(import|from) (ccgen|minic)" build/minic/lexer.py build/minic/parser.py ; ls build/minic
```

复核观测：测试全部 `ok`；手工命令打印“两次生成一致”，`grep` 没有输出，`ls` 列出五个文件。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.137s），退出码 0，无失败、错误或跳过；[AC01 完整日志](evidence/AC01.log)。
## AC02 生成器与语言无关

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：用四则运算规则生成分析器并分析 `1+2*3`，断言语法树形状。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac02 -v
```

复核观测：用例 `ok`，退出码 0。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.099s），退出码 0，无失败、错误或跳过；[AC02 完整日志](evidence/AC02.log)。
## AC03 正规式语法

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：对 spec 列出的六个正规式逐一断言接受与拒绝的串。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac03 -v
```

复核观测：用例 `ok`，退出码 0。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.003s），退出码 0，无失败、错误或跳过；[AC03 完整日志](evidence/AC03.log)。
## AC04 Thompson、子集法、等价状态法

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：对 `(a|b)*abb` 断言最小 DFA 为 4 个状态，并穷举长度不超过 8 的串比较三种自动机；对 mini-C 规则检查三个状态数。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac04 -v
```

复核观测：用例 `ok`，退出码 0。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.012s），退出码 0，无失败、错误或跳过；[AC04 完整日志](evidence/AC04.log)。
## AC05 mini-C 记号序列

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：扫描 `tests/fixtures/lex_ok.mc`，断言记号种别序列、种别码、属性值和位置。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac05 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 build/minic/lexer.py tests/fixtures/lex_ok.mc --text
```

复核观测：测试 `ok`；手工命令输出 16 行记号，第 2 行为 `(7, integer)`、`IDENT`、`1:5`。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.030s），退出码 0，无失败、错误或跳过；[AC05 完整日志](evidence/AC05.log)。
## AC06 词法错误

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：编译 `tests/fixtures/lex_error.mc`，断言退出码、两条诊断和产物文件。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac06 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic；被编译程序有错，预期退出码为 1
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic tests/fixtures/lex_error.mc --frontend build/minic --out out/lex_error ; echo "退出码 $?" ; ls out/lex_error
```

复核观测：测试 `ok`；手工命令在标准错误打印 1:11 和 2:7 两条 `词法错误[L001]`，退出码 1，目录中只有 `tokens.txt`、`tokens.json`。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.081s），退出码 0，无失败、错误或跳过；[AC06 完整日志](evidence/AC06.log)。
## AC07 LR(1) 分析表与产生式编号

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：读取生成的 `parser_tables.json`，断言产生式、FIRST 集和冲突列表。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac07 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -c "import json; t=json.load(open('build/minic/parser_tables.json', encoding='utf-8')); print(len(t['productions']), t['states'], t['first']['Expr'], t['conflicts'])"
```

复核观测：测试 `ok`；手工命令先打印 38，再打印状态数，FIRST(Expr) 含 `IDENT`、`NUMBER`、`(` 三项，冲突各项的 `lookahead` 都是 `else`、`resolution` 都是 `shift`。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.086s），退出码 0，无失败、错误或跳过；[AC07 完整日志](evidence/AC07.log)。
## AC08 未声明的冲突

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：用二义文法和去掉 `%prefer` 声明的 mini-C 文法分别生成，断言失败、错误信息和无输出文件。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac08 -v
```

```bash
# 计划，未执行；手工复核情形 (a)。预期生成失败，退出码为 2
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex tests/fixtures/calc.lex --grammar tests/fixtures/ambiguous.grammar --out out/ambiguous ; echo "退出码 $?" ; ls out/ambiguous 2>/dev/null
```

复核观测：测试 `ok`；手工命令在标准错误列出 `+` 上的移进-归约冲突和相关项目，退出码 2，`ls` 没有输出。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.081s），退出码 0，无失败、错误或跳过；[AC08 完整日志](evidence/AC08.log)。
## AC09 规则文件错误

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：对四份有错的规则分别生成，断言退出码、文件名与行号、输出目录为空。有错规则由测试在临时目录中写出。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac09 -v
```

复核观测：四种情形的用例都 `ok`，退出码 0。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.262s），退出码 0，无失败、错误或跳过；[AC09 完整日志](evidence/AC09.log)。
## AC10 表达式的 AST 结构

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：编译 `tests/fixtures/expr.mc`，断言 `ast.json` 的嵌套结构。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac10 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic tests/fixtures/expr.mc --frontend build/minic --out out/expr --stop-after ast && cat out/expr/ast.json
```

复核观测：测试 `ok`；`ast.json` 中第一条语句的 `init` 是 `op` 为 `-` 的 `BinaryOp`，它的 `left` 的 `op` 为 `+`，再下一层 `right` 的 `op` 为 `*`。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.083s），退出码 0，无失败、错误或跳过；[AC10 完整日志](evidence/AC10.log)。
## AC11 else 的最近配对

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：编译 `tests/fixtures/dangling_else.mc`，断言外层 `If` 无 `else`、内层 `If` 有 `else`。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac11 -v
```

复核观测：用例 `ok`，退出码 0。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.085s），退出码 0，无失败、错误或跳过；[AC11 完整日志](evidence/AC11.log)。
## AC12 语法错误

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：编译两个语法错误样例，断言退出码、诊断位置、实际记号、期望集合和产物文件。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac12 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic；被编译程序有错，预期退出码为 1
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic tests/fixtures/syntax_chain.mc --frontend build/minic --out out/syntax_chain ; echo "退出码 $?" ; ls out/syntax_chain
```

复核观测：测试 `ok`；手工命令打印一条位于 1:15 的 `语法错误[P001]`，期望集合为 `+ - * / ;`，退出码 1，目录中只有 `tokens.txt`、`tokens.json`。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.138s），退出码 0，无失败、错误或跳过；[AC12 完整日志](evidence/AC12.log)。
## AC13 语义错误

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：编译 `tests/fixtures/semantic_error.mc`，断言四条诊断的代码、位置和顺序，以及产物文件。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac13 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic；被编译程序有错，预期退出码为 1
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic tests/fixtures/semantic_error.mc --frontend build/minic --out out/semantic_error ; echo "退出码 $?" ; ls out/semantic_error
```

复核观测：测试 `ok`；手工命令依次打印 2:1 `S002`、3:1 `S001`、4:9 `S003`、6:1 `S001` 四条诊断，退出码 1，目录中有 `tokens.*` 和 `ast.*`，没有 `.ll`。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.087s），退出码 0，无失败、错误或跳过；[AC13 完整日志](evidence/AC13.log)。
## AC14 LLVM IR 的生成

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：以 `--stop-after ir` 编译演示程序两次，断言 IR 的结构特征和两次产物一致。此项不需要 clang。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac14 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic examples/demo.mc --frontend build/minic --out out/demo_ir --stop-after ir && cat out/demo_ir/demo.ll && grep -c "alloca i32" out/demo_ir/demo.ll
```

复核观测：测试 `ok`；手工命令打印完整 IR，末行计数为 4。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.102s），退出码 0，无失败、错误或跳过；[AC14 完整日志](evidence/AC14.log)。
## AC15 优化、机器码与运行结果

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：完整编译演示程序（`-O0` 与 `-O2`），运行可执行文件并比较输出。需要 clang；测试被跳过时此项不能勾选。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac15 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic examples/demo.mc --frontend build/minic --out out/demo && ls out/demo && echo 5 | out/demo/demo && echo 10 | out/demo/demo
```

复核观测：测试 `ok` 且没有跳过；手工命令列出包括 `demo.opt.ll`、`demo.s`、`demo` 在内的全部产物，随后输出 `15`、`120`、`1`、`55`、`3628800`、`0` 六行。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（3.390s），退出码 0，无失败、错误或跳过；[AC15 完整日志](evidence/AC15.log)。
## AC16 运行语义

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：编译并运行 7 个运行样例，逐个比较标准输出。需要 clang；测试被跳过时此项不能勾选。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac16 -v
```

复核观测：7 个样例各自对应的用例都 `ok`，没有跳过，退出码 0。实际结果/日期/证据：2026-11-10，单项 7 个测试 OK（17.415s），退出码 0，无失败、错误或跳过；[AC16 完整日志](evidence/AC16.log)。
## AC17 clang 不可用

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：以 `--clang /nonexistent/clang` 编译演示程序，断言退出码 3 和保留的产物。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac17 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic；预期退出码为 3
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic examples/demo.mc --frontend build/minic --out out/demo_noclang --clang /nonexistent/clang ; echo "退出码 $?" ; ls out/demo_noclang
```

复核观测：测试 `ok`；手工命令说明无法运行 clang，退出码 3，目录中有 `tokens.*`、`ast.*`、`demo.ll`，没有 `demo.opt.ll`、`demo.s`、`demo`。实际结果/日期/证据：2026-11-10，单项 3 个测试 OK（0.439s），退出码 0，无失败、错误或跳过；[AC17 完整日志](evidence/AC17.log)。
## AC18 AST 可视化

- [ ] 部分通过（2026-11-10）：阶段自动检查通过，退出码 0。人工目视检查留给用户，未代勾。方法：自动化测试核对四个 AST 文件存在，`ast.html` 自包含、含 SVG、结点数与 `ast.json` 一致；另需人工在浏览器中离线打开目视检查。两部分都完成才能勾选。此项不需要 clang。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac18 -v
```

```bash
# 计划，未执行；人工检查。会写入 build/minic 和 out/demo_ast，并用 macOS 默认浏览器打开
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic examples/demo.mc --frontend build/minic --out out/demo_ast --stop-after ast && ls out/demo_ast && open out/demo_ast/ast.html
```

复核观测：测试 `ok`；`ls` 列出 `ast.json`、`ast.txt`、`ast.html`、`ast.dot` 和两个记号文件；浏览器断网时仍能显示以 `Program` 为根的树，结点不重叠，连线旁有字段名。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.087s），退出码 0，无失败、错误或跳过；[AC18 完整日志](evidence/AC18.log)。人工检查：未执行，留给用户，不能勾选。布局坐标无重叠的机器断言不替代目视验收。

## AC19 生成器构造报告

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：自动化测试核对 `report.html` 的九节内容、与表文件一致的数字和自包含；建议人工打开浏览一遍。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac19 -v
```

```bash
# 计划，未执行；人工浏览。会写入 build/minic，并用 macOS 默认浏览器打开
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && open build/minic/report.html
```

复核观测：测试 `ok`；页面依次有正规式、三个状态数、最小 DFA 转换表、产生式、FIRST 集、项目集数量、ACTION/GOTO 表、冲突与消解。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.103s），退出码 0，无失败、错误或跳过；[AC19 完整日志](evidence/AC19.log)。
## AC20 生成的分析器独立运行

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：在仓库外的临时目录用 `python3 -I` 依次运行 `lexer.py`、`parser.py`，把结果与 `minic` 的产物逐字节比较。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac20 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic、out/demo_ast 和仓库外的 /tmp/minic-ac20
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m minic examples/demo.mc --frontend build/minic --out out/demo_ast --stop-after ast && mkdir -p /tmp/minic-ac20 && cd /tmp/minic-ac20 && python3 -I "/Users/aqua_night/codex_project/编译原理/minic-compiler/build/minic/lexer.py" "/Users/aqua_night/codex_project/编译原理/minic-compiler/examples/demo.mc" -o tokens.json && python3 -I "/Users/aqua_night/codex_project/编译原理/minic-compiler/build/minic/parser.py" tokens.json -o ast.json && cmp tokens.json "/Users/aqua_night/codex_project/编译原理/minic-compiler/out/demo_ast/tokens.json" && cmp ast.json "/Users/aqua_night/codex_project/编译原理/minic-compiler/out/demo_ast/ast.json" && echo "独立运行结果一致"
```

复核观测：测试 `ok`；手工命令打印“独立运行结果一致”。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.179s），退出码 0，无失败、错误或跳过；[AC20 完整日志](evidence/AC20.log)。
## AC21 全量测试与标准库依赖

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：运行全部测试；其中 `ac21` 用例扫描所有 `.py` 文件的 import，并确认没有依赖清单文件。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac21 -v
```

复核观测：末尾为 `OK`，没有 `FAILED`、`errors`，也没有 `skipped`；退出码 0。若有跳过，逐条写明原因且本项不勾选。实际结果/日期/证据：2026-11-10，单项 2 个测试 OK（0.024s），退出码 0，无失败、错误或跳过；[AC21 完整日志](evidence/AC21.log)。
全量验证：[Python 3.11.15 与最终演示](evidence/T1-06.log) 41 tests / 24.045s；[默认 Python 3.14.6](evidence/python314-full.log) 41 tests / 24.529s；均 OK，无跳过，退出码 0。

## AC22 答辩演示

- [x] 已验证（2026-11-10）：阶段自动检查通过，退出码 0。方法：自动化测试核对演示程序的 AST 含六种语句结点，并运行演示脚本比较输出。需要 clang。

```bash
# 已验证 2026-11-10；shell zsh；Python 3.11.15
export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac22 -v
```

```bash
# 计划，未执行；手工复核。会写入 build/minic 和 out/demo
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && echo 5 | bash scripts/demo.sh ; echo "退出码 $?"
```

复核观测：测试 `ok` 且没有跳过；手工命令先列出各产物路径，最后三行为 `15`、`120`、`1`，退出码 0。实际结果/日期/证据：2026-11-10，单项 1 个测试 OK（0.811s），退出码 0，无失败、错误或跳过；[AC22 完整日志](evidence/AC22.log)。
实际最终演示：T1-06 中 `echo 5 | bash scripts/demo.sh` 已执行，退出码 0，标准输出先列产物路径、最后三行 `15`、`120`、`1`；见 [T1-06 日志](evidence/T1-06.log)。

## 当前汇总

计划 AC：1/1（AC00）；实施 AC：21/22。AC18 人工检查未执行；只勾选实际通过的自动化 AC，clang 用例跳过不算通过。

2026-11-11 修复轮补充实测（保留上文 2026-11-10 历史结果及全部复选状态）：RV01～RV11 的修前失败与修后通过见 [修复汇总](../review/fix-summary.md)。D 逐项运行 AC02、AC05、AC06、AC10、AC13～AC22 的 14 组筛选及全部新增回归（26 tests），均退出 0、无失败/错误/跳过；随后 Python 3.11.15 全量 **67 tests / 21.386s，0 失败、0 错误、0 跳过，退出 0**，见 [full-regression.json](../review/fixes/evidence/D/full-regression.json)。源码在定向和全量验证前后摘要一致；真实 Apple clang 21.0.0 后端实际执行。

```bash
# 已验证 2026-11-11；shell zsh；Python 3.11.15；所有测试产物在临时目录
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -v
```

演示实测设置 `MINIC_PYTHON=/Users/aqua_night/.local/bin/python3.11`、`MINIC_BUILD_DIR` 和 `MINIC_OUT_DIR` 指向带空格临时目录，然后执行 `echo 5 | bash scripts/demo.sh`，退出 0，最后三行 `15`、`120`、`1`；五个生成器文件与十个编译产物齐全非空。实际路径、环境、完整 stdout/stderr 及退出码见 [demo.json](../review/fixes/evidence/D/demo.json)，可复制复核入口见 [D 报告](../review/fixes/agent-D.md)。

AC18 技术补充：D 在 Safari 26.5 以本地文件打开长标识符与 demo 图，实际文字越框、节点文字/字段标签重叠、文字超出 SVG 均为 0；[浏览器记录](../review/fixes/evidence/D/browser-observations.txt) 含修前/修后真实测量及目视观察。这不等于用户亲自离线目视，AC18 保持未勾选。Python 3.14、其他系统/浏览器、clang 15 最低版本与答辩机器未在本轮验证。
