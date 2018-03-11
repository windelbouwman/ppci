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

"""


from .parser import Parser
from .lexer import Lexer
from .codegenerator import CodeGenerator
from .visitor import Visitor
from .visitor import AstPrinter
from .builder import C3Builder, c3_to_ir
from .context import Context

__all__ = [
    'AstPrinter', 'C3Builder', 'CodeGenerator', 'Context', 'Lexer', 'Parser',
    'Visitor', 'c3_to_ir']
