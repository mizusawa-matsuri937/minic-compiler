# mini-C 编译器生成器与编译器成品 设计

状态：设计已完成（2026-11-10），未实施。业务规则与验收定义以 [spec](spec.md) 为准，本文只解释怎样实现。

## 1. 整体思路

系统分成两个互不依赖的 Python 包和一组规则文件。

- `ccgen` 是生成器，与具体语言无关（R01）。它读入词法规则和语法规则，按课内算法造出 DFA 和 LR(1) 分析表，再把表和一段固定的驱动代码拼成两个独立的 Python 源文件 `lexer.py`、`parser.py`（R02）。
- `minic` 是 mini-C 编译器驱动。它加载生成出来的 `lexer.py`、`parser.py`，依次做词法分析、语法分析、语义检查、LLVM IR 生成、调用 clang，并把每一步的结果存成文件（R21）。
- `rules/minic.lex` 和 `rules/minic.grammar` 描述 mini-C（R03）。换一套规则文件就得到另一种语言的分析器，AC02 用四则运算语言验证这一点。

```text
rules/minic.lex ──┐                        ┌─> build/minic/lexer.py  ─┐
                  ├─> python3 -m ccgen ────┤                          │  （生成阶段，做一次）
rules/minic.grammar┘                       ├─> build/minic/parser.py ─┤
                                           └─> *_tables.json, report.html
                                                                      │
源程序 demo.mc ─> lexer.py ─> 记号 ─> parser.py ─> AST ─> 语义检查 ─> LLVM IR ─> clang ─> 优化 IR / 汇编 / 可执行文件
                 （python3 -m minic 依次调用，产物写入 out/demo/）
```

两个包之间唯一的接口是数据格式：记号列表和 AST 都是普通的字典与列表，和落盘的 JSON 完全一致。因此生成的分析器不需要导入任何项目代码，`minic` 也不需要知道分析表的内部结构。

## 2. 当前事实与前置条件

| 内容 | 当前情况 | 证据或验证方式 | 状态 |
|---|---|---|---|
| Python | `python3` 为 3.11.15；未安装 pytest | 2026-11-10 执行 `python3 --version` | 已验证 |
| clang | Apple clang 21.0.0，arm64-apple-darwin | 2026-11-10 执行 `clang --version` | 已验证 |
| clang 处理手写 IR | 第 8 节形状的 `.ll`（`ptr`、可变参数调用 `scanf`/`printf`、循环）可以编译、`-O2` 优化、生成汇编并正确运行；输入 10 时样例输出 27，符合预期 | 2026-11-10 用一次性样例实测，样例不在仓库中 | 已验证 |
| 目标三元组警告 | `.ll` 不写 `target triple` 时 clang 给出 `-Woverride-module` 警告；加 `-Wno-override-module` 后无警告 | 同上 | 已验证 |
| 附录文法的 LR(1) 性质 | 不加增广产生式时规范 LR(1) 有 263 个项目集、76 个不同的心；仅有 2 处冲突，都是 `else` 上“归约 16 号产生式 / 移进”的冲突；项目集构造耗时约 0.01 秒 | 2026-11-10 用一次性探针脚本实测，脚本不在仓库中 | 已验证（探针，非项目代码） |
| 加增广产生式后的状态数 | 预计 264 | 由上一行推算 | 估算，实现后以 `parser_tables.json` 为准 |
| Graphviz、`opt`、`llc` | 本机均未安装 | 2026-11-10 执行 `command -v` | 已验证；方案不依赖它们 |
| 仓库 | 已 `git init`，分支 `main`，尚无业务代码 | `git status` | 已验证 |

## 3. 目录与组件职责

```text
minic-compiler/
├── ccgen/                    # 生成器（语言无关）
│   ├── __main__.py           # 命令行入口，参数解析，退出码
│   ├── errors.py             # RuleError(文件, 行号, 说明)
│   ├── regex.py              # 正规式文本 -> 正规式语法树
│   ├── nfa.py                # Thompson 算法
│   ├── dfa.py                # 子集法、等价状态法
│   ├── lexspec.py            # 词法规则文件解析，汇总成 LexTables
│   ├── grammar.py            # 语法规则文件解析，构造动作解析
│   ├── lr1.py                # FIRST 集、LR(1) 项目集规范族、ACTION/GOTO、冲突处理
│   ├── codegen.py            # 把表填进模板，产出 lexer.py / parser.py 的文本
│   ├── templates/            # lexer_template.py、parser_template.py（固定驱动代码）
│   └── report.py             # 构造报告 report.html
├── minic/                    # mini-C 编译器驱动
│   ├── __main__.py           # 命令行入口，阶段调度，产物落盘，退出码
│   ├── frontend.py           # 用 importlib 加载生成的 lexer.py / parser.py
│   ├── diagnostics.py        # 诊断对象与统一格式
│   ├── semantic.py           # 作用域、声明检查、常数范围
│   ├── irgen.py              # AST -> LLVM IR 文本
│   ├── backend.py            # 调用 clang
│   └── astviz.py             # ast.txt / ast.html / ast.dot
├── rules/                    # minic.lex、minic.grammar
├── examples/                 # demo.mc
├── scripts/demo.sh           # 一条命令的答辩演示
└── tests/                    # unittest 用例与 fixtures/
```

