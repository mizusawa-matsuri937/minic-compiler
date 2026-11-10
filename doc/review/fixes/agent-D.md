# D：测试可移植性修复与独立集成验证

日期：2026-11-11 Asia/Taipei（执行记录对应 2026-11-10 UTC）。基线 `main / 2fa29b29440069881b91735e13c9a870450ef918`。本轮没有 Git 写操作；保留已有审查、交接及其他所有者修改。

RV11 已按同一失败用例完成“修前失败→修后通过”。最终 Python 3.11.15 全量 **67 tests，0 失败、0 错误、0 跳过，退出 0**；新增回归 **26 tests 全通过**。真实 Apple clang 21.0.0 的后端测试和演示实际执行；浏览器 RV08 技术复核通过所测两样例，但 **AC18 用户离线人工验收仍未执行**。

## 文件与根因

D 仅改原测试 `tests/test_backend.py`，新增 `tests/test_review_portability.py`、本报告及 `evidence/D/`。没有改 A/B/C 业务文件、其他原测试、fixtures、examples、spec、AC 或规则。

- RV11 根因：原测试把 `sys.executable` 直接拼进 shebang。解释器路径含空格时系统不能按该路径启动 Python；假 clang 存在并有执行权限，但未执行，编译器只能报告“无法运行 clang”。这与“工具已启动、输出诊断、退出 7”的原测试目标不符。
- 修复：用固定 `#!/bin/sh` 和 `exec`，通过标准库 `shlex.quote` 分别引用解释器路径及 Python `-c` 内容。新回归创建同时含空格、单引号的解释器软链，先断言实际 `sys.executable` 为该软链，再在其下运行原 `test_ac17_failed_clang_keeps_frontend`，断言恰执行 1 项且无跳过。
- 原断言全部保留；增加直接调用工具退出 7、stdout 为空、stderr 精确为 `test clang diagnostic\n` 的断言，以及编译失败后完整 7 件前端/IR 产物集合断言。
- 配合 A 的 RV05，将 mock clang 命令的所有输入/输出文件参数精确期望更新为 `./source.ll`、`./source.opt.ll`、`./source.s`、`./source`，仍逐条比较三条完整命令，没有删减断言。

## RV11 修前与修后证据

工作目录均为 `/Users/aqua_night/codex_project/编译原理/minic-compiler`，执行 shell 为 zsh。以下同一命令在修复前、后均实际运行：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_review_portability.py -v
```

| 时点 | 实际结果 | stdout / stderr / 退出码 |
|---|---|---|
| 修前 | 外层 1 test 失败；内层原用例 1 test 失败。工具未启动，缺少 `test clang diagnostic`，编译器报告 `无法运行 clang：[Errno 2] No such file or directory` | [before.stdout](evidence/D/rv11-before.stdout) 为空；[before.stderr](evidence/D/rv11-before.stderr) 保存完整双层 traceback；[before.exit](evidence/D/rv11-before.exit) 为 1 |
| 修后 | 同一回归 1 test / 0.667 s，OK，0 跳过 | [after.stdout](evidence/D/rv11-after.stdout) 为空；[after.stderr](evidence/D/rv11-after.stderr)；[after.exit](evidence/D/rv11-after.exit) 为 0 |
| RV05 期望同步后 | 原 AC17 3 tests / 0.634 s 全通过 | [AC17 stderr](evidence/D/ac17-targeted.stderr)，[exit](evidence/D/ac17-targeted.exit) 为 0 |

另以 [probe_rv11.py](evidence/D/probe_rv11.py) 实际捕获成功启动后的底层命令输出；[rv11-tool-proof.json](evidence/D/rv11-tool-proof.json) 保存工具、生成器、编译器三条完整命令和结果。工具 stdout 空，stderr 恰为 `test clang diagnostic\n`，退出 7；编译器 stdout 空，stderr 恰为 `后端错误: test clang diagnostic\nclang 执行失败，退出码 7\n`，退出 3。产物为 `tokens.txt/json`、`ast.json/txt/html/dot`、`demo.ll`，没有后端产物。探针自身退出 0。

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B doc/review/fixes/evidence/D/probe_rv11.py
```

