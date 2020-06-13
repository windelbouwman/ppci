
.. currentmodule:: ppci.lang.c

C compiler
==========

This page describes the design of the C compiler. If you want to use the
compiler, please see :ref:`ppci-cc` or :func:`ppci.api.cc`.

Overview
--------

.. graphviz::

   digraph x {
   codegen [label="code generator" ]
   source -> lexer [label="text"]
   lexer -> preprocessor [label="tokens"]
   preprocessor -> parser [label="tokens"]
   preprocessor -> source [label="include"]
   parser -> semantics [label="callback functions"]
   semantics -> scope
   semantics -> codegen [label="parsed program (AST)"]
   }

The C compilers task is to take C code, and produce intermediate code for
the backend. The first step is pre processing, during which a sequence of
tokens is transformed into another sequence of tokens. Next comes parsing and
code generation. There are two options here: split the parser and code
generation passes, such that there is a clean seperation, or do it all at
once. Maybe the best choice is to do it all in one pass, and transform a
sequence of tokens into IR-code in a single go.

Limitations
-----------

The C compiler has some limitations. This is the list of current
known limitations:

- type qualifiers (const, volatile, etc) are parsed but ignored
- K&R function declarations are not supported
- wide characters are not supported
- VLA is not implemented
- function declarations in function definitions are not allowed

Pre-processor
-------------

The preprocessor is a strange thing. It must
handle trigraphs, backslash newlines
and macros.

The top level design of the preprocessor is the following:

- Context: Contains state that would be global otherwise.
- :class:`CLexer`: processes a raw file into a sequence of tokens
- Preprocessor: takes the token sequence a does macro expansion,
  resulting in another stream of tokens.
- Output: The token stream maybe outputted to file.
- Feed to compiler: The token stream might be fed into the rest of the
  compiler.


C compiler
----------

The c compiler consists of the classical stages: parsing and codegeneration.
Code generation is done to ir-code.

Parsing
~~~~~~~

The C parsing is done by two classes :class:`CParser` and :class:`CSemantics`.
CParser is
a recursive descent parser. It dances a tight dance with the CSemantics class.
This idea is taken from the Clang project. The CParser takes a token sequence
from the preprocessor and matches the C syntax. Whenever a valid C construct
is found, it calls the corresponding function on the CSemantics class. The
semantics class keeps track of the current scope and records the global
declarations. It also check types and lvalues of expressions. At the end of
parsing and this type checking, an abstract syntax tree (AST) is build up.
This AST is type checked and variables are resolved. This AST can be used
for several purposes, for example static code analysis or style checking. It
is also possible to generate C code again from this AST.

L-values
~~~~~~~~

The semantics class determines for each expression node whether it is an lvalue
or not. The lvalue (short for location value) indicates whether the expression
has a memory address, or is a value in a register. Basically it boils down
to: can we take the address of this expression with the '&' operator. Numeric
literals and the results of addition are not lvalues. Variables are lvalues.
The lvalue property is used during code generation to check whether the value
must be loaded from memory or not.

Types
~~~~~

Hosted vs freestanding
~~~~~~~~~~~~~~~~~~~~~~

A C compiler can be hosted or freestanding. The difference between those two
is that a hosted C compiler also provides the standard C library. A
freestanding compiler only contains a few really required header files. As a
result a hosted compiler is really a combination of a C compiler and a
C standard library implementation. Also, the standard library depends on the
operating system which is used, where as a freestanding C compiler can be
used independent of operating system. Writing an application using a hosted
compiler is easier since the standard library is available.

.. graphviz::

   digraph x {
     hosted [label="Hosted C application"]
     freestanding [label="Freestanding C application"]
     os [label="Operating system"]
     libc [label="C standard library"]
     compiler [label="C compiler"]
     hosted -> libc
     freestanding -> compiler
     libc -> os
     libc -> compiler
   }


Code generation
~~~~~~~~~~~~~~~

Code generation takes the AST as a whole and loops over all its elements and
generates the corresponding IR-code snippets from it. At the end of code
generation, there is an IR module which can be feed into the optimizers or
code generators.

C classes
---------

The C frontend can be used to generate an AST from C code. You can use
it to parse C code and analyze its structure like this:

.. doctest::

    >>> from ppci.api import get_arch
    >>> from ppci.lang.c import create_ast
    >>> src = "int a, *b;"
    >>> ast = create_ast(src, get_arch('msp430').info)
    >>> ast
    Compilation unit with 2 declarations
    >>> from ppci.lang.c import CAstPrinter
    >>> printer = CAstPrinter()
    >>> printer.print(ast)
    Compilation unit with 2 declarations
        Variable [storage=None typ=Basic type int name=a]
            Basic type int
        Variable [storage=None typ=Pointer-type name=b]
            Pointer-type
                Basic type int
    >>> ast.declarations[0].name
    'a'


Module reference
----------------

.. automodule:: ppci.lang.c
    :members:


Uml
---

.. uml:: ppci.lang.c.nodes.types

.. uml:: ppci.lang.c.nodes.expressions

.. uml:: ppci.lang.c.nodes.statements

.. uml:: ppci.lang.c.nodes.declarations

References
----------

This section contains some links to other compilers. These were used to draw
inspiration from. In the spirit of: it is better to steal ideas then invent
something bad yourself :).

Other C compilers
~~~~~~~~~~~~~~~~~

A c99 frontend for libfirm:
https://github.com/libfirm/cparser


tcc

tcc: tiny c compiler

This compiler is tiny and uses a single pass to parse and generate code.


lcc

https://github.com/drh/lcc

This compiler does parsing and type checking in one go.


cdt

CDT is an eclipse c/c++ ide.

http://wiki.eclipse.org/CDT/designs/Overview_of_Parsing

Good resources about preprocessors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cpp internal description:

https://gcc.gnu.org/onlinedocs/cppinternals/

A portable C preprocessor:

http://mcpp.sourceforge.net


The boost wave preprocessor:

http://www.boost.org/doc/libs/1_63_0/libs/wave/

A java implementation of the preprocessor:

http://www.anarres.org/projects/jcpp/

https://github.com/shevek/jcpp


CDT preprocessor:
http://git.eclipse.org/c/cdt/org.eclipse.cdt.git/tree/core/org.eclipse.cdt.core/parser/org/eclipse/cdt/internal/core/parser/scanner/CPreprocessor.java

The lcc preprocessor part:

https://github.com/drh/lcc/blob/master/cpp/cpp.h