| 组件 | 职责 | 输入与输出 | 关联规则/AC |
|---|---|---|---|
| `ccgen/regex.py` | 解析正规式 | 字符串 → 语法树；语法错误抛 `RuleError` | R04, R26；AC03, AC09 |
| `ccgen/nfa.py` | Thompson 构造 | 语法树 → NFA | R05；AC04 |
| `ccgen/dfa.py` | 确定化与最小化 | NFA → DFA → 最小 DFA | R05, R06；AC04 |
| `ccgen/lexspec.py` | 读词法规则，编排上面三步 | `.lex` → `LexTables` | R06, R07, R26；AC05, AC09 |
| `ccgen/grammar.py` | 读语法规则和动作 | `.grammar` → `Grammar` | R03, R11, R26；AC07, AC09 |
| `ccgen/lr1.py` | 造分析表 | `Grammar` → `ParseTables` | R09, R10；AC07, AC08 |
| `ccgen/codegen.py` | 产出独立分析器源码 | 表 + 模板 → 源码文本 | R02, R29；AC01, AC20 |
| `ccgen/report.py` | 构造报告 | 两套表 → HTML 文本 | R23；AC19 |
| `minic/semantic.py` | 语义检查 | AST → 诊断列表，并在结点上标注存储槽 | R14, R15；AC13 |
| `minic/irgen.py` | IR 生成 | 标注后的 AST → `.ll` 文本 | R16–R18；AC14, AC16 |
| `minic/backend.py` | 优化与机器码 | `.ll` → `.opt.ll`、`.s`、可执行文件 | R19, R20；AC15, AC17 |
| `minic/astviz.py` | AST 展示 | AST → 文本、HTML、DOT | R21, R22；AC18 |
| `minic/__main__.py` | 调度、落盘、诊断输出 | 命令行 → 产物与退出码 | R21, R24, R25；AC06, AC12 |

`ccgen` 内的模块只允许互相导入和导入标准库；`minic` 不导入 `ccgen`。模板文件本身必须是语法正确、只用标准库的 Python 文件。

## 4. 规则文件格式

两种文件都按 UTF-8 读取，逐行解析；空行和以 `#` 开头的行忽略。出错时 `RuleError` 带文件名和行号（R26）。

### 4.1 词法规则 `.lex`

```text
%skip 名字 [名字 ...]      # 这些记号匹配后丢弃，可出现多次
名字 <空白> 正规式          # 一行一条规则
```

- 名字是该行第一个以空白分隔的字段，也就是语法规则里的终结符名字，可以是任意不含空白的串，如 `IDENT`、`;`、`==`。名字不能重复，不能以 `%` 或 `#` 开头，不能是 `$`、`ε`。
- 正规式是该行名字之后去掉首尾空白的剩余部分，其中的空格按字面字符处理。
- 规则的先后顺序就是优先级（R06）。非 `%skip` 的记号按出现顺序从 1 起编种别码；`%skip` 的记号没有种别码；输入结束符 `$` 的种别码为 0。
- `%skip` 提到的名字必须有对应规则。

正规式语法（R04），优先级从低到高为：`|`、连接、后缀 `*` `+` `?`。

| 写法 | 含义 |
|---|---|
| `r\|s`、`rs`、`r*`、`r+`、`r?`、`(r)` | 选择、连接、闭包、正闭包、可选、分组 |
| `[abc]`、`[a-z0-9_]` | 字符类，可含范围 |
| `[^\n]` | 取反字符类 |
| `\n` `\t` `\r` | 换行、制表、回车 |
| `\` 加其他任意字符 | 该字符本身，如 `\+`、`\(`、`\\` |
| 其他字符 | 字面字符 |

元字符只有 `| * + ? ( ) [ ] \`。字符类内部只有 `]`、`\`、开头的 `^` 和两字符之间的 `-` 有特殊含义。

字母表是 ASCII 码 0 到 127 的字符，再加一个代表“所有其他字符”的伪符号 `OTHER`。只有取反字符类会包含 `OTHER`，这使 `//[^\n]*` 能匹配含中文的注释，而中文出现在别处仍是非法字符。

mini-C 的词法规则 `rules/minic.lex` 内容如下（顺序同附录表格，种别码因此为 `int`=1 … `write`=6、`IDENT`=7、`NUMBER`=8、`+`=9 … `/`=12、`==`=13 … `>`=18、`=`=19、`;`=20、`,`=21、`(`=22、`)`=23、`{`=24、`}`=25）：

```text
# mini-C 词法规则。格式：记号名 <空白> 正规式；靠前的规则优先。
%skip WS COMMENT
WS       [ \t\r\n]+
COMMENT  //[^\n]*

# 关键字（须写在 IDENT 之前）
int      int
if       if
else     else
while    while
read     read
write    write

# 标识符与整型常数
IDENT    [a-zA-Z_][a-zA-Z0-9_]*
NUMBER   [0-9]+

# 算术运算符
+        \+
-        -
*        \*
/        /

# 关系运算符
==       ==
!=       !=
<=       <=
>=       >=
<        <
>        >

# 赋值与界符
=        =
;        ;
,        ,
(        \(
)        \)
{        {
}        }
```

`,` 在附录词法中存在而语法中未使用，保留在词法规则里；源程序出现 `,` 时由语法分析报错。

### 4.2 语法规则 `.grammar`

```text
%start 符号                 # 可选，缺省取第一条产生式的左部
%prefer shift 终结符 [...]  # 这些终结符上的移进-归约冲突取移进，可出现多次
左部 -> 符号 符号 ...  [=> 动作]
```

