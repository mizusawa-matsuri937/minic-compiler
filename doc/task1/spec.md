# mini-C 编译器生成器与编译器成品 规格

状态：计划已完成（2026-11-10），实现未开始，除 AC00 外没有已通过的验收。设计见 [design](design.md)，阶段见 [tasks](tasks.md)，验证状态见 [checklist](checklist.md)。

## 目标

交付一个可现场演示的成品：一个与具体语言无关的生成器，读入词法规则和语法规则，输出该语言的词法分析器和语法分析器；再用它生成的 mini-C 分析器组成编译器，把 mini-C 源程序依次变成记号序列、可视化的 AST、LLVM IR，并调用 clang 得到优化后的 IR、汇编和可执行文件。

## 范围

- 包含：生成器 `ccgen`；mini-C 规则文件；编译器驱动 `minic`（词法、语法、语义检查、LLVM IR 生成、调用 clang）；各阶段产物落盘；AST 可视化与生成器构造报告；自动化测试；答辩演示程序和脚本。
- 不包含：《程序设计文档》、答辩 PPT、远端仓库与 Issues/PR 材料；三地址代码路线；LL 分析、SLR、LALR；语法错误恢复（只报首个）；以产生式形式书写的正规文法输入；自研优化和自研目标代码生成；除零等运行时错误检查；附录文法之外的语言特性（函数、数组、其他类型、逻辑运算、一元负号）。
- 约束：仅用 Python 3.11+ 标准库；作业要求与课件在仓库外，只读；后端依赖本机 `clang`（15 及以上），缺少时前端与 IR 部分仍须可用。
- 依据：下文“要求”指 `../作业要求/6749484.pdf`。§1.1、§1.2、§1.3 分别指“一、期末项目任务”的任务（1）（2）（3）；§3 指“三、答辩安排”；§4 指“四、附录：mini-C 词法和语法规则”。“用户选择”指 2026-11-10 会话中的答复，见假设表。

## 规则

