# 交接：task1 实现完成 → 交给评审

日期：2026-11-10。本文件记录本轮实施快照，接手时先核对 Git 状态。

## 当前范围与状态

- 用户授权：按顺序完成 T1-01 至 T1-06，编码、unittest、实测记录和六次本地阶段提交；不推送、不改写历史、不修改 Git 配置。
- 起始分支 `main`，起点 `6dfbbd0`，工作区干净；实际已存在 origin，与旧交接“没有远端”的快照不同。
- T1-01 至 T1-06 编码及自动验证完成；实施 AC 21/22。AC18 自动通过但人工未执行，保持未勾选。
- README、tasks/checklist 已更新；spec 完全未改，design 仅在“实施中的调整”追加事实。计划维护者需要更新 spec/design 顶部和 project-config 的历史进度/环境描述。
- 此交接与收尾内容随 T1-06 本地提交；该阶段的哈希用 `git log -1 --format=%h --grep="^T1-06 "` 读取。提交后以 `git status --short --branch` 核对工作区，未执行任何远端操作。

## 阶段交付与提交

| 阶段 | 改动与阶段检查 | 本地提交 |
|---|---|---|
| T1-01 | 正规式、Thompson、子集法、DFA 最小化、独立扫描器；5 tests 通过 | `935e20f` |
| T1-02 | 文法动作、FIRST、规范 LR(1)、冲突处理、ccgen CLI；7 tests 通过 | `1f39378` |
| T1-03 | 编译器前端、三类诊断、语义作用域、AST 展示、独立运行；9 tests 通过 | `b25663e` |
| T1-04 | LLVM IR、clang 三步后端、运行和失败保留；13 tests 通过且无跳过 | `ffbb486` |
| T1-05 | AST 专项验证和九节报告；3 tests 通过，人工 AC18 未做 | `7480057` |
| T1-06 | 演示脚本、依赖/样例核验、全量与逐 AC 证据、README、交接；41 tests 通过 | 本文件所属 T1-06 提交 |

阶段原始日志位于 `doc/task1/evidence/T1-01.log` 至 `T1-06.log`；T1-02 初次失败的日志也保留，修正模板笔误后通过。T1-06 收尾补齐 NFA 的 BFS 编号及冲突声明实际行号，随后重新运行全量回归与全部逐 AC 命令，没有删测试或降低断言。

## 每个 AC 的实测与证据

以下均为 AI 实际执行的机器验证，日期 2026-11-10，测试命令退出码均为 0，无跳过。失败情形断言的是被测命令应返回的 1/2/3。完整测试方法名、工作目录、解释器、输出及退出码见各日志。