- 一行一条产生式，不支持用 `|` 合并多个右部，这样产生式编号与书写顺序一一对应。符号以空白分隔。右部写 `ε` 或 `%empty` 表示空串。
- 出现在某个左部的符号是非终结符，其余都是终结符。终结符必须是词法规则中的非 `%skip` 记号名，否则报错（R26）。词法规则中有而语法未用的记号是允许的。
- 生成器自动加入 0 号增广产生式 `S' -> 开始符号`（若 `S'` 已被占用则继续加撇号），用户产生式从 1 起编号（R03）。
- `->` 和 `=>` 是分隔符，不能用作符号名。

构造动作（R11）的语法：

```text
动作   := $k                          传递第 k 个右部符号的值
        | 名字(字段=$k, 字段=$k, ...)  新建类型为“名字”的结点，可以没有字段
        | []                          空列表
        | [项, 项, ...]               列表；项为 $k（一个元素）或 *$k（把第 k 个值这个列表展开）
```

- `k` 从 1 起，不得超过右部长度。非终结符的值是它归约时算出的值。终结符的值是记号；记号被放进结点字段或列表时取其词素字符串。
- 新建的结点是字典：先是 `type`、`line`、`col`，再按动作中书写的顺序放各字段。`line`、`col` 取该产生式所覆盖的第一个记号的位置；右部为空时取当前向前看记号的位置。
- 没写动作的产生式使用缺省动作：结点为 `{"type": 左部, "line", "col", "children": [...]}`，其中终结符孩子写成 `{"type": 种别名, "lexeme": 词素, "line", "col"}`。AC02 的预期就是这种结点。

mini-C 的语法规则 `rules/minic.grammar` 内容如下，共 37 条，顺序和编号同附录：

```text
# mini-C 语法规则。产生式编号 1-37 与作业要求附录一致。
%start S
%prefer shift else

S -> Program                                    => $1
Program -> StatementList                        => Program(body=$1)
StatementList -> Statement StatementList        => [$1, *$2]
StatementList -> ε                              => []

Statement -> VarDecl                            => $1
Statement -> AssignStmt                         => $1
Statement -> IfStmt                             => $1
Statement -> WhileStmt                          => $1
Statement -> ReadStmt                           => $1
Statement -> WriteStmt                          => $1
Statement -> CompoundStmt                       => $1

VarDecl -> int IDENT ;                          => VarDecl(name=$2)
VarDecl -> int IDENT = Expr ;                   => VarDecl(name=$2, init=$4)
AssignStmt -> IDENT = Expr ;                    => Assign(target=$1, value=$3)
CompoundStmt -> { StatementList }               => Block(body=$2)
IfStmt -> if ( Expr ) Statement                 => If(cond=$3, then=$5)
IfStmt -> if ( Expr ) Statement else Statement  => If(cond=$3, then=$5, else=$7)
WhileStmt -> while ( Expr ) Statement           => While(cond=$3, body=$5)
ReadStmt -> read ( IDENT ) ;                    => Read(target=$3)
WriteStmt -> write ( Expr ) ;                   => Write(value=$3)

Expr -> RelExpr                                 => $1
RelExpr -> AddExpr < AddExpr                    => BinaryOp(op=$2, left=$1, right=$3)
RelExpr -> AddExpr > AddExpr                    => BinaryOp(op=$2, left=$1, right=$3)
RelExpr -> AddExpr == AddExpr                   => BinaryOp(op=$2, left=$1, right=$3)
RelExpr -> AddExpr != AddExpr                   => BinaryOp(op=$2, left=$1, right=$3)
RelExpr -> AddExpr <= AddExpr                   => BinaryOp(op=$2, left=$1, right=$3)
RelExpr -> AddExpr >= AddExpr                   => BinaryOp(op=$2, left=$1, right=$3)
RelExpr -> AddExpr                              => $1
AddExpr -> AddExpr + Term                       => BinaryOp(op=$2, left=$1, right=$3)
AddExpr -> AddExpr - Term                       => BinaryOp(op=$2, left=$1, right=$3)
AddExpr -> Term                                 => $1
Term -> Term * Factor                           => BinaryOp(op=$2, left=$1, right=$3)
Term -> Term / Factor                           => BinaryOp(op=$2, left=$1, right=$3)
Term -> Factor                                  => $1
Factor -> IDENT                                 => Identifier(name=$1)
Factor -> NUMBER                                => Number(value=$1)
Factor -> ( Expr )                              => $2
```

由此得到的 mini-C AST 结点共 11 种：

| 类型 | 字段 | 说明 |
|---|---|---|
| `Program` | `body`：语句列表 | 根结点 |
| `VarDecl` | `name`：字符串；`init`：表达式，可无 | 位置是 `int` |
| `Assign` | `target`：字符串；`value`：表达式 | 位置是被赋值的标识符 |
| `Block` | `body`：语句列表 | 位置是 `{` |
| `If` | `cond`、`then`；`else` 可无 | |
| `While` | `cond`、`body` | |
| `Read` | `target`：字符串 | 位置是 `read` |
| `Write` | `value`：表达式 | |
| `BinaryOp` | `op`：运算符词素；`left`、`right` | 算术与关系运算共用 |
| `Identifier` | `name`：字符串 | |
| `Number` | `value`：数字串 | 转整数留给语义检查 |