- R01 [要求§1.1]：生成器以一个词法规则文件和一个语法规则文件为输入，输出该语言的词法分析器和语法分析器；生成器代码中不出现任何 mini-C 专有的记号或产生式。
- R02 [要求§1.1；工程默认]：生成的词法分析器和语法分析器各是一个可独立运行的 Python 源文件，运行时不导入 `ccgen` 或 `minic`。
- R03 [要求§4]：仓库内的 mini-C 规则文件覆盖附录的全部词法类别和 37 条产生式，产生式编号与附录一致。
- R04 [要求§1.1]：词法规则用正规式书写，支持连接、`|`、`*`、`+`、`?`、分组、字符类（含范围与取反）和转义。
- R05 [要求§1.1]：词法分析器的构造依次经过 Thompson 算法（正规式→NFA）、子集法（NFA→DFA）、等价状态法（DFA 最小化）。
- R06 [工程默认]：扫描按最长匹配；长度相同时规则文件中靠前的规则优先；标记为 `%skip` 的记号被丢弃。
- R07 [要求§1.1]：词法分析器输入源代码，输出记号序列；每个记号含种别码、种别名、属性值、行、列。只能匹配一个固定串的记号没有属性值，其余记号的属性值是其词素。
- R08 [要求§1.1]：遇到不属于任何记号的字符时报告词法错误，跳过该字符继续扫描，一次报出全部词法错误。
- R09 [要求§1.1；工程默认]：语法分析器的构造采用规范 LR(1) 方法：FIRST 集、LR(1) 项目集规范族、ACTION/GOTO 表。
- R10 [要求§4 备注(3)；工程默认]：分析表冲突只按语法规则文件中的显式声明消解；存在未声明的冲突时生成失败，并列出冲突的状态、向前看符号和相关项目。
- R11 [要求§1.1]：语法分析器输入词法分析器输出的记号序列，输出 AST；AST 结点的形状由语法规则文件中每条产生式的构造动作决定，未写动作的产生式得到以左部命名、保留全部子结点的语法树结点。
- R12 [要求§4]：mini-C 的 AST 体现附录的优先级与结合性：`*` `/` 高于 `+` `-`，同级左结合，关系运算优先级最低且不可连续；`else` 与最近的未配对 `if` 配对。
- R13 [要求§1.1；工程默认]：遇到语法错误时报告第一个错误的位置、实际记号和期望记号集合，然后停止，不输出 AST。
- R14 [工程默认]：变量先声明后使用；同一作用域内重复声明是错误；`{ }` 块以及 if、else、while 的单语句体各自构成嵌套作用域，内层声明可以遮蔽外层。
- R15 [工程默认]：整型常数大于 2147483647 是语义错误。
- R16 [要求§1.2；用户选择]：以 AST 为输入生成文本形式的 LLVM IR；每个源程序对应一个含 `main` 函数的模块；IR 由本项目代码直接拼出，不使用第三方 IR 库。
- R17 [要求§3]：IR 生成覆盖变量声明、赋值、if、if-else、while、read、write，以及四种算术运算和六种关系运算。
- R18 [工程默认]：运行语义为 32 位有符号整数；加减乘溢出时按 32 位回绕；除法向零截断；关系运算结果为 1 或 0；条件非零为真；未带初值的声明把变量置 0；`read` 从标准输入读一个十进制整数；`write` 向标准输出打印十进制整数并换行。
- R19 [要求§1.3；用户选择]：调用本机 clang，由生成的 IR 得到优化后的 IR、汇编文件和可执行文件；可执行文件的行为符合 R18，且不随优化级别改变。
- R20 [工程默认]：找不到 clang 或 clang 执行失败时，记号、AST、IR 产物照常保留，命令报告后端错误并以专用退出码结束。
- R21 [要求§1.1]：编译命令把每个阶段的结果保存成文件：记号（文本和 JSON）、AST（JSON、缩进文本、可视化 HTML、DOT）、IR、优化后的 IR、汇编、可执行文件。
- R22 [要求§1.1]：AST 可视化是单个自包含的 HTML 文件，不引用任何外部资源，离线用浏览器打开即显示树形图，每个 AST 结点对应图中一个结点。
- R23 [要求§3；工程默认]：生成器另外输出一份自包含的 HTML 构造报告，内容为：各记号的正规式，NFA、DFA、最小 DFA 的状态数，最小 DFA 转换表，带编号的产生式，各非终结符的 FIRST 集，LR(1) 项目集数量，ACTION/GOTO 表，冲突及其消解方式。
- R24 [工程默认]：源程序诊断统一写到标准错误，格式为 `路径:行:列: 类别[代码]: 说明`，行列从 1 起计。代码固定为：L001 非法字符，P001 语法错误，S001 使用未声明的变量，S002 重复声明，S003 整型常数越界。
- R25 [工程默认]：退出码：0 成功；1 源程序有错；2 命令用法或规则文件有错；3 后端工具出错。出错阶段自身的产物照常保存，其后各阶段的产物不生成。
- R26 [工程默认]：规则文件有错时，生成器报告文件名和行号并失败，不写出任何文件。错误包括：正规式语法错误、记号可匹配空串、语法规则使用了词法规则未定义的终结符、构造动作语法错误或引用越界。
- R27 [用户选择；工程默认]：全部代码只依赖 Python 3.11+ 标准库；测试使用 `unittest`，一条命令运行全部测试。
- R28 [要求§3]：仓库提供答辩演示程序，包含变量声明、赋值、条件分支、循环、输入、输出语句；并提供一条命令完成“生成分析器→编译→运行”的全过程。
- R29 [工程默认]：相同输入重复执行，生成器和编译器的文本产物逐字节相同，不含时间戳或随机内容。

## AC测试

除 AC00 外，命令的工作目录都是项目根目录。多行样例的内容在本节末尾“样例文件”中定义；“编译”指 `python3 -m minic <源文件> --frontend build/minic --out out/<名>`，其中 `build/minic` 是 AC01 的生成结果。

