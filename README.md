# minic-compiler

编译原理期末项目：语言无关的词法/规范 LR(1) 分析器生成器，以及使用生成物的 mini-C 编译器。仅依赖 Python 标准库，后端调用 clang。

当前状态（2026-11-11）：T1-01 至 T1-06 已实现，RV01～RV11 已修复；T1-07 的 BOM 兼容和 AST 定位/缩放已实现。Python 3.11.15 全量 **71 个测试通过，0 失败、0 错误、0 跳过**。实施 AC 为 **24/24**：AC24 的数值实测已经评审通过，用户于同日确认 AC18 人工离线目视及两个按钮的效果。见 [checklist](doc/task1/checklist.md) 和 [人工验收交接](doc/handoffs/2026-11-11-task1-human-acceptance.md)。

## 运行

需要 Python 3.11+；优化 IR、汇编、链接和运行另需 clang 15+。不需要 pip、Graphviz、opt 或 llc。以下命令在项目根目录执行。

一条命令生成分析器、编译并运行：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
echo 5 | bash scripts/demo.sh
```

先输出产物路径，最后三行是 `15`、`120`、`1`。测试用 `MINIC_BUILD_DIR`、`MINIC_OUT_DIR` 指向临时目录；默认演示输出到 `build/minic/` 和 `out/demo/`。可用 `MINIC_PYTHON=python3.11` 选择解释器。

分别执行：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic
python3 -m minic examples/demo.mc --frontend build/minic --out out/demo -O2 --run
```

没有 clang 时，仍可生成前端和 IR：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic
python3 -m minic examples/demo.mc --frontend build/minic --out out/demo --stop-after ir
```

`--stop-after` 支持 `tokens`、`ast`、`ir`；`-O` 支持 0–3（默认 2）；`--clang` 可指定后端路径。`--run` 标准输入输出直接交给程序，编译过程信息和诊断写入标准错误。退出码：0 成功、1 源程序错误、2 用法或规则错误、3 后端错误。

编译前会统一检查输入源文件、所选 `lexer.py` / `parser.py` 与阶段产物的路径关系；冲突时在清理或写入前退出 2，保留原文件。源文件主名与固定阶段产物重名时，后端主名自动追加 `.program`：例如 `tokens.json.mc` 生成 `tokens.json.program.ll`、`.opt.ll`、`.s` 和可执行文件 `tokens.json.program`，原 `tokens.json` 仍是记号数据。普通文件名和旧产物清理方式保持原用法。

更新本项目后，请重新运行 `ccgen` 更新已有独立分析器。集成驱动直接加载当前生成源码；独立与集成入口均忽略文件开头的一个 UTF-8 BOM，保留 CR/LF，仅 LF 增加行号；源程序中间的非法 BOM 仍报 L001。记号文本表转义控制字符和反斜杠，JSON 保留原词素。

AST 页面新增“适应宽度 / 原始大小”按钮，默认原始大小并定位到根结点，字体重排后沿用当前模式。实现保持静态 SVG、自包含和确定性；三种状态的浏览器实测数值见 checklist 的 AC24。

## 产物与算法

| 位置 | 内容 |
|---|---|
| `build/minic/lexer.py`、`parser.py` | 可脱离仓库、使用 `python3 -I` 运行的独立分析器 |
| `build/minic/lexer_tables.json`、`parser_tables.json` | 词法表、规范 LR(1) 表及冲突记录 |
| `build/minic/report.html` | 九节离线构造报告 |
| `out/demo/tokens.txt`、`tokens.json` | 二元式记号表与 JSON（含全部词法错误） |
| `out/demo/ast.json`、`ast.txt`、`ast.html`、`ast.dot` | AST 数据、文本树、离线 SVG、DOT |
| `out/demo/demo.ll`、`demo.opt.ll`、`demo.s`、`demo` | 原始 IR、优化 IR、汇编、可执行文件 |

词法构造依次使用 Thompson、子集法、等价状态划分；mini-C 实测 NFA 177、DFA 48、最小 DFA 44 个状态。语法构造为规范 LR(1)，38 条产生式（含增广产生式）、264 个状态；只有两处 `else` 冲突，按规则文件显式声明取移进。规则和样例与计划中的原文逐字节核对。

## 测试与证据

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
python3 -m unittest discover -s tests -v
```

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
python3 -m unittest discover -s tests -k ac03 -v
```

所有测试方法名含 AC 编号；测试在临时目录生成分析器和编译产物，不读写 `build/`、`out/`。没有 clang 时相关测试明确跳过，跳过不代表验收通过。全量结果、逐项命令和退出码见 [checklist](doc/task1/checklist.md) 与 [证据目录](doc/task1/evidence/)。本机默认 `python3` 为 3.14.6；3.11 的精确环境与命令也已记录。

## 文档与接手

- [最新交接：用户人工验收完成](doc/handoffs/2026-11-11-task1-human-acceptance.md)；[T1-07 评审结论](doc/handoffs/2026-11-11-task1-t107-review.md)；评审对象是 [T1-07 实现交接](doc/handoffs/2026-11-11-task1-t107-impl-to-review.md)，更早的依据是[验收评审结论](doc/handoffs/2026-11-11-task1-acceptance-review.md)；上一份为 [RV01～RV11 修复与验收](doc/handoffs/2026-11-11-task1-fixes-to-review.md)
- [协作约定](AGENTS.md)与[项目配置](doc/project-config.md)
- [spec](doc/task1/spec.md)、[design](doc/task1/design.md)、[tasks](doc/task1/tasks.md)、[checklist](doc/task1/checklist.md)

本轮未改 spec 的规则或 AC；实施与验证限制记录在 design 第 14 节。spec 和项目配置中计划时点的状态保留为历史记录，当前进度以 tasks、checklist 和最新交接为准。T1-07 评审时已在 Python 3.14.6 下复跑全量 71 个测试并通过。

## 限制

只支持约定的 mini-C 文法与 `//` 注释；没有函数、数组、逻辑运算或一元负号。语法错误只报告第一个，词法和语义错误收集后一起报告。不检查除零、除法溢出或无效 read 输入等运行时错误；LLVM `sdiv` 对 `INT_MIN / -1` 不定义结果。未验证其他操作系统或答辩机器。AST 的用户人工离线检查已通过；用户未提供浏览器名称与版本。

项目只交付代码成品，不包含《程序设计文档》和答辩 PPT；原始要求 `../作业要求/6749484.pdf` 保持只读。
