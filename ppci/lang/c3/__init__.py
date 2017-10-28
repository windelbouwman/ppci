""" This is the c3 language front end.

For the front-end a recursive descent parser is created.

.. graphviz::

   digraph c3 {
   rankdir="LR"
   1 [label="source text"]
   10 [label="lexer" ]
   20 [label="parser" ]
   40 [label="code generation"]
   99 [label="IR-code object"]
   1 -> 10
   10 -> 20
   20 -> 40
   40 -> 99
   }

.. autoclass:: ppci.lang.c3.C3Builder

.. autoclass:: ppci.lang.c3.Lexer

.. autoclass:: ppci.lang.c3.Parser

.. autoclass:: ppci.lang.c3.CodeGenerator

"""


from .parser import Parser
from .lexer import Lexer
from .codegenerator import CodeGenerator
from .visitor import Visitor
from .visitor import AstPrinter
from .builder import C3Builder
from .context import Context

__all__ = [
    'AstPrinter', 'C3Builder', 'CodeGenerator', 'Context', 'Lexer', 'Parser',
    'Visitor']
