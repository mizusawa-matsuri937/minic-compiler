# 交接：T1-07 实现与自动检查 → 评审及补齐浏览器验收

日期：2026-11-11。本文件是本轮工作快照，接手时核对实际状态。

## 范围和 Git 状态

- 只实施 T1-07（CR01、CR02），不修改 spec 的规则或 AC、规则文件、样例和已有测试。
- 工作目录：`/Users/aqua_night/codex_project/编译原理/minic-compiler`；分支 `main`，本轮基线 `e05c7ee`。
- 本文件随说明以 `T1-07 实现` 开头的本地提交入库。提交完成后用 `git log -1 --format=%H --grep="^T1-07 实现"` 读取准确哈希；不推送、不改写历史、不修改 Git 配置。
- 原有 53 个未跟踪文件保持未跟踪，核对内容 SHA-256 一致；没有用 `git add .` 纳入旧审查材料。

## 实现

| 文件 | 变化 |
|---|---|
| `ccgen/templates/lexer_template.py` | 仅命令行入口读取编码改为 `utf-8-sig`，保留 `newline=''`，扫描算法不变 |
| `minic/__main__.py` | 同步一处文件读取编码 |
| `minic/astviz.py` | 页面工具栏与内嵌脚本：默认原始大小、根定位；适应宽度与原始大小切换；用 `aria-pressed` 标识；每次字体重排后沿用当前模式 |
| `tests/test_review_cr.py` | 新增 3 个 AC23 测试和 1 个 AC24 结构测试；BOM 输入由 `write_bytes` 在临时目录写出 |

只使用 Python 3.11 标准库；静态 SVG 和原有坐标/布局算法未改。已有独立分析器需要重新运行 `ccgen` 才能获得新入口。

## 实测与证据

环境：macOS 26.5.1 arm64、`/Users/aqua_night/.local/bin/python3.11`（3.11.15）、Apple clang 21.0.0，shell zsh。

| 检查 | 实际结果 | 证据 |
|---|---|---|
| 修前复现 | 新增 4 tests，3 failures，退出 1；中间 BOM 的既有错误行为已通过 | [before.log](../task1/evidence/t107/before.log) |
| T1-07 第一条命令 | 4 tests / 0.355s，OK，退出 0，无失败/错误/跳过 | [targeted.log](../task1/evidence/t107/targeted.log)、[命令及环境](../task1/evidence/t107/targeted.json) |
| AC23 | 开头 BOM：两入口退出 0、无诊断，首记号 int/1:1，共 10 个记号，JSON 逐字节相同；中间 BOM：两入口退出 1，仅 2:1 L001；双开头 BOM：只去掉第一个，另一个 1:1 L001 | 同上及 [测试断言](../../tests/test_review_cr.py) |
| T1-07 第二条命令 | 71 tests / 25.202s，OK，退出 0，0 失败、0 错误、0 跳过 | [full-regression.json](../task1/evidence/t107/full-regression.json) |
| AC05、AC06、AC14、AC20 | 随全量回归重新确认，各自 checklist 小节已补记 | [checklist](../task1/checklist.md) |
| AC18 | 自动部分重新通过；用户人工目视未执行，未勾选 | 同上 |
| AC24 | 结构、46 结点、自包含、确定性检查通过；真实浏览器几何实测未执行，未勾选 | [browser-attempt.md](../task1/evidence/t107/browser-attempt.md) |
| AC00 与范围检查 | 结构检查、静态 SVG 比较、原文件保护检查 | [plan-check.log](../task1/evidence/t107/plan-check.log)、[scope-verification.json](../task1/evidence/t107/scope-verification.json) |

两条实际测试命令在 [tasks](../task1/tasks.md) 中可直接复制；全量命令前加 `setopt PIPE_FAIL`，避免 `tail` 掩盖 unittest 失败退出码。

## 计划调整与阻碍

没有调整 R30、R31 或 AC23、AC24 的预期。验证方面的补充已记入 design 第 14 节：全量管道启用 `PIPE_FAIL`；浏览器验证受阻，保留部分完成状态。

本机连接曾中断，恢复后重新核对了工作区和旧未跟踪文件。AC24 尝试使用 ChatGPT 内置浏览器：已设置 1280×900 视口，但打开本地 `file://` 页面被浏览器安全策略拒绝（仅允许 HTTP/HTTPS）。页面没有加载，没有取得内核版本、三状态根矩形/容器边界或 scrollWidth/clientWidth；已恢复默认视口。没有绕过该拒绝，也没有把自动结构测试或历史 Safari 记录当作本次实测。这不是用户的人工目视。

## 剩余工作

1. 评审 T1-07 代码和新增测试。完成可用浏览器中的 AC24 离线几何实测，记录浏览器版本和三状态数据；满足 spec 后再勾选 AC24 和 T1-07。
2. 用户完成 AC18 的人工离线目视；实现方不代勾。
3. 换答辩用机、其他操作系统或 Python 版本的验证均未在本轮执行。

当前实施 AC 为 22/24。README、tasks、checklist 已同步；spec 和 project-config 的旧状态文字保留为此前计划时点记录，本轮实际状态以本交接和 checklist 为准。

入口：[README](../../README.md)、[design 第 14 节](../task1/design.md)、[计划交接](2026-11-11-task1-t107-plan-to-impl.md)、[待浏览器验收的 demo 页面](../task1/evidence/t107/demo/ast.html)。