| AC | Rule | Input | Expected result |
|---|---|---|---|
| AC00 | 项目计划文件规范 | 本任务四文件、项目配置、作业要求与本轮授权范围 | spec 五个二级标题顺序正确；规则依据明确；R01–R29 均被 AC 和任务覆盖；checklist 的 AC 与本表一一对应；关键未决项明确；未执行项未勾选；本轮实施范围清楚。 |
| AC01 | R01, R02, R29 | 执行 `python3 -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out build/minic`；再把 `--out` 换成另一个空目录执行一次 | 两次退出码都是 0；输出目录中有 `lexer.py`、`parser.py`、`lexer_tables.json`、`parser_tables.json`、`report.html`；`lexer.py` 和 `parser.py` 中没有对 `ccgen`、`minic` 的 import；两个目录中这五个文件逐字节相同。 |
| AC02 | R01, R11 | 用 `tests/fixtures/calc.lex` 和 `tests/fixtures/calc.grammar`（无构造动作）生成分析器，分析输入 `1+2*3` | 生成与分析均成功，生成器代码无需改动。结果的根结点类型为 `E`，三个孩子依次是 `E`、`+`、`T`；右侧 `T` 的三个孩子依次是 `T`、`*`、`F`；全部叶子的词素自左向右为 `1 + 2 * 3`。 |
| AC03 | R04 | 对下列正规式逐个判定整串是否匹配：`(a\|b)*abb`；`[0-9]+`；`[a-zA-Z_][a-zA-Z0-9_]*`；`a?b+`；`//[^\n]*`；`\+\*` | `(a\|b)*abb` 接受 `abb`、`aabb`、`babb`，拒绝 `ab`、`abba`、空串；`[0-9]+` 接受 `0`、`007`，拒绝空串、`1a`；标识符式接受 `_x1`、`A`，拒绝 `1x`；`a?b+` 接受 `b`、`abbb`，拒绝 `a`、`aab`；注释式接受 `//`、`// 中文 x`，拒绝 `/`、含换行的 `//a\nb`；`\+\*` 只接受 `+*`。 |
| AC04 | R05 | 只含一条规则 `X (a\|b)*abb` 的词法规则；以及 `rules/minic.lex` | 对第一份规则：最小 DFA 恰有 4 个状态；子集法得到的 DFA 状态数不少于 4；对字母表 {a, b} 上长度 0 到 8 的全部串，NFA、DFA、最小 DFA 三者的接受结果都等于“该串以 abb 结尾”。对 `rules/minic.lex`：`lexer_tables.json` 记录了三个状态数，且最小 DFA 状态数不大于 DFA 状态数。 |
| AC05 | R03, R06, R07 | 用 mini-C 词法分析器扫描 `tests/fixtures/lex_ok.mc` | 没有错误；共 16 个记号，种别名依次为 `int IDENT = NUMBER ; if ( IDENT >= NUMBER ) write ( IDENT ) ;`；前四个记号的（种别码, 属性值）依次为 (1, 无)、(7, `integer`)、(19, 无)、(8, `10`)；`integer` 位于 1:5，`>=` 位于 2:13；空白和含中文的注释不产生记号。 |
| AC06 | R08, R24, R25 | 编译 `tests/fixtures/lex_error.mc` | 退出码 1；标准错误恰有两条诊断：`tests/fixtures/lex_error.mc:1:11: 词法错误[L001]` 指出字符 `@`，`tests/fixtures/lex_error.mc:2:7: 词法错误[L001]` 指出字符 `$`；输出目录中有 `tokens.txt` 和 `tokens.json`，没有任何 `ast.*` 和 `.ll` 文件。 |
| AC07 | R03, R09, R10 | AC01 生成的 `parser_tables.json` | 产生式共 38 条：0 号是增广产生式，1–37 号的左部与右部同附录 (1)–(37) 逐条一致；记录了 16 个非终结符的 FIRST 集，其中 FIRST(Expr) = { `IDENT`, `NUMBER`, `(` }；冲突列表非空，每一项都是向前看符号为 `else`、归约产生式为 16 号的移进-归约冲突，消解结果都是移进；没有归约-归约冲突。 |
| AC08 | R10, R25 | (a) 用 `tests/fixtures/calc.lex` 和 `tests/fixtures/ambiguous.grammar` 生成；(b) 用 `rules/minic.lex` 和删去 `%prefer shift else` 一行的 mini-C 语法规则生成 | 两种情形退出码都是 2，输出目录中没有 `lexer.py` 和 `parser.py`。(a) 的错误信息指出向前看符号 `+` 上的移进-归约冲突并列出相关项目；(b) 的错误信息指出向前看符号 `else` 上的移进-归约冲突。 |
| AC09 | R25, R26 | 三份有错的规则：(a) 词法规则中某行为 `X (ab`；(b) 语法规则使用了词法规则中没有的终结符 `foo`；(c) 某产生式右部有 3 个符号而动作写 `$5`。另加 (d) 词法规则中某行为 `X a*` | 四种情形退出码都是 2，标准错误含出错规则文件名和行号，输出目录保持为空。(b) 的信息含 `foo`；(d) 的信息说明该记号可匹配空串。 |
| AC10 | R11, R12 | 编译 `tests/fixtures/expr.mc`，查看 `ast.json` | 根为 `Program`，`body` 有 3 项。第 1 项是 `VarDecl`，`name` 为 `x`，`init` 为 `-(+(1, *(2, 3)), 4)`；第 2 项是 `Assign`，`value` 为 `*(+(1, 2), 3)`；第 3 项的 `value` 为 `/(/(8, 4), 2)`。这里 `op(l, r)` 表示 `BinaryOp` 结点，数字表示 `Number` 结点。 |
| AC11 | R12 | 编译 `tests/fixtures/dangling_else.mc`，查看 `ast.json` | `body` 第 4 项是没有 `else` 字段的 `If`，其 `then` 是带 `else` 字段的 `If`。 |
| AC12 | R13, R24, R25 | 分别编译 `tests/fixtures/syntax_chain.mc` 和 `tests/fixtures/syntax_eof.mc` | 两者退出码都是 1，标准错误各有一条 `语法错误[P001]`，输出目录有 `tokens.*`，没有 `ast.*` 和 `.ll`。前者位置为 1:15，实际记号为 `<`，期望集合恰为 `+ - * / ;`；后者位置为 1:10，实际记号为输入结束，期望集合包含 `;`。 |
| AC13 | R14, R15, R24, R25 | 编译 `tests/fixtures/semantic_error.mc` | 退出码 1；标准错误按位置顺序恰有四条诊断：2:1 `S002`（`a`）、3:1 `S001`（`b`）、4:9 `S003`、6:1 `S001`（`d`）；第 5 行的块内声明不报错；输出目录有 `tokens.*` 和 `ast.*`，没有 `.ll`。 |
| AC14 | R16, R17, R21, R29 | 以 `--stop-after ir` 编译 `examples/demo.mc` 两次，输出到两个目录 | 退出码 0，生成 `demo.ll`。其中：有 `define i32 @main()`；恰有 4 条 `alloca i32`，都在 `entry` 块的第一条 `br` 之前；出现 `icmp sle`、`icmp eq`、`mul i32`、`sdiv i32`、`sub i32`、`add i32`；有 1 处对 `@scanf` 的调用和 4 处对 `@printf` 的调用；有 while 和 if 各自的条件跳转与标号；以 `ret i32 0` 结束。两个目录中的 `tokens.json`、`ast.json`、`ast.html`、`demo.ll` 逐字节相同。输出目录中没有可执行文件。 |
| AC15 | R18, R19, R21 | 编译 `examples/demo.mc`（完整流程），分别以 `-O0` 和 `-O2` 各做一次；运行得到的可执行文件，标准输入先后为 `5` 和 `10` | 编译退出码 0；输出目录有 `demo.opt.ll`、`demo.s` 和可执行文件 `demo`。输入 `5` 时标准输出恰为三行 `15`、`120`、`1`；输入 `10` 时恰为 `55`、`3628800`、`0`；程序退出码 0。`-O0` 与 `-O2` 的输出相同。 |
| AC16 | R17, R18 | 编译并运行“运行样例”表中的 7 个程序 | 每个程序的标准输出与表中“标准输出”列完全一致，退出码 0。 |
| AC17 | R20, R25 | 编译 `examples/demo.mc`，附加 `--clang /nonexistent/clang` | 退出码 3；标准错误说明无法运行 clang；输出目录有 `tokens.*`、`ast.*`、`demo.ll`，没有 `demo.opt.ll`、`demo.s` 和可执行文件。 |
| AC18 | R21, R22 | 以 `--stop-after ast` 编译 `examples/demo.mc`，查看输出目录 | 输出目录有 `ast.json`、`ast.txt`、`ast.html`、`ast.dot`。`ast.html` 含一个 `<svg`；不含 `<link`、`<script src`、`src="http`、`href="http`；其中 `class="ast-node"` 的元素个数等于 `ast.json` 中带 `type` 键的对象个数。人工用浏览器离线打开，可见以 `Program` 为根、层次分明且结点互不重叠的树。 |
| AC19 | R05, R23 | AC01 生成的 `report.html` | 文件自包含（判据同 AC18）；依次含 R23 列出的九项内容；三个状态数与 `lexer_tables.json` 一致；产生式表有 38 行；ACTION/GOTO 表的行数等于 `parser_tables.json` 中的状态数；冲突一节写明 `else` 上的冲突按移进消解。 |
| AC20 | R02, R07, R11 | 在仓库之外的空目录中，以 `python3 -I` 运行 AC01 生成的 `lexer.py` 处理 `examples/demo.mc` 得到 `tokens.json`，再以 `python3 -I` 运行 `parser.py` 处理该 `tokens.json` 得到 `ast.json` | 两条命令退出码都是 0；得到的 `tokens.json`、`ast.json` 与以 `--stop-after ast` 编译 `examples/demo.mc` 得到的同名文件逐字节相同。 |
| AC21 | R27 | 执行 `python3 -m unittest discover -s tests -v`；并扫描 `ccgen/`、`minic/`、`tests/`、`scripts/` 下全部 `.py` 文件的 import | 测试命令退出码 0，没有失败和错误；被跳过的测试逐条列出原因。所有 import 的顶层模块都属于标准库或本仓库；仓库中没有 `requirements.txt` 之类的依赖清单。 |
| AC22 | R28 | 查看编译 `examples/demo.mc` 得到的 `ast.json`；执行 `echo 5 \| bash scripts/demo.sh` | AST 中出现 `VarDecl`、`Assign`、`If`（带 `else`）、`While`、`Read`、`Write` 六种结点。演示脚本退出码 0，标准输出的最后三行为 `15`、`120`、`1`，并在此之前列出各产物文件的路径。 |