| AC | 状态 | 观测结果 | 测试数与证据 |
|---|---|---|---|
| AC00 | 结构检查通过，人工审阅未记录 | 计划结构检查：29 条规则、23 项 AC、7 个阶段；本轮按用户授权实施。 | 结构检查；[AC00.log](../task1/evidence/AC00.log) |
| AC01 | 通过 | 两次生成的五个文件逐字节一致，分析器无项目包 import。 | 1 tests；[AC01.log](../task1/evidence/AC01.log) |
| AC02 | 通过 | 四则运算文法生成成功，1+2*3 的树形与叶子顺序正确。 | 1 tests；[AC02.log](../task1/evidence/AC02.log) |
| AC03 | 通过 | 六类正规式的接受/拒绝串均正确。 | 1 tests；[AC03.log](../task1/evidence/AC03.log) |
| AC04 | 通过 | (a|b)*abb 最小 DFA 为 4 态；长度 0–8 的 511 个串在 NFA/DFA/最小 DFA 上结果一致。 | 2 tests；[AC04.log](../task1/evidence/AC04.log) |
| AC05 | 通过 | 16 个记号、种别码、属性值、最长匹配和 1:5 / 2:13 位置正确。 | 2 tests；[AC05.log](../task1/evidence/AC05.log) |
| AC06 | 通过 | 恰有两条 L001（1:11、2:7），退出 1，仅保留记号产物。 | 1 tests；[AC06.log](../task1/evidence/AC06.log) |
| AC07 | 通过 | 38 条产生式及编号正确，16 个 FIRST 集；264 态，2 处 else/r16 冲突均移进。 | 2 tests；[AC07.log](../task1/evidence/AC07.log) |
| AC08 | 通过 | 未声明的移进/归约及归约/归约冲突均拒绝，退出 2，列出项目且不写生成物。 | 2 tests；[AC08.log](../task1/evidence/AC08.log) |
| AC09 | 通过 | 四种指定错误、动作语法错误及冲突指令定位均正确，失败不改已有输出。 | 2 tests；[AC09.log](../task1/evidence/AC09.log) |
| AC10 | 通过 | 三条表达式的运算树、优先级和左结合完全匹配预期。 | 1 tests；[AC10.log](../task1/evidence/AC10.log) |
| AC11 | 通过 | else 绑定内层 if，外层没有 else 字段。 | 1 tests；[AC11.log](../task1/evidence/AC11.log) |
| AC12 | 通过 | 1:15 和 1:10 的 P001、实际记号和期望集正确，退出 1，不留 AST/IR。 | 2 tests；[AC12.log](../task1/evidence/AC12.log) |
| AC13 | 通过 | S002/S001/S003/S001 的四条位置与顺序正确；作用域、初值和槽绑定检查通过。 | 2 tests；[AC13.log](../task1/evidence/AC13.log) |
| AC14 | 通过 | 4 个 entry alloca、所需指令和 scanf/printf 调用数正确；IR 和前端文本确定。 | 1 tests；[AC14.log](../task1/evidence/AC14.log) |
| AC15 | 通过 | O0/O2 输入 5、10 分别输出 15/120/1、55/3628800/0；可执行文件和后端产物真实生成。 | 2 tests；[AC15.log](../task1/evidence/AC15.log) |
| AC16 | 通过 | 7 个运行样例在 O0/O2 均逐字匹配 stdout，全部退出 0。 | 7 tests；[AC16.log](../task1/evidence/AC16.log) |
| AC17 | 通过 | 缺失或失败 clang 退出 3，保留记号、AST、IR；后端调用参数验证通过。 | 3 tests；[AC17.log](../task1/evidence/AC17.log) |
| AC18 | 部分通过（待人工） | 2 个自动测试通过：四文件、离线 SVG、结点数、字段连线、转义及布局矩形无重叠；人工目视未执行。 | 2 tests；[AC18.log](../task1/evidence/AC18.log) |
| AC19 | 通过 | 九节报告自包含，状态数、38 条产生式、FIRST、264 行 ACTION/GOTO 与冲突均对应表数据。 | 1 tests；[AC19.log](../task1/evidence/AC19.log) |
| AC20 | 通过 | 仓库外 python3 -I 独立运行；tokens.json、ast.json 与编译器输出逐字节相同。 | 2 tests；[AC20.log](../task1/evidence/AC20.log) |
| AC21 | 通过 | 全部 import 属标准库/仓库；全部测试名含 AC；规则与样例逐字节一致；双 Python 全量通过。 | 2 tests；[AC21.log](../task1/evidence/AC21.log) |
| AC22 | 通过 | AST 含六类演示语句和 if-else；演示先列文件路径，最后输出 15/120/1，退出 0。 | 1 tests；[AC22.log](../task1/evidence/AC22.log) |

全量 Python 3.11.15：41 tests / 24.045s；默认 Python 3.14.6：41 tests / 24.529s。二者均 OK、零跳过。三套检查同时运行，耗时包含竞争，不作为独立性能基准。证据：[T1-06](../task1/evidence/T1-06.log)、[Python 3.14 全量](../task1/evidence/python314-full.log)。

