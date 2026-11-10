# RV01～RV11 修复汇总

日期：2026-11-11。范围：`doc/review/README.md` 的 11 项确认问题；不处理作业程序设计文档、PPT、远端材料或 `INT_MIN / -1` 合同选择。原审查报告、证据和历史验收记录保留。

## 基线与协作

- 开始分支 `main`，HEAD `2fa29b29440069881b91735e13c9a870450ef918`，比 `origin/main` 领先 6 个本地提交；暂存区和已跟踪文件无修改。
- 初始未跟踪文件为原 `doc/review/` 全部材料及 `doc/handoffs/2026-11-10-task1-review-to-fix.md`。本轮不覆盖、不清理，也不将这些已有材料顺带暂存。
- 已读取 AGENTS、项目配置、README、审查交接、task1 四文件、审查汇总与六份阶段报告，并核对实际实现。计划结构检查退出 0；原规则、AC 预期及 AC18 未勾选状态不变。
- 实际环境：Python 3.11.15（`/Users/aqua_night/.local/bin/python3.11`）、Apple clang 21.0.0、macOS arm64。所有测试分析器、源文件、缓存、编译产物均放临时目录。

四个子对话通过 `spawn_agent` 的实际参数创建，均为 `model="gpt-6-astra"`、`reasoning_effort="high"`、`fork_turns="none"`；必要要求完整传入，禁止再次分派。

| 子对话 | 负责问题 | 独占业务/测试文件 | 结果 |
|---|---|---|---|
| A | RV01、RV04、RV05；驱动 RV06/RV07 接入 | `minic/__main__.py`、`minic/backend.py`、`tests/test_review_paths.py` | [agent-A](fixes/agent-A.md) |
| B | RV02、RV03、RV06、RV09；独立解析器 RV07 | `minic/frontend.py`、两个模板、`tests/test_review_generated.py` | [agent-B](fixes/agent-B.md) |
| C | RV07 全链路牵头、RV08、RV10 | `minic/semantic.py`、`irgen.py`、`astviz.py`、`ccgen/report.py`、`tests/test_review_ast.py` | [agent-C](fixes/agent-C.md) |
| D | RV11、回归覆盖复核、最终独立验证 | `tests/test_backend.py`、`tests/test_review_portability.py` | [agent-D](fixes/agent-D.md) |

主对话负责接口协调、设计调整、最终 diff 与证据审阅、README/交接/验收事实补充及本地提交。子对话没有 Git 写权限授权。原测试的后端参数期望由 D 同步，其他文件只有所属子对话修改。

## 实施调整

已在修改业务前写入 [design §14](../task1/design.md)：统一产物规划和路径身份检查；与固定产物冲突的后端主名追加 `.program`；clang 文件参数加 `./`；直接执行当前生成源码而不复用 pyc；内部记号类型与用户 AST 字典分开；源文件读取保留 CR/LF；文本属性转义；迭代 JSON/语义/IR/展示处理；离线 SVG 根据实际字形测量重排；DFA 空格表头显式可见。没有增加语言特性或改变作用域、整数运算和文法。

## 逐项复现、修复与证据

所有问题都有新增 unittest 反例先失败、同例修后通过的记录。测试进程修前退出 1，修后退出 0；被测编译器本身的退出码另列，成功退出也可能伴随数据丢失。下面的子测试数量不相加作为独立测试总数。

