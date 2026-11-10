# minic-compiler

编译原理期末项目：一个词法分析器与语法分析器的生成器，以及用它构成的 mini-C 编译器。

当前状态（2026-11-10）：计划已完成，业务代码尚未开始。当前任务：[task1 mini-C 编译器生成器与编译器成品](doc/task1/spec.md)。下一步：按 [tasks](doc/task1/tasks.md) 从 T1-01 开始实现。

## 项目目标

- 生成器 `ccgen`：输入词法规则（正规式）和语法规则（上下文无关文法），用 Thompson 算法、子集法、等价状态法和规范 LR(1) 方法，输出该语言的词法分析器和语法分析器。
- 编译器 `minic`：用生成的 mini-C 分析器，把源程序变成记号序列、可视化的 AST、LLVM IR，再调用 clang 得到优化后的 IR、汇编和可执行文件。

需求来自仓库外的 `../作业要求/6749484.pdf`。本仓库只负责代码成品，不含《程序设计文档》和答辩 PPT。

## 环境与启动

需要 Python 3.11 及以上，无第三方依赖；“优化与机器码”部分另需 clang 15 及以上。下面的命令是计划中的入口，代码实现后才可用，工作目录为项目根目录。

```bash
python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic
```

```bash
python3 -m minic examples/demo.mc --frontend build/minic --out out/demo --run
```

```bash
bash scripts/demo.sh
```

## 文档入口

| 内容 | 位置 |
|---|---|
| 协作规则 | [AGENTS.md](AGENTS.md)（Claude 入口为 [CLAUDE.md](CLAUDE.md)） |
| 项目配置：环境、命令、Git 策略、分工 | [doc/project-config.md](doc/project-config.md) |
| 当前任务四文件 | [spec](doc/task1/spec.md)、[design](doc/task1/design.md)、[tasks](doc/task1/tasks.md)、[checklist](doc/task1/checklist.md) |
| 最新交接 | [2026-11-10 task1 计划完成，交给实现](doc/handoffs/2026-11-10-task1-plan-to-impl.md) |
| 工作请求模板 | [doc/request-template.md](doc/request-template.md) |
| 新任务的空白母版 | `doc/task-template/`、`doc/templates/` |

## 验证入口

计划结构检查（已可用）：

```bash
python3 scripts/check_plan.py doc/task1
```

全部测试（计划中，代码实现后可用）：

```bash
python3 -m unittest discover -s tests -v
```

每个 AC 的单独复核命令见 [checklist](doc/task1/checklist.md)。

## 已知限制

- 只支持作业要求附录中的 mini-C 文法，外加 `//` 行注释；没有函数、数组、逻辑运算和一元负号。
- 语法错误只报告第一个，不做错误恢复。
- 不检查除零等运行时错误。
- 没有 clang 时只能做到生成 LLVM IR 为止。

## 目录

```text
minic-compiler/
├── AGENTS.md / CLAUDE.md     # 协作规则与入口
├── doc/                      # 项目配置、任务四文件、交接、模板
├── scripts/check_plan.py     # 计划结构检查
├── ccgen/                    # 生成器（待实现）
├── minic/                    # mini-C 编译器驱动（待实现）
├── rules/                    # minic.lex、minic.grammar（待实现）
├── examples/                 # 演示程序（待实现）
└── tests/                    # 测试与样例（待实现）
```
