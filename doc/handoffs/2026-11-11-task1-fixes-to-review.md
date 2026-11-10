# task1 RV01～RV11 修复交接

日期：2026-11-11（Asia/Taipei）。工作目录 `/Users/aqua_night/codex_project/编译原理/minic-compiler`。本轮范围与授权：修复审查汇总的 11 项问题，四个 Astra / High 子对话并行，主对话协调、记录、集成和本地提交。未包含作业程序设计文档、PPT、远端协作材料及除法溢出新语义。

## 当前结果

RV01～RV11 全部已复现、修复并有回归证据。入口为 [fix-summary](../review/fix-summary.md)，四个子对话记录在 [A](../review/fixes/agent-A.md)、[B](../review/fixes/agent-B.md)、[C](../review/fixes/agent-C.md)、[D](../review/fixes/agent-D.md)。创建参数实际指定 `model="gpt-6-astra"`、`reasoning_effort="high"`，没有再次分派。

- 路径规划在清理前保护源文件和所选分析器；阶段产物互不覆盖。与固定名冲突的后端主名追加 `.program`，新旧产物清理均保留。另修复大小写不敏感文件系统上的重复编译误拒绝。
- 集成加载直接使用当前生成源码；私有记号标记避免合法 AST 字段碰撞；两个入口保留源 CR/LF；文本记号转义控制字符，JSON 保持原值。
- 独立 parser 的 `json_text(value)` 与驱动共享；JSON、语义、IR、文本/布局/HTML/DOT 均去除依赖 AST 深度的 Python 递归。保留原左右顺序、作用域和控制流，不提高业务进程递归上限。
- AST HTML 内嵌无依赖字形测量和重排，完整长标识符可读；DFA 空格列可辨识；假 clang 启动器支持含空格/单引号的解释器路径。

设计调整均先记录于 [design §14](../task1/design.md) 后实施。原 spec、语言规则、样例与历史验收预期不变；tasks/checklist 只追加本轮事实，AC18 不代勾。README 同步了路径冲突、消歧命名及重新生成分析器的运行说明。

## 本轮验收

Python 3.11.15（`/Users/aqua_night/.local/bin/python3.11`）、macOS 26.5.1 arm64、Apple clang 21.0.0。D 独立执行：相关 14 组 AC 筛选通过；新增 **26 tests** 通过；全量 **67 tests / 21.386s，0 失败、0 错误、0 跳过，退出 0**。真实 clang 后端未跳过。证据见 [D/full-regression.json](../review/fixes/evidence/D/full-regression.json)。

演示显式设置实际 `MINIC_PYTHON`，两个输出目录放带空格临时路径，执行 `echo 5 | bash scripts/demo.sh`，退出 0，最后三行 `15`、`120`、`1`；五个生成文件、十个编译产物均非空。完整环境与实际命令见 [demo.json](../review/fixes/evidence/D/demo.json)。所有测试源、分析器、缓存、编译产物均在临时目录，没有借用仓库 build/out。

RV08 的 Safari 26.5 修前/修后真实字形测量和目视记录见 [browser-observations](../review/fixes/evidence/D/browser-observations.txt)。长标识符 6 结点与 demo 46 结点的文字越框/节点或字段文字重叠/视口裁切均为 0；原始图自包含，本地文件打开，没有断网，不等于用户 AC18 验收。

源码/测试在最终检查前后 60 文件摘要一致，之后只做文档记录、暂存核对和提交；没有业务变更使验收失效。运行复核命令：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -v
```

## Git 与下一步

开始为 `main / 2fa29b29440069881b91735e13c9a870450ef918`，跟踪工作区和暂存区干净。原 `doc/review/` 审查材料及 `2026-11-10-task1-review-to-fix.md` 是已有未跟踪文件，全部保留，未混入本轮提交。本轮完整集成批次说明为 `T1-RV 修复 RV01-RV11 并补充反例回归`，本交接随批次本地提交；用下列命令读取实际提交标识：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
git log -1 --format='%H %s' --grep='^T1-RV 修复 RV01-RV11 并补充反例回归$'
git status --short --branch
```

没有推送、改写历史或修改 Git 配置。接手前仍应先核对实际 HEAD/工作区，不能把本快照当作未来状态。

下一步由用户完成 AC18 离线人工目视；既定计划维护者处理历史“未实施”状态及 `INT_MIN / -1` 合同口径。未验证其他操作系统/浏览器、最低 clang 15、答辩机器或 Python 3.14 的本次修复，深树测试也不是无限规模保证。没有范围内已知未修复 RV。