最终执行了 `python3 -m unittest discover -s tests -v && echo 5 | bash scripts/demo.sh`，整体退出 0，demo 标准输出最后三行为 `15`、`120`、`1`；构造统计 NFA 177 / DFA 48 / 最小 DFA 44 / 产生式 38 / LR(1) 264 / 消解冲突 2。

## 计划调整与理由

所有发现与 R/AC 影响均先记入 [design 第 14 节](../task1/design.md#14-实施中的调整)，没有修改 spec 规则或 AC：

1. 实际默认 Python 是 3.14.6，另有 3.11.15；临时选择 3.11 后完成每阶段检查，最后也验证默认版本。zsh 启动会重设继承 PATH，改为启动后 export 并实测版本；初期采集日志的版本标记已纠正，没有改写提交历史。影响 R27 / AC21。
2. design 的 fixed 语法判据不能覆盖 `[a]`、`a|a` 这类唯一串；按 R07 递归求唯一字符串，并增加测试。影响 AC05。
3. AC14 要比较 ast.html，原排期却在下一阶段才实现：AST 展示提前随 T1-03 交付，T1-05 做专项验收。影响 R21/R22/R29、AC13/AC14/AC18。
4. 报告要求九节但合写 ACTION/GOTO 时只有八项：将 ACTION、GOTO 分成两节，保留原顺序与全部内容。影响 R23 / AC19。
5. 后端在产物目录中用文件名调用 clang，避免优化 IR 写入不同输出目录的绝对路径；符合确定性要求。核对了 LLVM LangRef 的 call/add/sdiv，未采用外部代码。GitHub 上游测试页面抓取失败，检索得到的镜像用法仅供对照。影响 R16–R20/R29、AC14–AC17。

## 环境与复核入口

- macOS arm64，Apple clang 21.0.0；Python 3.11.15、3.14.6 实际通过。无第三方 Python 包，无依赖清单。
- 每个测试均在 TemporaryDirectory 中生成分析器/产物；演示测试用 MINIC_BUILD_DIR、MINIC_OUT_DIR 重定向到临时目录。只有 tasks 中的人工生成命令和最终演示写 build/out。
- [README](../../README.md) 提供运行说明；[checklist](../task1/checklist.md) 的每个 AC 都有可独立复制的实测命令。
- 最终演示产物已生成：`out/demo/ast.html`、`out/demo/demo.ll`、`out/demo/demo.opt.ll`、`out/demo/demo.s`、`out/demo/demo`；报告为 `build/minic/report.html`。它们被 .gitignore 忽略，可随时通过演示命令再生。

## 未完成或未验证事项

- **AC18 人工目视未执行、未勾选**：用户离线打开 `out/demo/ast.html`，确认 Program 根、层次及结点/连线可读性；自动坐标检查不能代替这一项。
- AC00 的独立人工审阅与报告的建议人工浏览未记录；未验证其他机器、其他操作系统、答辩机 clang。
- 计划中的 5 秒生成/60 秒测试只是预算；测试实测通过不等于大规模压力验证。
- 按原设计不做运行时错误检查；LLVM sdiv 的除零及 INT_MIN / -1 边界没有定义结果。没有新增语言行为或改 AC，评审者可核对 R18 的边界描述是否需要另开变更。
- spec/design 顶部与 project-config 的历史“仅规划”描述留给计划维护者更新；本轮只补充授权的调整和执行证据。
- 没有推送、PR、合并或 Git 配置修改；远端与协作流程仍由用户决定。

## 下一步

1. 用户完成 AC18 人工检查；通过后由计划维护者填写证据并勾选。
2. 评审者阅读 design 调整、源码和逐项日志，更新计划的状态快照；出现新问题时新增复现测试，再修复。
3. 换答辩机器时重新运行全部测试与 demo，特别核对 clang 用例不能跳过。

文件入口：[README](../../README.md)、[spec](../task1/spec.md)、[design](../task1/design.md)、[tasks](../task1/tasks.md)、[checklist](../task1/checklist.md)。