优先级、结合性、`a < b < c` 非法都由文法本身保证（R12），动作只是丢掉单产生式链和括号。

## 5. 词法分析器生成

### 5.1 三步构造（R05）

1. **Thompson 算法**（`nfa.py`）。对每条规则的正规式语法树自底向上构造 NFA 片段，每个片段恰有一个初态和一个终态：
   - 单个字符或字符类：新建两个状态，之间一条标有字符集合的弧。
   - `rs`：`r` 的终态到 `s` 的初态连一条 ε 弧。
   - `r|s`：新建初态和终态，初态以 ε 弧连到两个片段的初态，两个片段的终态以 ε 弧连到新终态。
   - `r*`：新建初态和终态，加四条 ε 弧（进入、跳过、回环、离开）。
   - `r+` 按 `rr*`、`r?` 按 `r|ε` 处理。

   然后新建一个总初态，以 ε 弧连到每条规则的片段初态；每条规则的终态记下该规则的序号。
2. **子集法**（`dfa.py`）。用 ε-闭包和 move 运算从总初态的闭包出发逐个求出 DFA 状态。一个 DFA 状态若含多个规则的终态，取序号最小的那条规则作为它识别的记号，这就实现了“靠前优先”。没有后继的情形不建死状态，转换表是部分函数。
3. **等价状态法**（`dfa.py`）。初始划分为：全部非终态一组，终态按所识别的记号各成一组（识别不同记号的终态不能合并）。反复检查每一组：若组内两个状态对某个输入符号转向不同的组，或一个有转换一个没有，就把该组拆开；直到不再变化。每组留一个代表状态。

为了输出确定（R29），每一步结束后都从初态出发按符号的固定顺序做广度优先遍历，按到达顺序重新给状态编号，初态为 0。集合在遍历前先排序。

规则文件解析阶段还要检查：任何记号不得匹配空串（总初态的 ε-闭包中不得含终态），否则扫描会原地打转（R26，AC09 的情形 d）。

“只能匹配一个固定串”的判定（R07）：正规式语法树只由单字符的连接构成，没有选择、闭包、可选和字符类。结果记在表里的 `fixed` 字段。

### 5.2 生成的 `lexer.py`

内容是：文件头注释、表（`TOKENS`、`START`、`ACCEPT`、`TRANS`、`OTHER_TRANS`，以 Python 字面量写出）、固定的驱动代码。对外接口：

```python
def tokenize(text: str) -> tuple[list[dict], list[dict]]:  # 返回 (记号列表, 错误列表)
```

扫描算法（R06、R08）：从当前位置出发沿 DFA 一直走到无路可走，途中记下最后一次到达终态的位置；有记录就取那段文本作为一个记号（最长匹配），没有记录就报告当前字符非法并只跳过这一个字符。行号、列号从 1 起，列按字符计，制表符算一列，遇到 `\n` 行号加一、列号归 1。

记号和错误的格式，也是 `tokens.json` 的内容：

```json
{
  "tokens": [
    {"code": 1, "kind": "int", "attr": null, "lexeme": "int", "line": 1, "col": 1},
    {"code": 7, "kind": "IDENT", "attr": "integer", "lexeme": "integer", "line": 1, "col": 5}
  ],
  "errors": [
    {"code": "L001", "line": 1, "col": 11, "message": "非法字符 '@'"}
  ]
}
```

列表中不含输入结束符。命令行用法：`python3 lexer.py 源文件 [-o tokens.json] [--text]`。缺省把上面的 JSON 写到标准输出；`--text` 改为输出二元式表。有词法错误时照常输出，诊断写到标准错误，退出码 1。

`tokens.txt`（二元式表）每个记号一行，四列以制表符分隔，属性值为空时写 `-`：

```text
序号	(种别码, 属性值)	种别名	行:列
1	(1, -)	int	1:1
2	(7, integer)	IDENT	1:5
```

所有 JSON 文件统一用 `json.dumps(对象, ensure_ascii=False, indent=2)` 加一个结尾换行写出，这是 AC20 逐字节比较的前提。

## 6. 语法分析器生成

### 6.1 LR(1) 构造（R09）

1. **FIRST 集**。对所有文法符号做不动点迭代，同时求出可推出空串的非终结符集合。
2. **项目与闭包**。LR(1) 项目是（产生式编号, 圆点位置, 向前看终结符）。闭包：对项目 `[A -> α·Bβ, a]`，把 B 的每条产生式 `B -> γ` 连同 FIRST(βa) 中的每个终结符 b 构成 `[B -> ·γ, b]` 加入，直到不再增加。
3. **项目集规范族**。初始项目集是 `[S' -> ·S, $]` 的闭包；对每个项目集和每个圆点后的符号求 GO，新的项目集加入族中。符号按在规则文件中首次出现的顺序处理，项目集按发现顺序编号，保证输出确定（R29）。
4. **分析表**。`[A -> α·aβ, b]` 且 a 是终结符：`ACTION[i, a]` 为移进到 GO 的目标；`[A -> α·, a]`：`ACTION[i, a]` 为按该产生式归约；`[S' -> S·, $]`：接受；非终结符上的 GO 填入 `GOTO`。

### 6.2 冲突处理（R10）

填表时发现同一格有两个动作即为冲突。处理规则：

