# 交接：task1 验收评审（Claude）→ 用户决策与收尾

日期：2026-11-11。本文件是该时间点的快照，接手时核对实际状态。

## 当前范围与状态

- 本轮目标和已授权范围：用户要求评审 task1 的完成情况。Claude 只读核对实现、独立复现全部 AC、做对抗性验证，并更新自己维护的计划文件状态；没有修改业务代码、测试、规则或样例。
- 当前分支/提交/未提交修改：分支 `main`。评审基线是 `bee4c08`（T1-RV 修复 RV01-RV11）。本次评审的文档与证据在说明以 `T1-RV2` 开头的提交中。本地领先 `origin/main`，尚未推送。Codex 第一轮审查留下的 53 个文件（`doc/review/` 下除 `fixes/`、`fix-summary.md`、`claude-acceptance/` 之外的内容，以及两份交接）仍未入库，本轮没有动它们。
- 当前任务目录与阶段：`doc/task1/`。T1-01 至 T1-06 已完成；只剩 AC18 的用户人工目视。
- README 与四文件是否同步：spec、design 的状态行和项目配置已按实测更新；tasks、checklist 由实现方维护，内容与实测相符，但 checklist 开头的状态行仍写着第一轮的“41 个测试”，以其末尾的 2026-11-11 补充为准。

## 结论

实现符合 spec。AC01–AC17、AC19–AC22 经独立复现全部通过；AC18 的自动化部分通过，人工目视仍需用户完成。没有发现需要返工的正确性问题。下面“发现”一节列出 2 个建议在答辩前处理的小问题和 3 个提示。

## 已完成与证据

环境：macOS 26.5.1 arm64，Python 3.11.15，Apple clang 21.0.0。所有产物写到仓库外的临时目录。证据在 [doc/review/claude-acceptance/](../review/claude-acceptance/)。

| 完成事项 | 相关任务/AC | 实际检查结果 | 证据位置 |
|---|---|---|---|
| 项目自带测试 | AC21 | Python 3.11.15：67 个测试通过，无失败、错误、跳过（约 23 秒）。Python 3.14.6：同样 67 个通过。测试前后已跟踪文件无变化 | 命令见下节 |
| 独立复现全部 AC | AC01–AC22（AC18 仅自动部分、AC21 见上） | 评审者按 spec 另写脚本，不复用项目测试；82 项断言全部通过 | `verify_ac.py`、`verify_ac.log` |
| 样例与规则文件逐字核对 | R03 | 17 个样例与 spec 原文一致；两个规则文件与 design 第 4 节原文一致；spec 的规则与 AC 自计划提交以来没有改动 | 本文“复核命令” |
| 生成器的对抗性验证 | R04, R05, R09, R10, R26, R29 | 27 项全部通过：400 个随机正规式在 369 个串上与 Python `re` 一致；最小 DFA 的状态数等于独立填表法求出的等价类数；一个 LR(1) 但非 LALR(1) 的文法能生成，证明确实是规范 LR(1)；归约-归约冲突被拒绝；不同哈希种子和 Python 3.14 下五个生成文件逐字节相同；14 种规则文件错误都被拒绝且不留输出 | `adversarial_generator.py`、`.log` |
| mini-C 的对抗性验证 | R06–R08, R12–R19, R24, R25 | 52 项全部通过：23 个边界程序的运行结果、17 个错误程序的诊断位置与代码，以及 read、退出码、记号文本格式、旧产物清理等 | `adversarial_minic.py`、`.log` |
| 随机程序差分 | R17, R18, R19 | 两轮共 180 个随机 mini-C 程序（含遮蔽、嵌套循环、回绕、截断除法、read），`-O0` 和 `-O2` 的输出与评审者写的参考解释器逐行一致，共 699 行输出 | 同上 |
| 变异测试 | 测试有效性 | 在仓库副本中逐个植入 20 个缺陷，项目自带测试发现了全部 20 个，每个都有至少一处真实的断言失败 | `mutation.py`、`mutation.log` |
| 源码通读 | 全部 | `ccgen/`、`minic/` 全部 21 个源文件逐行阅读；算法与 design 第 5、6、8 节一致，实施中的偏离都记在 design 第 14 节且理由成立 | 本文“发现” |

## 发现

按建议处理的先后排列。都不影响已勾选 AC 的结论。

