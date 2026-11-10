# B：生成分析器与前端加载修复

日期：2026-11-11。修复基线为 `main` / `2fa29b29440069881b91735e13c9a870450ef918`；实际解释器 `/Users/aqua_night/.local/bin/python3.11`，Python 3.11.15。所有生成物、规则副本、源程序、缓存、编译产物都在 `TemporaryDirectory`。未更改原规则、fixtures、examples、既有测试、Git 配置或历史，未写 `build/`、`out/`。开始前已读指定计划、交接和审查材料，实施方案先交主对话写入 design §14，再修改业务。

B 范围已完成：RV02、RV03、RV06 的独立 lexer 部分、RV09，以及 RV07 的独立 parser JSON 序列化。RV06 驱动由 A 负责；RV07 驱动复用接口由 A 负责，语义/IR/展示遍历与 1000 项 mini-C 端到端用例由 C 负责；本报告不以 B 的局部结果代替那些验证。

## 修改文件与接口

| 文件 | 修改 |
|---|---|
| `minic/frontend.py` | 保留 importlib module/spec 元信息，直接读取当前源码 bytes，`compile` 后 `exec`；不读写 `.pyc` |
| `ccgen/templates/lexer_template.py` | UTF-8 读取显式 `newline=''`；文本属性转义反斜杠及不可打印字符 |
| `ccgen/templates/parser_template.py` | 值栈私有 `_Token` 标记；`json_text(value) -> str` 改为显式栈序列化 |
| `tests/test_review_generated.py` | 6 个含 AC 编号的回归方法，涵盖五项发现及 JSON 格式兼容控制组 |
| `doc/review/fixes/evidence/B/` | 新增修前、修后、最终增强回归及相关既有测试原始证据与采集脚本 |

不新增业务辅助模块。生成物仍只需 `lexer.py`、`parser.py` 两份 Python 源文件，无 `minic`/`ccgen` import 或第三个运行时文件。回归实际把两份文件复制到仓库外目录，用 `python -I -B` 运行。外部 `tokens` 和 AST 仍是普通 dict/list/string，不泄漏 `_Token` 子类，也不修改输入记号对象。

## 根因、修复及断言

| 发现 / AC | 根因与改法 | 修前实际失败 | 修后覆盖 |
|---|---|---|---|
| RV02 / AC20 | 普通 import 缓存按整数秒 mtime + size 复用字节码；直接编译当前源码绕过该缓存 | lexer 用旧 `X x` 拒绝 `y`；parser 返回旧 `Past`，当前源码独立 CLI 返回 `Next` | 同目录两次真正生成等长 lexer/parser 源码；`py_compile` 显式建立 timestamp pyc，`os.utime` 固定同整数秒、不同纳秒；校验 pyc header、源码长度和缓存未变；普通 load 控制组确实仍读旧，而生产 frontend.load 与当前独立 CLI 一致 |
| RV03 / AC02、AC20 | `kind`、`lexeme` 键存在被当成 token 身份；shift 入栈时包装私有 `_Token`，只按类型识别 | 根、字段、列表、默认动作孩子、传递五变体丢失 Node，断言失败；CLI 退出 0 暴露静默数据损坏 | 五变体均保留合法字段，另保留 token 的直接传递和默认叶结点；API/CLI 相同；遍历断言结果类型为原生容器/标量，输入 tokens 不变 |
| RV06 / AC05、AC20（驱动交叉 AC06） | `Path.read_text` 通用换行改写；改用 UTF-8 `open(..., newline='')` | CR 被识别成 LF，CRLF 少一个记号，位置变化 | CR、CRLF、LF 源文件原始字节与 tokenize API 一致；CR 只增列，LF 才增行；独立 CLI 与 API 记号完整相同 |
| RV09 / AC05、AC20 | 属性直接插入 tab 表；新增文本专用转义 | 单记号输出含真实 LF、tab 等，精确输出断言失败 | 一个物理行、四个 tab 列；`\\`、`\n`、`\r`、`\t`、`\b`、`\f`、`\v` 可辨认；其他不可打印字符用 `\xNN` / `\uNNNN` / `\UNNNNNNNN`；包含 NUL、DEL、NEL、Unicode 行分隔符；中文保持可读，JSON attr/lexeme 原字符不变 |
| RV07 / AC02、AC10、AC20 | 标准库缩进 JSON 的容器遍历递归耗尽；显式栈处理 dict/list，标量借 json.dumps | calc 的 495 项加法独立解析器退出 1，stderr 为未捕获 `RecursionError` | 同例默认解释器限制下成功写 JSON；浅层含空容器、嵌套、Unicode/控制符、标量与 `json.dumps(ensure_ascii=False, indent=2)+'\n'` 精确一致；深树与 API 输出逐字节相同，独立标准库解码另验证 JSON 语法及完整叶序 |