- 移进-归约冲突，且向前看终结符在 `%prefer shift` 声明中：取移进，把冲突记入表的 `conflicts`，`resolution` 为 `shift`。
- 其余任何冲突（未声明的移进-归约、所有归约-归约）：收集齐所有冲突后抛 `RuleError`，信息中逐个列出状态号、向前看符号、冲突类型和相关项目（写成 `A -> α · β, a` 的形式）。生成失败，不写文件。

这对应课件“二义文法的应用：使用文法以外的信息解决分析动作冲突”。mini-C 文法中声明的只有 `else`，即附录备注 (3) 的最近配对规则。

### 6.3 生成的 `parser.py`

内容是：表（`PRODUCTIONS`、`ACTION`、`GOTO`、动作的结构化表示）和固定的驱动代码。对外接口：

```python
def parse(tokens: list[dict]) -> object            # 返回 AST（字典/列表/字符串）
class ParseError(Exception):                       # 属性：line, col, actual_kind, actual_lexeme, expected
```

驱动是标准的 LR 分析循环：状态栈和值栈并行。移进时值栈压入记号；归约时弹出右部长度个值，按该产生式的动作算出新值，再查 `GOTO` 压栈。值栈的每一项同时带着“所覆盖的第一个记号的位置”，用于给新结点填 `line`、`col`。

输入结束符的种别名为 `$`，词素为空，位置取最后一个记号末字符的下一列；没有任何记号时为 1:1。

查不到动作时抛 `ParseError`（R13）：`expected` 是当前状态 `ACTION` 行中有动作的全部终结符，按种别码升序排列，`$` 排在最后并显示为“输入结束”。规范 LR(1) 的向前看是精确的，所以错误在读到出错记号的当时就被发现，期望集合也不含多余的符号；AC12 断言 `1 < 2 < 3` 的期望集合恰为 `+ - * / ;` 依赖这一点。

动作在生成时已解析成结构化数据写进表中（例如 `("node", "If", [("cond", 3), ("then", 5)])`），驱动用一个小解释函数执行，不使用 `eval`。

命令行用法：`python3 parser.py tokens.json [-o ast.json]`。输入是 `lexer.py` 输出的 JSON；若其中 `errors` 非空则拒绝分析并以退出码 1 结束。语法错误时诊断写到标准错误，退出码 1。

### 6.4 表文件

`lexer_tables.json` 和 `parser_tables.json` 供测试和报告使用，至少含以下键（可以有更多）：

```text
lexer_tables.json:  tokens[{code, name, regex, skip, fixed}]
                    stats{nfa_states, dfa_states, min_dfa_states}
                    start, accept{状态: 记号名}, trans{状态: {字符: 状态}}, other_trans{状态: 状态}
parser_tables.json: productions[{id, lhs, rhs[], action}]   # id 0 为增广产生式
                    terminals[], nonterminals[], first{非终结符: [终结符...]}
                    states（整数）, action{状态: {终结符: [动作, 参数]}}, goto{状态: {非终结符: 状态}}
                    conflicts[{state, lookahead, kind, shift, reduce, resolution}]
```

`kind` 取 `shift-reduce` 或 `reduce-reduce`；`reduce` 是产生式编号。

### 6.5 生成器命令

```text
python3 -m ccgen --lex 词法规则 --grammar 语法规则 --out 输出目录
```

先在内存中完成全部构造和五个文件的文本，全部成功后才创建目录并写文件；任何一步失败都不写（R26）。成功时在标准输出打印各文件路径和一行统计（记号数、三种状态数、产生式数、LR(1) 状态数、已消解的冲突数）。生成的文件头注释只写规则文件的文件名，不写时间和绝对路径（R29）。

## 7. 编译器驱动 `minic`

```text
python3 -m minic 源文件 [--frontend 目录] [--out 目录] [--stop-after {tokens,ast,ir}]
                        [-O {0,1,2,3}] [--clang 路径] [--run]
```

缺省值：`--frontend build/minic`；`--out out/<源文件主名>`；`-O 2`；`--clang clang`。`--frontend` 目录中缺少 `lexer.py` 或 `parser.py` 时提示先运行 `ccgen`，退出码 2。

| 阶段 | 做什么 | 写出的文件 | 出错时 |
|---|---|---|---|
| 1 词法 | `lexer.tokenize` | `tokens.txt`、`tokens.json` | 有 L001：输出诊断，退出码 1 |
| 2 语法 | `parser.parse` | `ast.json`、`ast.txt`、`ast.html`、`ast.dot` | P001：输出诊断，退出码 1，不写 AST 文件 |
| 3 语义 | `semantic.check` | 无 | 有 S00x：输出全部诊断，退出码 1 |
| 4 IR | `irgen.generate` | `<主名>.ll` | 不应出错 |
| 5 后端 | `backend.build` | `<主名>.opt.ll`、`<主名>.s`、`<主名>`（Windows 上为 `<主名>.exe`） | 退出码 3，前面的文件保留 |
| 6 运行 | 仅 `--run`：执行可执行文件，标准输入输出直接继承 | 无 | 退出码取被运行程序的退出码 |

开始时先删除输出目录中上表列出的、属于本次源文件的旧文件（只删这些确定的文件名，不清空目录），这样“出错阶段之后的产物不存在”（R25）才可验证。阶段信息和产物路径打印到标准错误，使 `--run` 时标准输出只有被编译程序自己的输出。

诊断（R24）统一由 `diagnostics.py` 格式化，例如：

