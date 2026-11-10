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
