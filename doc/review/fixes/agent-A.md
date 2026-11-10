# A：驱动输入保护、产物路径与后端参数修复

日期：2026-11-11。修复基线由主对话确认：`main / 2fa29b29440069881b91735e13c9a870450ef918`。本报告记录 A 的定向检查，不代替 D 的最终全量回归或 AC18 用户人工目视验收。

## 修改范围

- `minic/__main__.py`：统一计划与预检、清理新旧产物名、保留 CR 的 UTF-8 读取、复用生成解析器的无递归 JSON 接口。
- `minic/backend.py`：统一后端产物命名函数、clang 文件参数显式 `./` 前缀。
- 新增 `tests/test_review_paths.py`：10 个标准库 unittest 方法，均带 AC 编号。
- 本报告与 `doc/review/fixes/evidence/A/` 新证据。

没有修改其他代理独占代码、旧测试、规则、fixtures、examples、spec/AC、旧审查证据或 Git 历史；没有添加辅助模块或第三方依赖。设计调整由主对话先记录到 `doc/task1/design.md` 后实施。

## 根因、处理与证据

| 问题 | 根因与最终行为 | 失败证据 | 通过证据 |
|---|---|---|---|
| RV01；AC06/18/20 | 原驱动按文件名清理，不检查源文件/所选分析器身份。现在在加载、mkdir、删除、写入前统一检查所有阶段输出及历史清理候选：`resolve()` 规范化路径及符号链接，`samefile()` 比较现有文件身份，覆盖硬链接、目录别名、文件/父目录不可共存。冲突退出 2，打印“路径冲突”，不修改旧内容。实际阶段输出相互别名也拒绝。 | `before.log`：无后缀源、目录/源 symlink、hardlink、所选 lexer/parser、产物别名均未按合同拒绝；源或分析器真实被删。`before-parent.log`：父子路径冲突仍退出 0 且改写旧 tokens.txt。 | `after-final.log`：输入/分析器及旧文件字节不变，别名和父子路径拒绝通过。 |
| RV04；AC14/15/18 | 后端可执行名直接取源 stem，与固定 `tokens.*`/`ast.*` 冲突。现在对整个产物名字集合规划，按 casefold 保留固定阶段名，碰撞时后端主名确定性追加 `.program`，不根据已有文件动态选名。六种固定阶段名均完整编译运行、保留 10 项产物；JSON 可解析，HTML/DOT/AST文本/记号文本各有语义断言。正常 demo 名不变。旧版本原 stem 的后端名仍纳入预检及清理。 | `before.log`：`tokens.json.mc`、`ast.json.mc` 编译运行成功却输出 Mach-O 前缀，JSON 覆盖断言失败；其他固定名亦缺少独立产物。 | `after-final.log`：六保留名完整编译运行输出 `1\n`，数据和文件集合通过；词法失败同时清除新旧两套后端旧产物，保留无关文件。 |
| RV05；AC14/15/17 | `-demo.ll` 裸传 clang 被当选项。现在全部输入/输出文件参数带 `./`，仍在输出目录 cwd 调用，显式 clang 相对工具路径仍相对调用者解析。 | `before.log`：`-demo.mc` 退出 3，clang 报 no input files。 | `after-final.log`：`-demo` 与 `@demo` 真实 clang 编译运行正确，两输出目录的记号、AST、原始/优化 IR、汇编文本逐字节相同。D 同步原 `test_ac17_clang_commands` 精确命令断言。 |
| RV06；AC13/20 | `Path.read_text` 通用换行读取把 CR 改成 LF。驱动现在以 `source.open(encoding='utf-8', newline='')` 读原字符序列。 | `before.log`：`int x;\rwrite(y);` CLI 诊断是 `2:7`，API 契约期望 `1:14`。 | `after-final.log`：诊断 `1:14`，tokens/errors 与直接 tokenize 原字符串一致。B 负责独立 lexer 对应读取与其回归。 |
| RV07；AC10/14/18/20 | 驱动调用标准库递归 AST JSON 写盘。改为 `parser.json_text(tree)`，复用 B 的显式栈实现；未提高 recursionlimit，未吞异常。后续语义/IR/可视化显式栈由 C 负责。 | C 在驱动修改前保存 `evidence/C/before.log` 的 1000 项长表达式入口 traceback；B 另有独立 parser 失败证据。 | A `existing-targeted.log` 的 AC20 独立/集成字节一致通过；C 回传 `evidence/C/after.log`：9 tests 全通过、退出 0，包含 1000 项表达式驱动到 IR、与独立 parser AST 字节一致、clang -O0 运行输出 1000，以及 550 层 if/block 输出 8/7；A 不把这些记为自己运行的检查。 |

修复过程中发现并关闭一个新增边界：在本机大小写不敏感文件系统上，`AST.JSON.mc` 第一次编译通过，第二次被历史清理名 `AST.JSON` 与实际阶段 `ast.json` 的同一文件身份误拒绝。先增加重复编译/再次词法失败回归，保存 `before-case-variant.log`（退出 1），再将“实际阶段输出必须互不别名”和“历史候选必须保护输入”分开预检。历史候选允许与当前产物表示同一个目录项，清理会在删除后跳过已不存在的别名；所有实际阶段输出仍完整互斥检查。最终 `after-final.log` 通过该用例及原产物硬链接拒绝用例。主对话已同步设计。

## 实测命令与退出码

工作目录均为 `/Users/aqua_night/codex_project/编译原理/minic-compiler`；shell zsh；Python 3.11.15；真实后端使用本机 Apple clang 21。所有测试源、生成分析器、缓存和编译产物放 TemporaryDirectory，没有使用仓库 build/out。外层证据采集脚本退出 0 仅代表日志保存成功；下面列出的退出码是日志记录的实际 unittest 子进程状态。

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_review_paths.py -v
```

- `before.log`：初版 8 tests，17 个子用例失败，unittest 退出 1；失败由目标缺陷触发，无导入/环境错误。
- `before-parent.log`：追加父子路径用例 1 test / 1 failure，退出 1。
- `after.log`：初步修复 9 tests 全通过，退出 0；保留该中间记录，不覆盖。
- `before-case-variant.log`：本轮新增大小写重复编译用例 1 test / 1 failure，退出 1。
- **`after-final.log`：最终 10 tests 全通过，0 失败、0 错误、0 跳过，退出 0。**

两个追加用例可独立复核，当前代码预期均通过：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_review_paths.py -k parent_conflict -v
```

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_review_paths.py -k case_variant -v
```

旧针对性测试（`existing-targeted.log`）分别为 5、2、1 个测试通过，三条命令各退出 0：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_minic_frontend.py -v
```

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_standalone.py -v
```

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_irgen.py -v
```

## 依赖与交接

A 业务及新增测试已冻结并通知主对话/D。依赖 B 保留 `parser.json_text(value) -> str` 接口与原缩进/末尾 LF 字节契约，B 已完成；C 负责 RV07 后续深树流程；D 负责旧后端测试同步、最终全量与演示，A 未重复全量。未改变 `INT_MIN / -1` 合同，不声明其他系统或 clang 15 已验证。预检保护本次调用开始时的路径身份，不声称能抵御并发进程在检查和写入之间恶意替换文件的竞态。AC18 用户人工验收仍未完成。