```text
tests/fixtures/lex_error.mc:1:11: 词法错误[L001]: 非法字符 '@'
tests/fixtures/syntax_chain.mc:1:15: 语法错误[P001]: 遇到 '<'，期望 '+' '-' '*' '/' ';' 之一
tests/fixtures/semantic_error.mc:3:1: 语义错误[S001]: 变量 'b' 未声明
```

路径按命令行给出的原样打印。

### 7.1 语义检查（R14、R15）

对 AST 做一次遍历，维护作用域栈，每个作用域是“名字 → 存储槽”的字典。

- `Program` 建立全局作用域；`Block` 进入时压栈、离开时弹栈；`If` 的 `then`、`else` 和 `While` 的 `body` 各自再压一层，因此 `if (x) int x = 5;` 中的声明只在该语句体内可见。
- `VarDecl`：先检查 `init`（此时本变量尚未声明，`int x = x;` 会报 S001），再在当前作用域登记。当前作用域已有同名变量报 S002，位置是该 `VarDecl`。
- `Identifier`、`Assign` 的 `target`、`Read` 的 `target`：从内向外查找，找不到报 S001，位置分别是该 `Identifier`、`Assign`、`Read` 结点。
- `Number`：值大于 2147483647 报 S003。
- 每次成功声明分配一个唯一的存储槽名：某个名字第一次声明用 `名字.addr`，之后每次再声明用 `名字.addr.1`、`名字.addr.2`……。检查通过后把槽名写到内存中的 `VarDecl`、`Identifier`、`Assign`、`Read` 结点上（键名 `_slot`），供 IR 生成使用。AST 文件在阶段 2 已经写出，不受影响。

错误全部收集，按（行, 列）排序后输出。

## 8. LLVM IR 生成（R16–R18）

整个程序翻译成一个 `main` 函数。`irgen.py` 维护三样东西：临时值计数器（`%t1`、`%t2`……）、控制结构计数器（每个 if 或 while 取一个编号 k）、当前基本块的指令列表。所有 `alloca` 单独收集，最后统一放在 `entry` 块最前面。

模块的固定骨架（已在本机 clang 上实测可用）：

```llvm
; ModuleID = 'demo.mc'
source_filename = "demo.mc"

@.fmt.read = private unnamed_addr constant [3 x i8] c"%d\00"
@.fmt.write = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)
declare i32 @scanf(ptr, ...)

define i32 @main() {
entry:
  %n.addr = alloca i32
  ...
  ret i32 0
}
```

不写 `target triple` 和 `datalayout`，由 clang 按本机补全，这样同一份 IR 在不同机器上都能编译。

翻译方案：

| AST 结点 | 生成的 IR |
|---|---|
| `Number` | 不产生指令，操作数就是该常数 |
| `Identifier` | `%t = load i32, ptr %槽` |
| `BinaryOp` 算术 | 先左后右求出操作数，再 `add` / `sub` / `mul` / `sdiv i32`。不加 `nsw`，溢出即回绕 |
| `BinaryOp` 关系 | `%c = icmp slt/sgt/eq/ne/sle/sge i32 a, b`，再 `%t = zext i1 %c to i32` |
| `VarDecl` | `entry` 中 `%槽 = alloca i32`；声明处 `store i32 初值或 0, ptr %槽` |
| `Assign` | 求值后 `store i32 值, ptr %槽` |
| `Read` | `call i32 (ptr, ...) @scanf(ptr @.fmt.read, ptr %槽)` |
| `Write` | 求值后 `call i32 (ptr, ...) @printf(ptr @.fmt.write, i32 值)` |
| `Block` | 依次翻译其中的语句 |
| `If` | 条件值 v：`%b = icmp ne i32 v, 0`；`br i1 %b, label %if.then.k, label %if.else.k`（无 else 时第二个目标是 `%if.end.k`）；各分支末尾 `br label %if.end.k` |
| `While` | `br label %while.cond.k`；`while.cond.k` 中求条件并 `br i1` 到 `%while.body.k` 或 `%while.end.k`；循环体末尾 `br label %while.cond.k` |

条件一律先得到 i32 再与 0 比较，不为“条件本身就是比较”的情形开特例。这样翻译规则只有一条，多出来的 `zext` 和 `icmp` 交给 clang 的优化消除，优化前后 IR 的对比也正好用于答辩展示。

mini-C 没有 `break`、`return`，每个基本块都自然落到下一个，不会出现无终结指令的块或不可达代码。调用 `scanf`、`printf` 时必须写出完整的可变参数函数类型 `i32 (ptr, ...)`，否则在 arm64 上参数传递方式不对。

## 9. 后端（R19、R20）

`backend.py` 用 `subprocess.run` 依次执行三条命令，`N` 是 `-O` 的取值：

```text
clang -Wno-override-module -ON -S -emit-llvm demo.ll -o demo.opt.ll    # 优化后的 IR
clang -Wno-override-module -ON -S demo.ll -o demo.s                    # 汇编
clang -Wno-override-module -ON demo.ll -o demo                         # 可执行文件
```

clang 找不到（`FileNotFoundError`）或返回非零时，把 clang 的标准错误原样转出，再打印一行说明，退出码 3。已生成的 `tokens.*`、`ast.*`、`.ll` 不删除。

## 10. 可视化

### 10.1 AST（R21、R22）

