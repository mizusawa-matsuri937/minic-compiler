# mini-C 编译器生成器与编译器成品 执行任务

状态：T1-00 至 T1-06 编码与阶段自动检查已完成（2026-11-10）；AC18 人工目视验收另计。T1-07 已完成（2026-11-11）：实现方完成实现和自动检查，评审者 Claude 补做 AC24 的浏览器实测后勾选。规则与验收见 [spec](spec.md)，实现方法见 [design](design.md)，逐项复核见 [checklist](checklist.md)。

所有命令的工作目录是 `/Users/aqua_night/codex_project/编译原理/minic-compiler`，shell 为 zsh，各阶段实测使用 Python 3.11.15（通过 PATH 选择）；默认 `python3` 3.14.6 另有完整回归日志。以下代码块可独立复核，显式设置当前机器已存在的 3.11 路径；原始执行环境也记录在日志中。各阶段按顺序进行，后一阶段依赖前一阶段的产物。

- [x] T1-00 完成四文件与计划检查。规则：全部；关联 AC00。
  - 文件：`doc/task1/` 四文件、`doc/project-config.md`、`README.md`、`.gitignore`。
  - 完成情况：已完成。目标、范围、29 条规则、AC00–AC22、设计、阶段和验收映射均已写出；阻碍实施的选择（语言、IR 路线）已由用户确认。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 scripts/check_plan.py doc/task1
  ```

  实际结果：见 [checklist](checklist.md) 的 AC00。

- [x] T1-01 实现词法分析器生成器。规则：R04–R08；关联 AC03、AC04、AC05。
  - 文件：`ccgen/errors.py`、`ccgen/regex.py`、`ccgen/nfa.py`、`ccgen/dfa.py`、`ccgen/lexspec.py`、`ccgen/codegen.py` 与 `ccgen/templates/lexer_template.py`（词法部分）、`rules/minic.lex`、`tests/test_regex.py`、`tests/test_lexgen.py`、`tests/test_lexer_minic.py`、`tests/fixtures/lex_ok.mc`。
  - 完成情况：编码与自动检查已完成。交付正规式解析、Thompson 算法、子集法、等价状态法，以及能独立运行的 `lexer.py`；此阶段用 Python 接口生成并调用词法分析器，并提供 `lexer_tables.json` 内容的构造函数。`python3 -m ccgen` 命令行入口和写盘在 T1-02 补齐。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac03 -k ac04 -k ac05 -v
  ```

  计划观测：名字含 `ac03`、`ac04`、`ac05` 的用例全部 `ok`，退出码 0；用例数量以实际为准。实际结果：2026-11-10：5 个测试全部 OK（0.044s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-01.log`。

- [x] T1-02 实现语法分析器生成器与生成命令。规则：R01–R03、R09–R11、R26、R29；关联 AC01、AC02、AC07、AC08、AC09。
  - 文件：`ccgen/grammar.py`、`ccgen/lr1.py`、`ccgen/codegen.py` 与 `ccgen/templates/parser_template.py`（语法部分）、`ccgen/__main__.py`、`rules/minic.grammar`、`tests/test_parsegen.py`、`tests/test_ccgen_cli.py`、`tests/fixtures/` 下的 `calc.lex`、`calc.grammar`、`ambiguous.grammar`。
  - 完成情况：编码与自动检查已完成。交付 FIRST 集、LR(1) 项目集规范族、分析表与冲突处理、构造动作、独立运行的 `parser.py`、两份表文件和 `python3 -m ccgen` 命令。`report.html` 此阶段可以只有标题和占位，内容在 T1-05 完成。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m unittest discover -s tests -k ac01 -k ac02 -k ac07 -k ac08 -k ac09 -v
  ```

  计划观测：生成命令退出码 0，并打印五个文件的路径和一行统计，其中 LR(1) 状态数预计为 264（估算，以实际为准）、已消解冲突数为 2；所列 AC 的用例全部 `ok`。实际结果：2026-11-10：7 个测试全部 OK（0.500s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-02.log`。

- [x] T1-03 实现编译器驱动的前端与诊断。规则：R12–R15、R21（记号文件与 `ast.json`）、R24、R25；关联 AC06、AC10、AC11、AC12、AC13、AC20。
  - 文件：`minic/__main__.py`、`minic/frontend.py`、`minic/diagnostics.py`、`minic/semantic.py`、`examples/demo.mc`、`tests/test_minic_frontend.py`、`tests/test_semantic.py`、`tests/test_standalone.py`、`tests/fixtures/` 下的 `lex_error.mc`、`expr.mc`、`dangling_else.mc`、`syntax_chain.mc`、`syntax_eof.mc`、`semantic_error.mc`。
  - 完成情况：编码与自动检查已完成。交付 `python3 -m minic` 命令的阶段 1 至 3 和 `--stop-after`：加载生成的分析器、写出 `tokens.*` 与 `ast.json`、统一诊断格式、退出码、语义检查；并验证 mini-C 的 AST 结构和分析器的独立运行。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac06 -k ac10 -k ac11 -k ac12 -k ac13 -k ac20 -v
  ```

  计划观测：所列 AC 的用例全部 `ok`，退出码 0。实际结果：2026-11-10：9 个测试全部 OK（0.419s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-03.log`。

- [x] T1-04 实现 LLVM IR 生成与 clang 后端。规则：R16–R20；关联 AC14、AC15、AC16、AC17。
  - 文件：`minic/irgen.py`、`minic/backend.py`、`minic/__main__.py`（阶段 4 至 6 与 `-O`、`--clang`、`--run`）、`tests/test_irgen.py`、`tests/test_backend.py`、`tests/fixtures/run/` 下 6 个运行样例。
  - 完成情况：编码与自动检查已完成。交付 IR 生成、三条 clang 命令的调用、可执行文件的运行，以及 clang 缺失时的降级行为。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh；需要 clang 在 PATH 中
  export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac14 -k ac15 -k ac16 -k ac17 -v
  ```

  计划观测：所列 AC 的用例全部 `ok`，没有被跳过的用例（本机有 clang）；退出码 0。实际结果：2026-11-10：13 个测试全部 OK（10.739s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-04.log`。

- [x] T1-05 实现 AST 可视化与生成器构造报告。规则：R21（`ast.txt`、`ast.html`、`ast.dot`）、R22、R23；关联 AC18、AC19。
  - 文件：`minic/astviz.py`、`ccgen/report.py`、`tests/test_astviz.py`、`tests/test_report.py`。
  - 完成情况：编码与自动检查已完成。交付三种 AST 展示文件和九节内容的 `report.html`；AC18 人工目视检查未执行，复选状态未勾选。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac18 -k ac19 -v
  ```

  计划观测：所列 AC 的用例全部 `ok`，退出码 0。另需人工按 checklist 中 AC18、AC19 的手工命令在浏览器中离线打开 `ast.html` 和 `report.html` 目视检查，结果记入 checklist 的 AC18。实际结果：2026-11-10：3 个测试全部 OK（0.207s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-05.log`。

- [x] T1-06 完成演示脚本、全量回归与交接。规则：R27、R28；关联 AC21、AC22，并核对 AC01–AC20 的证据仍然有效。
  - 文件：`scripts/demo.sh`、`tests/test_project.py`、`README.md`、`doc/task1/checklist.md`、`doc/handoffs/` 下新增的交接文件。
  - 完成情况：演示脚本、依赖检查、README 与交接完成；41 个测试在 Python 3.11.15、3.14.6 下均通过，无跳过。收尾按设计补齐 NFA 的 BFS 编号，并修正冲突声明的诊断行号；逐 AC 日志复核现有验收。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh；需要 clang 在 PATH 中
  export PATH="/Users/aqua_night/.local/share/uv/python/cpython-3.11-macos-aarch64-none/bin:$PATH"
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -v && echo 5 | bash scripts/demo.sh
  ```

  计划观测：全部测试 `OK`，没有失败、错误和跳过；演示脚本退出码 0，标准输出最后三行为 `15`、`120`、`1`。实际结果：2026-11-10：41 个测试全部 OK（24.045s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-06.log`（41 tests / 24.045s）；演示最后三行 `15`、`120`、`1`。默认 Python 回归为 41 tests / 24.529s，见 `evidence/python314-full.log`。三套检查并行运行，这些耗时不是单独性能基准。

- [x] T1-07 处理验收评审发现 CR01、CR02。规则：R30、R31；关联 AC23、AC24，并随全量回归重新确认 AC05、AC06、AC14、AC18、AC20。
  - 文件：`ccgen/templates/lexer_template.py`（命令行入口的读文件）、`minic/__main__.py`（读文件一处）、`minic/astviz.py`（页面模板与内嵌脚本）、`tests/test_review_cr.py`（新增）、`README.md`、`doc/task1/checklist.md`、`doc/handoffs/` 下新增的交接文件。
  - 完成情况：已实现两入口忽略开头 BOM，以及 AST 根结点定位和两种显示方式；新增 4 项自动测试通过，全量 71 项通过。AC24 离线打开页面被浏览器安全策略拒绝，实现方未能做几何实测，当时保持未勾选；规则文件、样例及已有测试未修改。评审补充（2026-11-11，Claude）：复跑两条命令均通过（4 个与 71 个测试，退出码 0），并在 Chromium 152 的 1280 像素宽视口中补做了 AC24 的三状态实测，全部达标，数值见 [checklist](checklist.md) 的 AC24；据此勾选本阶段。

  ```bash
  # 已验证 2026-11-11；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh；Python 3.11.15
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && /Users/aqua_night/.local/bin/python3.11 -m unittest discover -s tests -k ac23 -k ac24 -v
  ```

  ```bash
  # 已验证 2026-11-11；shell zsh；Python 3.11.15；Apple clang 21.0.0 在 PATH 中
  setopt PIPE_FAIL
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && /Users/aqua_night/.local/bin/python3.11 -m unittest discover -s tests 2>&1 | tail -4
  ```

  实际结果（2026-11-11）：第一条 4 tests / 0.355s，第二条 71 tests / 25.202s；两条均 `OK`、退出码 0，无失败、错误、跳过。证据：[定向日志](evidence/t107/targeted.log)、[全量输出和环境](evidence/t107/full-regression.json)、[浏览器尝试记录](evidence/t107/browser-attempt.md)；AC05、AC06、AC14、AC18 自动部分及 AC20 已随全量回归重新确认。

阶段本地提交：遵循 [项目配置](../project-config.md)，每个阶段检查通过后提交一次，提交说明以阶段编号开头（如 `T1-01 词法分析器生成器`）。

| 阶段 | 提交标识 |
|---|---|
| T1-00 | 见 `git log` 中说明以 `T1-00` 开头的提交（本文件随该提交入库，无法在自身中预填哈希） |
| T1-01 | `935e20f` |
| T1-02 | `1f39378` |
| T1-03 | `b25663e` |
| T1-04 | `ffbb486` |
| T1-05 | `7480057` |
| T1-06 | 随本文件提交；用 `git log -1 --format=%h --grep="^T1-06 "` 读取 |
| T1-07 | `c92139f`（实现）；AC24 浏览器实测与评审记录在说明以 `T1-RV3` 开头的提交中 |

修复轮验证补充（2026-11-11，以上阶段与历史结果不重写）：RV01～RV11 完成修复，新增 26 个含 AC 编号的回归方法。D 独立执行相关 14 个 AC 筛选、新增回归和最终全量；Python 3.11.15 全量 67 tests / 21.386s，0 失败、0 错误、0 跳过，退出 0。Apple clang 21.0.0 实际后端及临时目录演示均通过，输出 `15 / 120 / 1`。逐项证据见 [fix-summary](../review/fix-summary.md) 与 [D 报告](../review/fixes/agent-D.md)；AC18 用户人工目视仍未完成。

```bash
# 已验证 2026-11-11；shell zsh；Python 3.11.15；本机 clang 可用
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -v
```