## 独立核对其他组的回归有效性

D 逐项阅读最终 `test_review_paths.py`、`test_review_generated.py`、`test_review_ast.py` 及对应实现，没有用“文件名含 RV”代替触发条件核对。

- A：RV01 确实覆盖原地无扩展名源、目录/源符号链接、硬链接、选定分析器、输出别名、父子路径冲突，并在拒绝前后核对保护文件字节。RV04 用真实 clang 编译六种固定产物名，检查 JSON 可解析、精确产物集合、程序输出；D 指出的非 JSON 产物仅检查存在的缺口由 A 补为 HTML/SVG、DOT/digraph、文本 Program、记号 NUMBER 内容断言。A 另外补了大小写变体重复编译和词法失败清理回归，修复本轮新增边界。RV05 用 `-demo`、`@demo` 真正编译运行，并比较不同输出目录文本产物。
- B：RV02 明确建立同秒同大小 timestamp pyc，核对 header 和缓存字节未变，先证明普通 loader 实际读旧，再核对独立 CLI 与生产 loader 读新。RV03 覆盖含 kind/lexeme 的根、嵌套、列表、默认动作、传递动作及原记号输入未修改。RV06 用原始字节 CR/CRLF/LF 对照 API 与独立 CLI。RV09 精确比较所有转义、单物理行、4 列且 JSON 原值保留。D 指出深 JSON 仅计数并与同一序列化器对照不足以独立证明语法正确；B 已补隔离 `-I` 子进程使用标准库 `json.loads` 并迭代校验叶序。只有测试 reader 提高递归限，生成器和编译器未提高默认限制。
- C：1000 项表达式、550 层 if/block 的语义/作用域、1050 层语句 IR、全部深展示器，以及集成/独立 JSON 字节一致均命中报告边界；真实 clang 运行长表达式及深控制样例，输出分别为 `1000`、`8/7`。RV08 自动回归核对 200 字符全标签和实际度量脚本，实际几何由 D 浏览器测量补足；没有把脚本文字存在当成视觉成功。RV10 同时验证 SPACE 可见标签与全部 128 个 ASCII 的 DFA 分组签名，未只改标题而漏验转换数据。

## 最终环境、命令与结果

[environment.json](evidence/D/environment.json)：Python `/Users/aqua_night/.local/bin/python3.11`，版本 3.11.15；macOS 26.5.1 arm64；`/usr/bin/clang` 为 Apple clang 21.0.0。Python 编译器信息中的 Clang 22.1.3 是构建 Python 的编译器，并非本次 LLVM 后端版本。

所有生成器、测试源、缓存和编译产物均在临时目录，未使用仓库 `build/`、`out/`。执行环境设置 `PYTHONDONTWRITEBYTECODE=1`；pyc 反例仅在测试自己的临时目录显式生成。每个测试名含 acNN，所有新增代码只用 Python 标准库。

[run_final.py](evidence/D/run_final.py) 是已实际执行的复核入口，保存各命令的 cwd、参数、环境覆盖、完整 stdout/stderr、退出码和测试数量。重跑会更新 D 的本轮证据，不触碰旧审查证据。

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B doc/review/fixes/evidence/D/run_final.py targeted
```

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B doc/review/fixes/evidence/D/run_final.py integration
```

| 检查 | tests | 失败/错误/跳过 | 退出码 | 证据 |
|---|---:|---|---:|---|
| AC02 / AC05 / AC06 / AC10 | 3 / 4 / 5 / 2 | 各 0/0/0 | 各 0 | `evidence/D/ac02.json`、`ac05.json`、`ac06.json`、`ac10.json` |
| AC13 / AC14 / AC15 / AC16 | 5 / 5 / 4 / 8 | 各 0/0/0 | 各 0 | `evidence/D/ac13.json` 至 `ac16.json` |
| AC17 / AC18 / AC19 / AC20 | 5 / 6 / 2 / 12 | 各 0/0/0 | 各 0 | `evidence/D/ac17.json` 至 `ac20.json` |
| AC21 / AC22 | 3 / 1 | 各 0/0/0 | 各 0 | `evidence/D/ac21.json`、`ac22.json` |
| `test_review*.py` 新增回归 | 26（9.002 s） | 0/0/0 | 0 | [new-regressions.json](evidence/D/new-regressions.json) |
| `unittest discover -s tests -v` 全量 | 67（21.386 s） | 0/0/0 | 0 | [full-regression.json](evidence/D/full-regression.json) |
| 临时路径真实演示 | 不适用 | 未跳过真实 clang | 0 | [demo.json](evidence/D/demo.json)、[demo-products.json](evidence/D/demo-products.json) |

