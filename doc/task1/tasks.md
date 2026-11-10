# mini-C 编译器生成器与编译器成品 执行任务

状态：T1-00 至 T1-01 编码与阶段自动检查已完成（2026-11-10）；AC18 人工目视验收另计。规则与验收见 [spec](spec.md)，实现方法见 [design](design.md)，逐项复核见 [checklist](checklist.md)。

所有命令的工作目录是 `/Users/aqua_night/codex_project/编译原理/minic-compiler`，shell 为 zsh，Python 为临时 PATH 指向的 `python3`（3.11.15；默认系统命令为 3.14.6）。标“计划，未执行”的命令对应的代码尚未实现，执行后把实际结果补在该项下。各阶段按顺序进行，后一阶段依赖前一阶段的产物。

- [x] T1-00 完成四文件与计划检查。规则：全部；关联 AC00。
  - 文件：`doc/task1/` 四文件、`doc/project-config.md`、`README.md`、`.gitignore`。
  - 完成情况：已完成。目标、范围、29 条规则、AC00–AC22、设计、阶段和验收映射均已写出；阻碍实施的选择（语言、IR 路线）已由用户确认。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 scripts/check_plan.py doc/task1
  ```

  实际结果：见 [checklist](checklist.md) 的 AC00。

- [x] T1-01 实现词法分析器生成器。规则：R04–R08；关联 AC03、AC04、AC05。
  - 文件：`ccgen/errors.py`、`ccgen/regex.py`、`ccgen/nfa.py`、`ccgen/dfa.py`、`ccgen/lexspec.py`、`ccgen/codegen.py` 与 `ccgen/templates/lexer_template.py`（词法部分）、`rules/minic.lex`、`tests/test_regex.py`、`tests/test_lexgen.py`、`tests/test_lexer_minic.py`、`tests/fixtures/lex_ok.mc`。
  - 完成情况：编码与自动检查已完成。交付正规式解析、Thompson 算法、子集法、等价状态法，以及能独立运行的 `lexer.py`；此阶段用 Python 接口生成并调用词法分析器，并提供 `lexer_tables.json` 内容的构造函数。`python3 -m ccgen` 命令行入口和写盘在 T1-02 补齐。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac03 -k ac04 -k ac05 -v
  ```

  计划观测：名字含 `ac03`、`ac04`、`ac05` 的用例全部 `ok`，退出码 0；用例数量以实际为准。实际结果：2026-11-10：5 个测试全部 OK（0.044s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-01.log`。

- [x] T1-02 实现语法分析器生成器与生成命令。规则：R01–R03、R09–R11、R26、R29；关联 AC01、AC02、AC07、AC08、AC09。
  - 文件：`ccgen/grammar.py`、`ccgen/lr1.py`、`ccgen/codegen.py` 与 `ccgen/templates/parser_template.py`（语法部分）、`ccgen/__main__.py`、`rules/minic.grammar`、`tests/test_parsegen.py`、`tests/test_ccgen_cli.py`、`tests/fixtures/` 下的 `calc.lex`、`calc.grammar`、`ambiguous.grammar`。
  - 完成情况：编码与自动检查已完成。交付 FIRST 集、LR(1) 项目集规范族、分析表与冲突处理、构造动作、独立运行的 `parser.py`、两份表文件和 `python3 -m ccgen` 命令。`report.html` 此阶段可以只有标题和占位，内容在 T1-05 完成。

  ```bash
  # 已验证 2026-11-10；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic && python3 -m unittest discover -s tests -k ac01 -k ac02 -k ac07 -k ac08 -k ac09 -v
  ```

  计划观测：生成命令退出码 0，并打印五个文件的路径和一行统计，其中 LR(1) 状态数预计为 264（估算，以实际为准）、已消解冲突数为 2；所列 AC 的用例全部 `ok`。实际结果：2026-11-10：7 个测试全部 OK（0.500s），无失败、错误或跳过；退出码 0。证据：`evidence/T1-02.log`。

- [ ] T1-03 实现编译器驱动的前端与诊断。规则：R12–R15、R21（记号文件与 `ast.json`）、R24、R25；关联 AC06、AC10、AC11、AC12、AC13、AC20。
  - 文件：`minic/__main__.py`、`minic/frontend.py`、`minic/diagnostics.py`、`minic/semantic.py`、`examples/demo.mc`、`tests/test_minic_frontend.py`、`tests/test_semantic.py`、`tests/test_standalone.py`、`tests/fixtures/` 下的 `lex_error.mc`、`expr.mc`、`dangling_else.mc`、`syntax_chain.mc`、`syntax_eof.mc`、`semantic_error.mc`。
  - 完成情况：未执行。交付 `python3 -m minic` 命令的阶段 1 至 3 和 `--stop-after`：加载生成的分析器、写出 `tokens.*` 与 `ast.json`、统一诊断格式、退出码、语义检查；并验证 mini-C 的 AST 结构和分析器的独立运行。

  ```bash
  # 计划，未执行；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac06 -k ac10 -k ac11 -k ac12 -k ac13 -k ac20 -v
  ```

  计划观测：所列 AC 的用例全部 `ok`，退出码 0。实际结果：未执行。

- [ ] T1-04 实现 LLVM IR 生成与 clang 后端。规则：R16–R20；关联 AC14、AC15、AC16、AC17。
  - 文件：`minic/irgen.py`、`minic/backend.py`、`minic/__main__.py`（阶段 4 至 6 与 `-O`、`--clang`、`--run`）、`tests/test_irgen.py`、`tests/test_backend.py`、`tests/fixtures/run/` 下 6 个运行样例。
  - 完成情况：未执行。交付 IR 生成、三条 clang 命令的调用、可执行文件的运行，以及 clang 缺失时的降级行为。

  ```bash
  # 计划，未执行；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh；需要 clang 在 PATH 中
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac14 -k ac15 -k ac16 -k ac17 -v
  ```

  计划观测：所列 AC 的用例全部 `ok`，没有被跳过的用例（本机有 clang）；退出码 0。实际结果：未执行。

- [ ] T1-05 实现 AST 可视化与生成器构造报告。规则：R21（`ast.txt`、`ast.html`、`ast.dot`）、R22、R23；关联 AC18、AC19。
  - 文件：`minic/astviz.py`、`ccgen/report.py`、`tests/test_astviz.py`、`tests/test_report.py`。
  - 完成情况：未执行。交付三种 AST 展示文件和九节内容的 `report.html`。

  ```bash
  # 计划，未执行；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -k ac18 -k ac19 -v
  ```

  计划观测：所列 AC 的用例全部 `ok`，退出码 0。另需人工按 checklist 中 AC18、AC19 的手工命令在浏览器中离线打开 `ast.html` 和 `report.html` 目视检查，结果记入 checklist 的 AC18。实际结果：未执行。

- [ ] T1-06 完成演示脚本、全量回归与交接。规则：R27、R28；关联 AC21、AC22，并核对 AC01–AC20 的证据仍然有效。
  - 文件：`scripts/demo.sh`、`tests/test_project.py`、`README.md`、`doc/task1/checklist.md`、`doc/handoffs/` 下新增的交接文件。
  - 完成情况：未执行。交付一条命令的演示脚本、标准库依赖检查、全量测试结果，更新 README 的运行说明和 checklist 的实测记录。

  ```bash
  # 计划，未执行；工作目录 /Users/aqua_night/codex_project/编译原理/minic-compiler；shell zsh；需要 clang 在 PATH 中
  cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests -v && echo 5 | bash scripts/demo.sh
  ```

  计划观测：全部测试 `OK`，没有失败、错误和跳过；演示脚本退出码 0，标准输出最后三行为 `15`、`120`、`1`。实际结果：未执行。

阶段本地提交：遵循 [项目配置](../project-config.md)，每个阶段检查通过后提交一次，提交说明以阶段编号开头（如 `T1-01 词法分析器生成器`）。

| 阶段 | 提交标识 |
|---|---|
| T1-00 | 见 `git log` 中说明以 `T1-00` 开头的提交（本文件随该提交入库，无法在自身中预填哈希） |
| T1-01 | `935e20f` |
| T1-02 至 T1-06 | 未提交 |