| ID | 修前实际问题 | 修复与通过判据 | AC / 证据 |
|---|---|---|---|
| RV01 | 输出目录内无扩展名源文件、所选分析器被清理；还覆盖路径别名、硬链接及父子路径冲突 | 在清理前统一预检；冲突退出 2，源/分析器及旧产物字节不变；正常旧产物仍被准确清理 | AC06/18/20；[A 修前](fixes/evidence/A/before.log)、[父子路径修前](fixes/evidence/A/before-parent.log)、[A 最终](fixes/evidence/A/after-final.log) |
| RV02 | 显式构造同秒、等长源码与有效旧 timestamp pyc 后，lexer 执行旧规则，parser 返回旧 `Past` | 直接编译当前源码；普通 import 控制组仍命中旧缓存，而生产 load 与独立 CLI 使用新 `Next` 完全一致 | AC20；[B 修前](fixes/evidence/B/before.json)、[B 最终](fixes/evidence/B/final.json) |
| RV03 | 根、嵌套字段、列表、缺省动作孩子和传递动作中，合法 Node 静默丢失，CLI 仍退出 0 | 内部值栈标记记号类型；五种 Node 变体完整保留，普通 token 传递和默认叶结点保持；输出全为原生容器/标量，输入未变 | AC02/20；[B 修前](fixes/evidence/B/before.json)、[B 最终](fixes/evidence/B/final.json) |
| RV04 | 六个保留阶段名作为源主名时，可执行文件覆盖同名阶段产物 | 统一规划并确定性追加 `.program`；六组真实 clang 编译运行输出 `1`，十项产物独立，JSON/文本/HTML/DOT 内容断言通过 | AC15/18；[A 修前](fixes/evidence/A/before.log)、[A 最终](fixes/evidence/A/after-final.log) |
| RV05 | `-demo.mc` 的后端输入被当选项，编译器退出 3 | 所有 clang 文件参数显式 `./`；`-demo`、`@demo` 实际编译运行退出 0，输出 `1`，跨目录文本产物一致 | AC14/15；[A 修前](fixes/evidence/A/before.log)、[A 最终](fixes/evidence/A/after-final.log) |
| RV06 | 独立 lexer 改写 CR/CRLF；驱动语义位置由 1:14 错成 2:7 | 两入口 UTF-8 原字符读取；CR/CRLF/LF 词素及位置与 API 一致，驱动恢复 S001 1:14 | AC05/13/20；[B 最终](fixes/evidence/B/final.json)、[A 最终](fixes/evidence/A/after-final.log) |
| RV07 | calc 495 项独立 JSON、mini-C 1000 项输出及后续语义/IR/四种展示各自可触发 RecursionError | 全链显式栈，默认业务递归上限不变；独立/集成 AST 字节一致，独立 JSON 解码验证叶序；1000 项实际输出 `1000`，550 层作用域程序输出 `8 / 7` | AC02/10/13/14/16/18/20；[B 最终](fixes/evidence/B/final.json)、[C 修前](fixes/evidence/C/before.log)、[C 修后](fixes/evidence/C/after.log) |
| RV08 | Safari 200 字符标识符图：3 处越框、1 处相邻文字重叠（42.46875 px）、2 处文字超 SVG | 实际字形测量后重排；长标识符 6 结点、demo 46 结点的文字越框、节点/字段文字重叠和视口外文字均为 0；完整标签保留 | AC18；[C 回归](fixes/evidence/C/after.log)、[D 真实浏览器](fixes/evidence/D/browser-observations.txt) |
| RV09 | 词素控制字符产生多行/多列的单记号文本 | 文本转义反斜杠与控制字符；同记号一个物理行、四列，JSON 原词素保持；含 CR/LF/tab/NUL/DEL/Unicode 行分隔符 | AC05/20；[B 修前](fixes/evidence/B/before.json)、[B 最终](fixes/evidence/B/final.json) |
| RV10 | `character(32)` 为不可见的裸空格 | 显示为 `SPACE (U+0020)`；展开全部 ASCII 分组，转换签名保持一致 | AC19；[C 修前](fixes/evidence/C/before.log)、[C 修后](fixes/evidence/C/after.log) |
| RV11 | 含空格解释器路径的假 clang 未启动，目标测试退出 1 | shell 启动器正确引用路径；含空格和单引号的 Python 路径通过，直接验证假工具 stderr/退出 7，再验证编译器退出 3 与前端产物 | AC17/21；[D 修前](fixes/evidence/D/rv11-before.stderr)、[D 修后](fixes/evidence/D/rv11-after.stderr) |

集成前又复现并修正 RV04 清理的大小写变体：`AST.JSON.mc` 第二次编译原会错误退出 2。实际阶段输出之间继续互斥检查，历史清理候选统一保护输入；新增重复编译与词法失败清理回归通过。见 [修前](fixes/evidence/A/before-case-variant.log)、[修后](fixes/evidence/A/after-final.log)。此调整在实施前追加到 design §14。