### 样例文件

`examples/demo.mc`：

```c
// 答辩演示：读入 n，输出 1 到 n 的和、n 的阶乘，以及 n 的奇偶（偶数 0，奇数 1）
int n;
int i = 1;
int sum = 0;
int fact = 1;
read(n);
while (i <= n) {
    sum = sum + i;
    fact = fact * i;
    i = i + 1;
}
write(sum);
write(fact);
if (n - n / 2 * 2 == 0) {
    write(0);
} else {
    write(1);
}
```

`tests/fixtures/lex_ok.mc`：

```c
int integer = 10;
if (integer >= 3) write(integer); // 最长匹配与注释
```

`tests/fixtures/lex_error.mc`：

```c
int a = 3 @ 4;
a = a $ 2;
```

`tests/fixtures/calc.lex`：

```text
%skip WS
WS   [ \t\r\n]+
num  [0-9]+
+    \+
*    \*
(    \(
)    \)
```

`tests/fixtures/calc.grammar`：

```text
E -> E + T
E -> T
T -> T * F
T -> F
F -> ( E )
F -> num
```

`tests/fixtures/ambiguous.grammar`：

```text
E -> E + E
E -> num
```

`tests/fixtures/expr.mc`：

```c
int x = 1 + 2 * 3 - 4;
x = (1 + 2) * 3;
x = 8 / 4 / 2;
```