- `ast.txt`：缩进的树，用 `├──`、`└──` 画线，每行是“字段名: 类型 标量字段”。
- `ast.dot`：Graphviz DOT 文本，给装了 Graphviz 的人使用；本项目自己不调用 `dot`。
- `ast.html`：一个 HTML 文件，内嵌一个由本项目代码计算坐标的 `<svg>`，没有外部样式、脚本、字体或图片。

SVG 的布局算法：结点标签为类型加标量字段（如 `BinaryOp +`、`Identifier sum`、`Number 10`、`VarDecl n`），宽度按字符数估算（非 ASCII 字符按两个字符宽）。子树宽度 = max(本结点宽度, 各子树宽度之和加间距)；孩子从左到右依次排开，父结点放在孩子所占区间的正中；纵坐标 = 深度 × 层高。子树各占互不相交的水平区间，所以结点不会重叠。每个 AST 结点画成一个 `<g class="ast-node">`（内含圆角矩形和文字），父子之间画一条线，线旁用小字标出字段名，列表字段写成 `body[0]`、`body[1]`。文字全部做 HTML 转义。SVG 外面套一个可滚动的容器，大树可以横向滚动。

### 10.2 生成器构造报告（R23）

`report.html` 同样自包含，用普通 HTML 表格，按 R23 的顺序分九节：记号与正规式（含种别码、是否丢弃）；三个状态数；最小 DFA 转换表（行是状态，列是合并后的字符区间，终态标出所识别的记号）；编号产生式；FIRST 集；项目集数量；ACTION 表与 GOTO 表（移进写 `s12`，归约写 `r16`，接受写 `acc`）；冲突及消解。转换表的列需要把转换相同的连续字符合并成区间（如 `a-z`），否则有 128 列。

## 11. 异常、恢复与兼容

| 情形 | 处理方式 | 恢复/回滚方式 | 对应 AC |
|---|---|---|---|
| 规则文件有错 | 抛 `RuleError`，`ccgen` 打印 `文件:行号: 说明`，退出码 2 | 写文件发生在全部构造成功之后，失败时磁盘无变化；改正规则后重新运行 | AC09 |
| 分析表有未声明的冲突 | 同上，信息列出全部冲突 | 修改文法，或用 `%prefer shift` 声明 | AC08 |
| 源程序有非法字符 | 记录 L001，跳过一个字符继续 | 记号文件照常写出，不进入语法分析 | AC06 |
| 源程序有语法错误 | `ParseError` 转成 P001，停止 | 不写 AST 文件；改正源程序后重新编译 | AC12 |
| 源程序有语义错误 | 收集全部 S00x 后停止 | AST 文件已写出，不写 `.ll` | AC13 |
| clang 缺失或失败 | 退出码 3，转出 clang 的错误信息 | 前端产物保留；装好 clang 或用 `--clang` 指定后重新编译 | AC17 |
| 源文件或规则文件不存在、参数错误 | 打印说明，退出码 2 | 不适用 | 无单独 AC，由 R25 约束 |
| 输出目录残留旧产物 | 编译开始时删除本次会写的那些文件名 | 不适用 | AC06, AC12, AC13 |

本项目是新建仓库，没有需要兼容的既有功能、接口或数据，也没有持久化存储。

## 12. 方案取舍与参考

| 决策 | 采用方案与理由 | 备选方案及未采用原因 | 约束/代价 |
|---|---|---|---|
| 语法分析方法 | 规范 LR(1)。附录文法左递归，可原样使用；错误发现及时，期望集合精确；探针显示只有 `else` 一类冲突 | LL(1)：须消除左递归、提取左因子，文法与附录不再逐条对应，AST 也难直接得到左结合。SLR(1)/LALR(1)：状态约 76 个，更小，但出错时可能先做多余的归约，期望集合偏大 | 约 264 个状态，报告中的分析表较长，需要滚动查看 |
| 生成物形态 | 表加固定驱动拼成独立的 `.py` 文件 | 只输出 JSON 表、由 `minic` 内置驱动解释：实现更省，但“输出词法分析器和语法分析器”不够直观，也无法脱离项目运行 | 需要维护两个模板文件，并保证生成结果确定 |
| AST 的定义方式 | 规则文件里写声明式构造动作 | 在生成器里写死 mini-C 的结点：违反 R01。允许嵌入任意 Python 代码：灵活但要 `eval`，且不便展示 | 动作语言很小，只能传递、建结点、拼列表；对 mini-C 已经够用 |
| 关键字识别 | 关键字作为普通规则写在 `IDENT` 之前，靠最长匹配加优先级区分 | 先识别成标识符再查关键字表：需要在生成器里加语言专有的特例 | 无 |
| IR 的产生 | 自己拼 LLVM IR 文本 | `llvmlite`：是第三方依赖，且由库代劳，不利于原创性说明 | 需自己保证 IR 合法；已用样例在本机 clang 实测 |
| 优化与机器码 | 调用 `clang`，它同时承担优化、汇编和链接 | `opt` + `llc` + 链接器：本机未安装，且三步的环境要求更高 | 依赖 clang 15 及以上（H10） |
| AST 可视化 | 自己算布局，输出内嵌 SVG 的 HTML | 调用 Graphviz：本机未装，答辩用机也不一定有 | 布局是简单的子树宽度法，不追求最紧凑 |
| 测试框架 | 标准库 `unittest`，方法名含 `acNN` 以便用 `-k` 按 AC 筛选 | pytest：本机未安装，且是第三方依赖 | 断言写法稍啰嗦 |

