# 交接：task1 计划完成 → 交给 Codex 实现

日期：2026-11-10。本文件是该时间点的快照，接手时核对实际状态。

## 当前范围与状态

- 本轮目标和已授权范围：仅规划。由 Claude 完成 task1 四文件、项目配置、README，建立 Git 仓库并本地提交计划文件；不写业务代码。
- 当前分支/提交/未提交修改：分支 `main`。计划文件在说明以 `T1-00` 开头的提交中，哈希见 `git log --oneline`。没有远端仓库。
- 当前任务目录与阶段：`doc/task1/`。T1-00 已完成；下一项是 T1-01（词法分析器生成器）。
- README 与四文件是否同步：已同步。

## 已完成与证据

| 完成事项 | 相关任务/AC | 实际检查结果 | 证据位置 |
|---|---|---|---|
| 四文件、项目配置、README | T1-00 / AC00 | `python3 scripts/check_plan.py doc/task1` 输出“结构检查通过”，退出码 0（文档检查，AI 执行） | [checklist](../task1/checklist.md) 的 AC00 |
| 模板目录改名为 `minic-compiler`，`git init` | T1-00 | 分支 `main`，仓库本地配置了提交身份 | `git log`、`git config --local --list` |
| 环境核对 | design 第 2 节 | Python 3.11.15；Apple clang 21.0.0 可编译、优化、运行手写 IR；附录文法在规范 LR(1) 下只有 `else` 上的冲突 | [design](../task1/design.md) 第 2 节。探针脚本与 IR 样例是一次性的，不在仓库中 |

## 已作决定与约束

| 决定 | 依据/日期 | 后续影响 |
|---|---|---|
| Python 3.11+，只用标准库，测试用 `unittest` | 用户选择，2026-11-10 | 不得引入第三方包；AC21 会扫描 import |
| 中间代码为 LLVM IR 文本，优化与机器码调用 clang | 用户选择，2026-11-10 | 不做三地址代码；IR 自己拼，不用 llvmlite |
| 本任务不含文档与 PPT | 用户原话，2026-11-10 | 不要生成《程序设计文档》 |
| 规范 LR(1)；冲突须在语法规则中显式声明 | 工程默认，spec H05 | 不要换成 LL、SLR、LALR；若确有理由，先改四文件 |
| 词法规则用正规式；增加 `//` 注释 | 工程默认，spec H04、H06 | 见 design 第 4.1 节的规则文件全文 |
| 每个 tasks 阶段通过后本地提交一次 | 工程默认，见项目配置 | 提交说明以阶段编号开头；不推送 |
| 分工：Claude 规划与评审，Codex 编码与测试 | 用户指定，2026-11-10 | Codex 发现计划与实现冲突时，在 design“实施中的调整”记下并告知用户，不自行降低验收标准 |

## 环境与操作入口

- 项目根目录：`/Users/aqua_night/codex_project/编译原理/minic-compiler`，macOS / zsh，`python3` 为 3.11.15，`clang` 在 PATH 中。
- 已验证的命令只有 `python3 scripts/check_plan.py doc/task1`。tasks 与 checklist 中其余命令都标着“计划，未执行”，对应代码尚不存在。
- 不使用任何密钥或外部服务。

## 未完成事项与已知问题

- T1-01 至 T1-06 全部未执行，AC01–AC22 全部未验证。
- 用户尚未人工审阅计划（AC00 只是 AI 检查）。
- 远端仓库和 PR 流程未定，见项目配置“需要明确的问题”。
- spec 的 H10（答辩用机的 clang 版本）、H11（Python 3.11 运行）待验证，不阻塞实施。
- 本轮没有联网查阅 LLVM 语言参考手册和开源实现；IR 写法以本机 clang 实测为准。

## 下一步与文件索引

1. 用户审阅计划；如有调整，由 Claude 更新四文件后重新运行计划检查。
2. Codex 按 tasks 从 T1-01 做到 T1-06，每个阶段完成检查后本地提交，并把实际命令输出填进 tasks 和 checklist。
3. 每个阶段或全部完成后交回 Claude 评审，按评审意见迭代。

给 Codex 的启动请求（可直接复制）：

```text
请阅读 AGENTS.md、doc/project-config.md、README.md、doc/handoffs/2026-11-10-task1-plan-to-impl.md
和 doc/task1/ 的四份文件（spec、design、tasks、checklist）。
本次执行：T1-01 至 T1-06。
先核对计划与当前仓库是否一致；若发现计划有错或无法实现，先在 design 的“实施中的调整”写明并告诉我，不要自行降低验收标准。
样例文件按 spec“样例文件”“运行样例”的原文逐字符创建。测试方法名必须含对应的 AC 编号（如 test_ac03_…）。
只用 Python 3.11 标准库。每个阶段的检查通过后创建一次本地提交，提交说明以阶段编号开头；不要推送。
只把实际运行过且通过的 AC 在 checklist 中勾选，并填写日期、命令输出与退出码；依赖 clang 的测试被跳过时不得勾选。
结束时报告改动、检查结果、证据位置和未完成项，并在 doc/handoffs/ 新增交接文件。
```

相关入口：[README](../../README.md)、[项目配置](../project-config.md)、[spec](../task1/spec.md)、[design](../task1/design.md)、[tasks](../task1/tasks.md)、[checklist](../task1/checklist.md)。