`tests/fixtures/dangling_else.mc`：

```c
int a = 1;
int b = 0;
int x = 0;
if (a) if (b) x = 1; else x = 2;
write(x);
```

`tests/fixtures/syntax_chain.mc`（单行）：

```c
int x = 1 < 2 < 3;
```

`tests/fixtures/syntax_eof.mc`（单行，行末有换行符，没有分号）：

```c
int x = 1
```

`tests/fixtures/semantic_error.mc`：

```c
int a = 1;
int a = 2;
b = a + 1;
int c = 2147483648;
{ int a = 3; write(a); }
read(d);
```

### 运行样例

下列文件都在 `tests/fixtures/run/` 下，内容为单行；`dangling_else.mc` 复用上面的样例。标准输出各值之间为换行，表中用空格分隔书写。

| 文件 | 内容 | 标准输入 | 标准输出 |
|---|---|---|---|
| `arith.mc` | `write(7 / 2); write(0 - 7 / 2); write((0 - 7) / 2); write(2 + 3 * 4); write((2 + 3) * 4); write(10 - 3 - 2);` | 无 | `3 -3 -3 14 20 5` |
| `rel.mc` | `write(1 < 2); write(2 < 1); write(3 == 3); write(3 != 3); write(2 <= 2); write(3 >= 4); write(5 > 4);` | 无 | `1 0 1 0 1 0 1` |
| `scope.mc` | `int x = 1; { int x = 2; write(x); } write(x); if (x) int x = 5; write(x); int y; write(y);` | 无 | `2 1 1 0` |
| `control.mc` | `int i = 0; while (i < 3) { if (i == 1) write(100); else write(i); i = i + 1; } if (i < 0) write(7); while (0) write(8); write(i);` | 无 | `0 100 2 3` |
| `wrap.mc` | `int m = 2147483647; write(m + 1);` | 无 | `-2147483648` |
| `io.mc` | `int a; int b; read(a); read(b); write(a - b);` | `3 -10` | `13` |
| `tests/fixtures/dangling_else.mc` | 见上 | 无 | `2` |

