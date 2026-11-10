# minic-compiler

编译原理期末项目：语言无关的词法/规范 LR(1) 分析器生成器，以及使用生成物的 mini-C 编译器。仅依赖 Python 标准库，后端调用 clang。

当前状态（2026-11-10）：T1-01 至 T1-06 编码与自动检查完成。Python 3.11.15 和 3.14.6 下均为 **41 个测试通过、0 失败、0 错误、0 跳过**；最终演示退出码 0。实施 AC 为 **21/22**，AC18 的自动检查通过，人工离线目视检查留给用户，未勾选。

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

- [最新交接：实现完成，交给评审](doc/handoffs/2026-11-10-task1-impl-to-review.md)
- [协作约定](AGENTS.md)与[项目配置](doc/project-config.md)
- [spec](doc/task1/spec.md)、[design](doc/task1/design.md)、[tasks](doc/task1/tasks.md)、[checklist](doc/task1/checklist.md)

本轮不改 spec 的规则或 AC；计划文档的原始“未实施”状态、项目配置的历史环境信息由计划维护者接手更新。当前事实以本 README、tasks/checklist 的实测记录及最新交接为准。

## 限制

只支持约定的 mini-C 文法与 `//` 注释；没有函数、数组、逻辑运算或一元负号。语法错误只报告第一个，词法和语义错误收集后一起报告。不检查除零、除法溢出或无效 read 输入等运行时错误；LLVM `sdiv` 对 `INT_MIN / -1` 不定义结果。未验证其他操作系统或答辩机器。AST 的浏览器人工检查尚未执行。

项目只交付代码成品，不包含《程序设计文档》和答辩 PPT；原始要求 `../作业要求/6749484.pdf` 保持只读。