新测试分为 A 10、B 6、C 9、D 1，共 **26 个方法**，均带 AC 编号。C 另对基线做只读兼容核对：11 个样例的语义诊断、槽绑定、AST 文本相同，其中 10 个语义合法样例的 IR 逐字节相同，见 [compatibility.log](fixes/evidence/C/compatibility.log)。

## 集成验证与本地提交

D 在 A/B/C 冻结后独立完成以下检查，全部退出 0：

| 检查 | 实测结果 | 证据 |
|---|---|---|
| AC02、05、06、10、13～22 逐项筛选 | 14 组全部通过，无跳过；组间有交叉，不相加计总数 | [D 报告](fixes/agent-D.md)、`fixes/evidence/D/acNN.json` |
| 新增反例回归 | 26 tests / 9.002s，0 失败/错误/跳过 | [new-regressions.json](fixes/evidence/D/new-regressions.json) |
| Python 3.11.15 全量 | **67 tests / 21.386s，0 失败/错误/跳过** | [full-regression.json](fixes/evidence/D/full-regression.json) |
| 实际后端与演示 | Apple clang 21.0.0 后端用例实际执行；临时目录演示输出 `15 / 120 / 1`，5 个生成文件、10 个编译产物均非空 | [demo.json](fixes/evidence/D/demo.json)、[产物核对](fixes/evidence/D/demo-products.json) |
| 检查快照 | 针对性/全量检查前后共四份快照的 60 个源码/测试/脚本/规则/样例文件 SHA-256 一致 | `fixes/evidence/D/source-snapshot-*.json` |
| RV08 真实浏览器 | Safari 26.5，长标识符和 demo 的文字几何检查均通过；用户人工验收另计 | [browser-observations.txt](fixes/evidence/D/browser-observations.txt) |

修前与修后证据只新增到 `fixes/evidence/`，不覆盖历史审查日志。修复按一个完整集成批次提交，避免 A/B/C 深 AST 接口处于不兼容的中间提交；提交说明为 `T1-RV 修复 RV01-RV11 并补充反例回归`，本文件与交接随该批次提交，实际哈希可用以下只读命令查到：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
git log -1 --format='%H %s' --grep='^T1-RV 修复 RV01-RV11 并补充反例回归$'
```

只做本地提交，不推送、不改写历史、不改 Git 配置；初始未跟踪审查材料保持原状。最新接手说明为 [修复交接](../handoffs/2026-11-11-task1-fixes-to-review.md)。

主对话最终只读核对：初始 52 份未跟踪材料逐文件 SHA-256 不变；D 验证的 60 个源码/测试/脚本/规则/样例文件未再变；67 个测试方法全部含 AC 编号；规则、样例、fixtures、spec 无差异；新文档链接有效；计划结构及暂存源码/文档的空白检查均退出 0。122 个暂存文件全部属于本轮授权范围，未混入初始材料。原始失败日志有 6 行 unittest 子测试输出自带行尾空格，完整暂存空白检查因此退出 2；为保留原始证据不改写这些日志。见 [precommit-audit.json](fixes/evidence/main/precommit-audit.json) 和 [plan-check.log](fixes/evidence/main/plan-check.log)。

## 未完成与边界

- **AC18 用户人工离线目视仍未完成、未勾选。** D 的 Safari 技术检查实际打开本地 HTML、测量真实字形并目视；没有断开网络，不冒充用户验收。
- 本轮未复验 Python 3.14、其他操作系统/浏览器、最低 clang 15、答辩电脑或 Graphviz 实际渲染。历史记录保留为历史，当前通过结论限本轮环境。
- 深缩进 JSON/文本与简单树布局会占用较大文件和视图；验证了上述合法深度，不声称任意规模均可处理。
- `INT_MIN / -1` 的 spec 与 design/README 合同口径仍交既定计划维护者决定，未引入新运算语义。原计划/项目配置中的历史状态由既定维护者维护；本轮仅追加必要设计调整和验证事实。