| 编号 | 级别 | 现象 | 建议 |
|---|---|---|---|
| CR01 | 建议答辩前处理 | `ast.html` 打开时看不到根结点。演示程序的树宽约 3500 像素，根 `Program` 在正中，页面初始停在最左边，要横向滚动才能找到根。结点不重叠、连线有字段名，这些都符合 AC18 | 打开时把滚动位置对准根结点，并加“适应宽度 / 原始大小”切换。只涉及 `minic/astviz.py` 的内嵌脚本 |
| CR02 | 建议处理 | 带 UTF-8 BOM 的源文件在 1:1 报 L001。Windows 记事本默认可能写入 BOM，组员在 Windows 上写演示程序时会遇到 | 驱动和独立 `lexer.py` 读文件时用 `utf-8-sig`。spec 没有规定这一点，如采纳需在 R08 旁补一条规则 |
| CR03 | 提示 | 第一轮审查材料 53 个文件未入库；本地提交未推送 | 由用户决定是否入库和推送。它们是代码评审过程的直接证据 |
| CR04 | 提示 | T1-01 至 T1-06 六个提交集中在 2026-11-10 23:16–23:35 的 20 分钟内 | 历史无法也不应改写。后续修改建议走分支和 PR，留下评审记录 |
| CR05 | 提示 | 构造报告中“丢弃”“固定串”两列显示 `True`/`False`，状态数一节的行名是 `nfa_states` 等英文键名；Thompson 构造对每个连接多包一层状态，`(a\|b)*abb` 得到 21 个 NFA 状态，多于教材图示的 11 个 | 纯展示问题。答辩若被问到 NFA 状态数，说明是构造时多加了 ε 过渡，不影响 DFA（5 个）和最小 DFA（4 个） |

实施中对 design 的偏离，评审认为都合理：`fixed` 改为按语义判定；`astviz.py` 提前到 T1-03 实现；报告把 ACTION 与 GOTO 分成两节凑足九节；与固定产物重名时后端主名追加 `.program`；`ast.html` 内嵌无依赖的重排脚本。

## 已作决定与约束

| 决定 | 依据/日期 | 后续影响 |
|---|---|---|
| spec H09 补记 `-2147483648 / -1` 为不作规定的行为 | 评审，2026-11-11；实现方在 design 第 14 节请求评审者核对 | 不新增运行时检查；README 的限制说明与之一致 |
| spec H11 改为已验证 | 2026-11-11 实测 | 无 |
| 项目配置记录 `python3` 因 shell 而异（3.11.15 或 3.14.6） | 2026-11-11 实测 | 要固定版本时用 `/Users/aqua_night/.local/bin/python3.11` |

## 环境与操作入口

复核命令，均已于 2026-11-11 实际运行：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 -m unittest discover -s tests 2>&1 | tail -3
```

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 doc/review/claude-acceptance/verify_ac.py "$(mktemp -d)/ac" | tail -1
```

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler" && python3 doc/review/claude-acceptance/adversarial_generator.py "$(mktemp -d)/gen" | grep -c PASS
```

第一条末行应为 `OK`；第二条应输出“合计 82 项断言，失败 0 项”；第三条应输出 27。脚本的第一个参数是工作目录，会被清空重建，这里用 `mktemp -d` 在系统临时目录下新建，不要指向仓库内。`adversarial_minic.py` 另接受随机种子和程序个数两个参数；`adversarial_generator.py` 的确定性检查需要 `/Users/aqua_night/.local/bin/python3.14` 存在。

## 未完成事项与已知问题

- AC18 的人工目视未完成，checklist 中保持未勾选。评审者只看了 Quick Look 渲染出的静态图，不能代替用户在浏览器中的检查。
- 答辩用机的 clang 版本（spec H10）未验证。
- 没有在 Windows、Linux 上运行过。
- CR01、CR02 未处理。

## 下一步与文件索引

1. 用户按 checklist 的 AC18 手工命令在浏览器中打开 `ast.html` 检查并决定是否勾选。
2. 用户决定是否处理 CR01、CR02。处理时先由 Claude 更新四文件，再交 Codex 实现。
3. 用户决定是否把第一轮审查材料入库、是否推送。

相关入口：[README](../../README.md)、[项目配置](../project-config.md)、[spec](../task1/spec.md)、[design](../task1/design.md)、[tasks](../task1/tasks.md)、[checklist](../task1/checklist.md)、[修复汇总](../review/fix-summary.md)、[评审证据](../review/claude-acceptance/)。
