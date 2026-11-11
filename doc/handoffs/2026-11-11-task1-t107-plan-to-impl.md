# 交接：task1 T1-07 计划完成 → 交给 Codex 实现

日期：2026-11-11。本文件是该时间点的快照，接手时核对实际状态。

## 当前范围与状态

- 本轮目标和已授权范围：用户在验收评审后选择“更新计划”。Claude 把评审发现 CR01、CR02 写进 task1 的四文件，形成阶段 T1-07；不改业务代码。
- 当前分支/提交/未提交修改：分支 `main`。本次计划更新在说明以 `T1-07 计划` 开头的提交中。本地领先 `origin/main`，尚未推送。Codex 第一轮审查留下的未入库文件仍保持原状。
- 当前任务目录与阶段：`doc/task1/`。T1-00 至 T1-06 已完成；下一项是 T1-07。
- README 与四文件是否同步：已同步。

## 已完成与证据

| 完成事项 | 相关任务/AC | 实际检查结果 | 证据位置 |
|---|---|---|---|
| spec 新增 R30、R31、AC23、AC24、H12、H13 | AC00 | `python3 scripts/check_plan.py doc/task1` 输出 31 条规则、25 项 AC、8 个阶段，“结构检查通过”，退出码 0（文档检查，AI 执行） | [checklist](../task1/checklist.md) 的 AC00 |
| design 补充读文件方式和 AST 页面的定位与缩放 | R30, R31 | 已写入 5.2、第 7 节、10.1、第 13 节，并在第 14 节登记 | [design](../task1/design.md) |
| tasks 新增 T1-07；checklist 新增 AC23、AC24 | T1-07 | 两项均为未执行、未勾选 | [tasks](../task1/tasks.md)、[checklist](../task1/checklist.md) |

## 已作决定与约束

| 决定 | 依据/日期 | 后续影响 |
|---|---|---|
| 只忽略文件开头的一个 UTF-8 BOM，用 `utf-8-sig` 读取；其他位置的 BOM 仍报 L001 | 工程默认，spec H12，2026-11-11 | 驱动与独立 `lexer.py` 的读取方式必须相同，否则 AC20、AC23 的逐字节比较会失败 |
| `ast.html` 缺省“原始大小”并把根居中，另提供“适应宽度” | 工程默认，spec H13，2026-11-11 | 容器与按钮的 id 固定为 `ast-tree`、`ast-fit`、`ast-actual`，自动测试据此断言 |
| 页面仍须自包含，静态 SVG 及其坐标不变 | R22、R29 | AC14、AC18 的既有断言不得因此放宽 |
| 不处理评审中的提示项（报告中的 `True`/`False`、NFA 状态数等） | 评审 CR05，仅为展示 | 不在 T1-07 范围内 |

## 环境与操作入口

- 项目根目录：`/Users/aqua_night/codex_project/编译原理/minic-compiler`，macOS / zsh。固定用 `/Users/aqua_night/.local/bin/python3.11`（3.11.15），因为 `python3` 在不同 shell 中可能是 3.14.6。`clang` 在 PATH 中。
- 已验证的命令：`python3 scripts/check_plan.py doc/task1`。T1-07 的检查命令在 tasks 和 checklist 中都标着“计划，未执行”。

## 未完成事项与已知问题

- T1-07 未执行，AC23、AC24 未验证。
- AC18 的用户人工目视仍未完成。
- AC05、AC06、AC14、AC18、AC20 涉及读文件或 `ast.html`，T1-07 完成后须随全量回归重新确认。
- 用户尚未人工审阅这次计划扩充。

## 下一步与文件索引

1. Codex 实现 T1-07，本地提交，填写 tasks 与 checklist 的实测结果。
2. 交回 Claude 评审。
3. 用户完成 AC18 的目视检查（此时页面已带根结点定位，顺便目视 AC24 的效果）。

给 Codex 的启动请求（可直接复制）：

```text
请阅读 AGENTS.md、doc/project-config.md、README.md、doc/handoffs/2026-11-11-task1-t107-plan-to-impl.md、
doc/handoffs/2026-11-11-task1-acceptance-review.md，以及 doc/task1/ 的四份文件。检查当前分支和工作区状态，保留已有的未跟踪文件。

本次执行：tasks.md 中的 T1-07，只做这一个阶段。

要求：
1. 按 spec 的 R30、R31 和 AC23、AC24 实现，做法见 design 5.2、第 7 节、10.1 和第 13 节。
   改动限于 ccgen/templates/lexer_template.py 的命令行入口、minic/__main__.py 的读文件一处、minic/astviz.py 的页面模板与内嵌脚本。
2. 新增测试放在 tests/test_review_cr.py，方法名含 ac23 或 ac24。AC23 的源文件用 write_bytes 在临时目录写出。
   不修改已有测试的断言、规则文件和样例；不修改 spec 的规则与 AC 预期。发现计划有问题时，在 design 第 14 节写明并告诉我。
3. 只用 Python 3.11 标准库。统一使用 /Users/aqua_night/.local/bin/python3.11。
4. 完成后运行 tasks.md 中 T1-07 的两条命令。全量回归必须没有失败、错误和跳过。
5. AC24 的浏览器实测：用真实浏览器在 1280 像素宽的窗口中打开 demo 的 ast.html，
   记录刚打开、点“适应宽度”、点“原始大小”三种状态下根结点矩形与容器的边界，以及容器的 scrollWidth 和 clientWidth；
   写明浏览器及版本，并注明这不是用户的人工目视。做不了实测就如实写未执行，AC24 不勾选。
6. 在 tasks.md 填写 T1-07 的实际结果；在 checklist.md 中只勾选实际通过的 AC，填写日期、输出摘要和退出码。
   AC18 的人工目视仍留给我，不要代勾。AC05、AC06、AC14、AC20 随全量回归重新确认后在各自小节补一句。
7. 检查通过后创建一次本地提交，提交说明以 “T1-07” 开头。不要推送，不要改写历史，不要修改 Git 配置。
8. 更新 README 中受影响的说明，并在 doc/handoffs/ 新增交接文件。

最后用中文报告：改动、AC23 和 AC24 的实测结果与证据位置、全量回归结果、提交哈希、对计划的调整和未完成事项。
```

相关入口：[README](../../README.md)、[项目配置](../project-config.md)、[spec](../task1/spec.md)、[design](../task1/design.md)、[tasks](../task1/tasks.md)、[checklist](../task1/checklist.md)、[验收评审](2026-11-11-task1-acceptance-review.md)。