`parser.json_text` 面向公开 AST 数据：字符串键的 dict、list 及 JSON 标量；保留字段插入顺序、两空格缩进与末尾 LF。显式栈带活动容器身份集合，避免循环结构无限处理。没有提高任何业务进程的递归上限。为避免测试判据自身在深 JSON 解码处受递归限制，**仅独立测试 reader 子进程**调用 `sys.setrecursionlimit(10000)` 后使用标准库 `json.loads`，再迭代验证叶子还原为原输入；被测 `parser.py` 依旧使用默认上限。

## 失败与通过证据

| 证据 | 实际结果 |
|---|---|
| [before.json](evidence/B/before.json) | 修改业务前：6 个测试方法，5 个方法触发共 11 个失败条目，0 error、0 skip，退出 1；JSON 浅层控制组通过；记录 35 条真实子进程命令及 stdout/stderr/退出码 |
| [after.json](evidence/B/after.json) | 业务修改后同组：6 tests / 0.918s，0 fail/error/skip，退出 0；记录 36 条子进程 |
| [final.json](evidence/B/final.json) | 增强独立深 JSON 解码判据后：6 tests / 0.910s，0 fail/error/skip，退出 0；记录 37 条子进程 |
| [related.json](evidence/B/related.json) | 相关既有测试共 17 项，全部通过、无跳过；五条 unittest 命令分别退出 0 |

所有 JSON 证据保存实际命令、cwd、解释器版本与完整 stdout/stderr，未覆盖原审查探针和历史日志。修前失败不是“预期失败就记为成功”：采集命令确实退出 1，并保留目标失败断言。`run_targeted.py` 拒绝覆盖已存在的同名证据。

已实际执行的修前、修后与最终采集命令如下，均在项目根目录、zsh；前两条是当时快照，当前复核应使用后文普通 unittest 命令，不应覆盖历史证据：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B doc/review/fixes/evidence/B/run_targeted.py before
```

退出 1（业务修改前）。

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B doc/review/fixes/evidence/B/run_targeted.py after
```

退出 0（业务修改后）。

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B doc/review/fixes/evidence/B/run_targeted.py final
```

退出 0（只增强测试 reader 后，业务未再改变）。

当前 B 回归可独立复核：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_review_generated.py -v
```

相关既有测试实际使用同一 Python 3.11.15，以 `sys.executable` 解析到的实际解释器路径执行；完整 argv 在 related.json。以下等价入口便于复制，各条期望且实测退出码均为 0：

```bash
cd "/Users/aqua_night/codex_project/编译原理/minic-compiler"
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_parsegen.py -v
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_lexer_minic.py -v
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_standalone.py -v
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_ccgen_cli.py -v
PYTHONDONTWRITEBYTECODE=1 /Users/aqua_night/.local/bin/python3.11 -B -m unittest discover -s tests -p test_minic_frontend.py -v
```

对应数量分别为 3、2、2、5、5，合计 17。没有运行全量或真实 clang；统一最终验证交 D。这里只支持上述输入及环境的实际结果，不声称任意规模 AST 或其他平台都已验证。

## 协调与剩余事项

- 已通知 A 与 C：`parser.json_text(value)` 接口稳定，可直接复用；独立 lexer 的 UTF-8 原字符读取已完成。
- 已通知主对话与 D：B 业务和测试冻结，可开展统一全量。其余共享工作树变化来自对应负责人，B 未编辑他人文件。
- B 本范围无剩余已知失败。RV06 整体关闭需合并 A 的驱动位置验证；RV07 整体关闭需合并 A/C 的完整链验证和 D 的最终回归。
- AC18 人工目视仍留给用户，未代勾。未新增语言、修改 spec/AC、讨论或改变 `INT_MIN / -1`，未执行 Git add/commit/checkout/reset/stash/clean/push。
