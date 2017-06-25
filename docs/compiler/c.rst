
C compiler internals
====================

Notes about the c compiler internals.


Overview
--------

.. graphviz::

   digraph x {
   rankdir="LR"
   10 [label="source"]
   20 [label="lexer" ]
   30 [label="preprocessor" ]
   40 [label="output of preprocessor" ]
   41 [label="parser" ]
   50 [label="code generator" ]
   10 -> 20 [label="text"]
   20 -> 30 [label="tokens"]
   30 -> 40 [label="tokens"]
   30 -> 41 [label="tokens"]
   30 -> 10 [label="include"]
   41 -> 50 [label="parsed program"]
   }

The C compilers task is to take C code, and produce intermediate code for
the backend. The first step is pre processing, during which a sequence of
tokens is transformed into another sequence of tokens. Next comes parsing and
code generation. There are two options here: split the parser and code
generation passes, such that there is a clean seperation, or do it all at
once. Maybe the best choice is to do it all in one pass, and transform a
sequence of tokens into IR-code in a single go.

Pre-processor
-------------

The preprocessor is a strange thing. It must
handle trigraphs, backslash newlines
and macros.

The top level design of the preprocessor is the following:

- Context: Contains state that would be global otherwise.
- Lexer: processes a raw file into a sequence of tokens
- Preprocessor: takes the token sequence a does macro expansion,
  resulting in another stream of tokens.
- Output: The token stream maybe outputted to file.
- Feed to compiler: The token stream might be fed into the rest of the
  compiler.

Good resources about preprocessors:

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

C compiler
----------

The c compiler consists of the classical stages: parsing and codegeneration.
Code generation is done to ir-code.

Parsing
~~~~~~~

The C parsing is done by two classes CParser and CSemantics. CParser is
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

Code generation
~~~~~~~~~~~~~~~

Code generation takes the AST as a whole and loops over all its elements and
generates the corresponding IR-code snippets from it. At the end of code
generation, there is an IR module which can be feed into the optimizers or
code generators.

References
----------

Other C compilers
~~~~~~~~~~~~~~~~~


A c99 frontend for libfirm:
https://github.com/libfirm/cparser


tcc
~~~
tcc: tiny c compiler

This compiler is tiny and uses a single pass to parse and generate code.


lcc
~~~

https://github.com/drh/lcc

This compiler does parsing and type checking in one go.


cdt
~~~

CDT is an eclipse c/c++ ide.

http://wiki.eclipse.org/CDT/designs/Overview_of_Parsing

