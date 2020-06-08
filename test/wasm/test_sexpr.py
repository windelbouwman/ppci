""" Tests for the S-expression parser.
"""

from pytest import raises

from ppci.wasm.components import parse_sexpr
from ppci.common import CompilerError

TEXT = """
(module
  (import "js" "memory" (memory 1))
  (import "js" "table" (table 1 funcref))
  (elem (i32.const 0) $shared0func)
  (func $shared0func (result i32)
   i32.const 0
   i32.load)
  (foo 3.2)
)
"""

TUPLE = ('module',
            ('import', "js", "memory", ("memory", 1)),
            ('import', "js", "table", ("table", 1, "funcref")),
            ('elem', ("i32.const", 0), "$shared0func"),
            ('func', "$shared0func", ('result', "i32"),
            "i32.const", 0, "i32.load"),
            ('foo', 3.2),
        )

def test_basic():

    tuple = parse_sexpr(TEXT)
    assert tuple == TUPLE


def test_numbers():

    v = parse_sexpr('(foo 42)')[1]
    assert v == 42 and isinstance(v, int)
    v = parse_sexpr('(foo 42.1)')[1]
    assert v == 42.1 and isinstance(v, float)
    v = parse_sexpr('(foo 42.0)')[1]
    assert v == 42 and isinstance(v, float)
    v = parse_sexpr('(foo 42e0)')[1]
    assert v == 42 and isinstance(v, float)

    assert parse_sexpr('(foo .2)')[1] == 0.2
    assert parse_sexpr('(foo -.2)')[1] == -0.2
    assert parse_sexpr('(foo +.2)')[1] == 0.2


def test_strings():

    assert parse_sexpr('(foo "2")')[1] == "2"
    assert parse_sexpr(r'(foo "\00")')[1] == r"\00"
    assert parse_sexpr(r'(foo "\"x")')[1] == "\\\"x"
    assert parse_sexpr(r'(foo "\\")')[1] == "\\\\"


def test_whitespace_and_comment():

    assert parse_sexpr("(foo  \t\r\t  3)") == ('foo', 3)
    assert parse_sexpr("(foo  ;;4 bla\n 3)") == ('foo', 3)
    assert parse_sexpr("(foo 3) ;;4 bla :) :) 5") == ('foo', 3)
    assert parse_sexpr("(foo  (;4;) 3)") == ('foo', 3)
    assert parse_sexpr("(foo  (;4 (; 5 ;) 6;) 3)") == ('foo', 3)


def test_fail():

    # Unterminated
    with raises(CompilerError):
        parse_sexpr('(foo 3')

    # Stuff after terminated
    with raises(CompilerError):
        parse_sexpr('(foo 3) xx')
    with raises(ValueError):
        parse_sexpr('(foo 3) (bar 4)')
    with raises(CompilerError):
        parse_sexpr('(foo 3) ;; xx\n xx')
    with raises(CompilerError):
        parse_sexpr('(foo 3) (; xx ;) xx')

    # But this is ok
    assert parse_sexpr("(foo 3) (; (nomore 4) ;)") == ('foo', 3)
    assert parse_sexpr("(foo 3) ;; (nomore 3) :)") == ('foo', 3)


if __name__ == '__main__':
    test_basic()
    test_numbers()
    test_strings()
    test_whitespace_and_comment()
    test_fail()
