
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
