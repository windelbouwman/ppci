"""Use hypothesis and lark to generate snippets
of sourcecode to test the parser.
"""

from lark import Lark
from hypothesis.extra.lark import from_lark
from hypothesis import given, strategies as st
from ppci.lang.c import parse_text, print_ast
from ppci.common import CompilerError

grammar_text = r"""
start: program

program: declaration+

declaration: vardef
           | funcdef

typ: "int"
   | "float"
   | "void"
   | "double"

vardef: typ ID "=" expr ";"

funcdef: typ ID "(" ")" "{" statement* "}"

statement: assignment
         | if_stmt
         | while_stmt
         | for_stmt
         | compound_stmt

if_stmt: "if" "(" expr ")" statement
while_stmt: "while" "(" expr ")" statement
for_stmt: "for" "(" expr ";" expr ";" expr ")" statement

compound_stmt: "{" statement* "}"

assignment: typ ID "=" expr ";"

expr: NUM
    | expr op expr
    | ID
    | expr "(" expr "," expr ")"

op: "+"
  | "-"
  | "/"
  | "*"
  | "^"
  | "|"
  | "&"

%ignore / +/
%declare NUM ID

"""

grammar = Lark(grammar_text)
explicit = {
    "NUM": st.integers().map(str),
    "ID": st.text(alphabet="abcdefghijUVWXYZ", min_size=6),
}


@given(from_lark(grammar, explicit=explicit))
def test_c(prog):
    """Test various randomly generated slabs of C-ish code."""
    print(prog)
    try:
        ast = parse_text(prog)
    except CompilerError as ex:
        print("Compilation error", ex)
    else:
        print(ast)
        print_ast(ast)


if __name__ == "__main__":
    test_c()