参考依据：课件第 3 章（Thompson 算法、子集法、DFA 化简的划分方法）和“自下而上分析——LR 分析法”一章（LR(1) 项目集与分析表构造、二义文法的冲突消解），2026-11-10 只核对了章节与算法名目；作业要求给出的 LLVM 教程链接（Kaleidoscope 第 3 章）。本轮没有联网查阅 LLVM 语言参考手册，也没有检索开源实现；第 8 节的 IR 写法以本机 clang 的实测为准。实施时如遇到不确定的 IR 语法，应查阅 LLVM LangRef 并把查阅结果记入“实施中的调整”。

## 13. 验证安排与资源

- 测试组织：`tests/` 下按模块分文件，每个测试方法名含它所验证的 AC 编号，例如 `test_ac03_regex_accepts_and_rejects`。因此 `python3 -m unittest discover -s tests -k ac03 -v` 只运行 AC03 的用例，checklist 的复核命令都用这种形式。
- 测试隔离：需要分析器的测试在模块级 `setUpModule` 中调用 `ccgen` 把分析器生成到 `tempfile.TemporaryDirectory()`，编译产物也写到临时目录。测试不读写 `build/`、`out/`。
- 样例：全部来自 spec“样例文件”和“运行样例”，由实现阶段按原文创建到 `examples/`、`tests/fixtures/`。位置断言依赖文件内容逐字符一致，创建后不得重新排版。
- 正常、边界、失败的覆盖：正常路径为 AC01、AC02、AC05、AC10、AC14–AC16、AC20、AC22；边界为 AC03、AC04、AC11、AC16 中的回绕和空循环；失败为 AC06、AC08、AC09、AC12、AC13、AC17。
- 依赖 clang 的测试（AC15、AC16，以及 AC22 的演示脚本）在找不到 clang 时用 `unittest.skipUnless` 跳过并写明原因。跳过不等于通过：这些 AC 必须在有 clang 的机器上实际运行后才能勾选。
- 人工检查：AC18 需要人在浏览器中离线打开 `ast.html` 目视确认，自动化测试只能核对结构。
- 预算与默认参数：生成 mini-C 分析器 5 秒内，全部测试 60 秒内。这是预算，不是实测。
- 实测记录：未执行。实施后填写实际环境、耗时与证据位置。

## 14. 实施中的调整

- 2026-11-10（实施前）：当前 shell 的 `python3` 是 3.14.6，另有 `/Users/aqua_night/.local/bin/python3.11`（3.11.15）。本轮检查用临时 PATH 让 `python3` 指向 3.11.15，不修改系统或 Git 配置；日志记录版本。影响 R27 / AC21、H11；另在收尾核对默认 Python 的运行。
- 2026-11-10（实施前）：5.1 的 `fixed` 语法判定只是充分条件；`[a]`、`a|a` 也只匹配一个固定串。按 R07 对正规式树递归求唯一字符串（选择分支须相同、字符集合须单元素），保留 R07 的原始语义并增加测试。影响 R07 / AC05，不改 spec。
- 2026-11-10（实施前）：T1-04 的 AC14 要求比较 `ast.html`，但原阶段表将其首次实现放在 T1-05。把 `minic/astviz.py` 随 T1-03 前端产物落盘一起实现；T1-05 仍负责其专项测试及构造报告。这样各阶段验收无需跳过断言。影响 R21、R22、R29 / AC13、AC14、AC18；人工 AC18 仍由用户完成。
- 2026-11-10（实施前）：10.2 要求九节，合写 ACTION/GOTO 时实际只列八项；将 ACTION 与 GOTO 分为相邻两节，共九节，保留 R23 全部内容和顺序。影响 R23 / AC19。


- 2026-11-10（T1-02 环境复核）：zsh 启动脚本会重设继承的 PATH，阶段日志脚本改为启动后显式 export，再读取实际 `python3 --version`。T1-01 的首次直接测试在 3.11 上通过，日志采集在 3.14 上通过；现重跑 3.11 并修正日志，不改写已有提交。影响 R27 / AC21 的环境证据。

- 2026-11-10（T1-04 参考核对）：查阅 [LLVM LangRef](https://llvm.org/docs/LangRef.html) 的 `call`、`add`、`sdiv`：保持完整可变参数签名、不加 `nsw`、用有符号除法；没有改变翻译方案。检索 LLVM 上游 `llvm/test/CodeGen/Generic/print-arith-int.ll` 对照指令形状，GitHub 页面抓取失败，检索返回的上游镜像可见同类用法；未复制任何外部代码，无新增依赖。后端以产物目录为 cwd、向 clang 传文件名，避免优化 IR 的 ModuleID 含不同临时输出路径。影响 R16–R20、R29 / AC14–AC17。

- 2026-11-10（T1-06 收尾）：按既有 5.1 补齐 NFA 的广度优先编号；修复 `%prefer` 引用未定义记号时应报告声明实际行号，增加 AC09 回归；未更改规则/AC。最终 3.11.15 与 3.14.6 各 41 tests 全通过（无跳过）；日志在 `evidence/`。`sdiv` 的 `INT_MIN / -1` 属运行时未定义边界，按设计继续使用 i32 sdiv，未增加运行时检查；README 明示该限制，请评审者核对 R18 / AC16 的边界表述。