## 假设

| 编号 | 选择/假设 | 类别 | 依据与验证方式 | 影响规则 |
|---|---|---|---|---|
| H01 | 实现语言为 Python 3，只用标准库 | 用户已确认 | 2026-11-10 会话问答“实现语言” | R02, R27 |
| H02 | 中间代码走 LLVM IR 路线，并调用 clang 完成优化与机器码生成 | 用户已确认 | 2026-11-10 会话问答“中间代码” | R16, R19, R20 |
| H03 | 本任务只做代码成品，不含文档与 PPT | 用户已确认 | 2026-11-10 用户原话：“这次任务不包含文档，只需要做出一个成品” | 范围 |
| H04 | 词法规则以正规式而非产生式形式的正规文法给出 | 工程默认 | 要求 §4 的词法规则表本身是正规式，§1.1 指定的 Thompson 算法以正规式为输入；二者表达能力等价。若答辩要求演示正规文法输入，需新增规则 | R04, R05 |
| H05 | 语法分析采用规范 LR(1) | 工程默认 | 要求 §1.1 允许 LL 或 LR；附录文法含左递归，LR 可原样使用。2026-11-10 用一次性探针核对：该文法在规范 LR(1) 下仅有 `else` 上的 2 处移进-归约冲突，无归约-归约冲突 | R09, R10 |
| H06 | 在附录词法之外增加 `//` 行注释，作为被丢弃的记号 | 工程默认 | 附录标明规则为“参考”；演示程序需要注释。只需在规则文件加一行，可随时删去 | R03, R06 |
| H07 | 附录未规定的语义按 C 的习惯取定：块作用域、关系结果为 0/1、条件非零为真、未带初值的变量为 0 | 工程默认 | 附录只给出词法和语法。取值见 R14、R18，改动只影响语义检查与 IR 生成 | R14, R18 |
| H08 | 语法错误只报第一个，不做错误恢复 | 工程默认 | 要求 §1.1 只要求“有报错功能”；规范 LR(1) 能在读入出错记号时立即发现错误 | R13 |
| H09 | 除零、`read` 遇到非整数输入的行为不作规定，也不检查 | 工程默认 | 附录未规定；演示程序与测试样例不触发这些情形 | R18 |
| H10 | 运行环境的 clang 支持不透明指针 `ptr`（LLVM 15 及以上） | 待验证 | 本机 Apple clang 21.0.0 已于 2026-11-10 用手写 IR 样例验证编译、优化、运行均可；答辩用机若不同，需在该机执行 AC15 复核。不阻塞实施 | R19 |
| H11 | 生成器与编译器在 Python 3.11 上运行 | 待验证 | 本机 `python3` 为 3.11.15，已核对版本；代码实现后由 AC21 验证 | R27 |