AC 筛选有交叉，不能把表内数量相加当成独立测试数。最终独立数量为原有 41 + 新增 26 = 67。全量 stdout 为空，stderr 逐条 `ok`，末尾 `Ran 67 tests in 21.386s / OK`。

演示实际通过 `bash -c 'echo 5 | bash scripts/demo.sh'`，环境 `MINIC_PYTHON` 为上述真实 3.11 绝对路径，`MINIC_BUILD_DIR`、`MINIC_OUT_DIR` 均指向 `TemporaryDirectory` 下含空格路径；精确实际路径记录在 demo.json。stdout 列产物后最后三行为 `15`、`120`、`1`；stderr 为编译产物路径，退出 0；5 个分析器/报告文件和 10 个编译产物均存在且非空。AC15/AC16/RV04/RV05/RV07 与演示均实际调用真实 clang，无跳过。

针对性与集成前后分别保存 `source-snapshot-{targeted,integration}-{before,after}.json`；共 60 个源码、测试、脚本、规则、样例/fixture 的逐文件 SHA256 在四份快照中完全一致，验证期间无业务或测试改动。主对话同期文档编辑不影响这组快照。

## RV08 浏览器技术复核

完整观察、精确 BBox 和方法见 [browser-observations.txt](evidence/D/browser-observations.txt)，度量脚本为 [geometry.js](evidence/D/geometry.js)。Safari 26.5、14px monospace、本地 file 页面。baseline/fixed 原 HTML SHA256 分别见 [baseline](evidence/D/browser-baseline-sha256.json)、[fixed](evidence/D/browser-fixed-sha256.json)。

| 样例 | 节点/字段 | viewBox 宽×高 | 文字越框 | 节点文字重叠 | 字段文字重叠 | 文字越 SVG 边界 |
|---|---|---|---:|---:|---:|---:|
| 修前 200 字符标识符 | 6/5 | 5200×410 | 3 | 1 | 0 | 2 |
| 修后同样例 | 6/5 | 5470.125×396 | 0 | 0 | 0 | 0 |
| 修后 demo | 46/45 | 3321.34375×696 | 0 | 0 | 0 | 0 |

修后均实际读到 `data-layout="measured"`。长 Identifier 的真实字形宽 1778.46875，矩形宽 1802.46875，左右各 12 px；相邻文字从重叠 42.46875 px 变为间隔 48 px。全标签未截短。原 HTML 技术目视确认 VarDecl 开头由左侧裁切恢复完整，demo 可见节点和字段可辨。宽图需要滚动，截图只覆盖浏览器可见部分，完整几何结论来自全部节点/字段实际 getBBox。没有宣称截图含完整大图，也未声称保存了 PNG。

以下已验证脚本重建 baseline、fixed 原 HTML 和只追加诊断的测量副本；`--hold` 保持临时文件等待浏览器检查，回车后清理。脚本无 --hold 的创建流程已实测退出 0，见 [browser-reproduction.stdout](evidence/D/browser-reproduction.stdout)。无需依赖历史 `/tmp` 文件：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B doc/review/fixes/evidence/D/prepare_browser.py --hold
```

浏览器仅新开一个检查标签页，结束时关闭并保留原来的 4 页。未改变安全设置、未安装自动化依赖、未断开系统网络。检查者技术复核不能代替用户 AC18。

## 未验证及边界

未验证其他操作系统、其他浏览器、clang 15 最低版本、答辩电脑/投影设备；未重跑 Python 3.14。没有据有限深度样例宣称任意规模输入都可处理。没有处理或擅定 `INT_MIN / -1` 行为。AC18 用户离线人工验收保持未完成。本轮验证通过后未再修改业务或测试。
