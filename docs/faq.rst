
Faq
===

*Why did you do this?*

    There are several reasons:

    * it is possible! (For me, this already is a sufficient explanation :))
    * this compiler is very portable due to python being portable.
    * writing a compiler is a very challenging task

*Is this compiler slower than compilers written in C/C++?*

    Yes. Although a comparison is not yet done, this will be the
    case, due to the overhead and slower execution of python code.

*Cool project, I want to contribute to this project, what can I do?*

    Great! Please :doc:`see this page<contributing/support>`.
    If you are not sure where to begin, please contact me first.
    For a list of tasks, refer to :doc:`the todo page<contributing/todo>`. For hints on 
    development see :doc:`the development page<contributing/development>`.


*Why would one want to make a compiler for such a weird language such as C?*

    Because of the enormous amount of C-source code available. This serves
    as a great test suite for the compiler.

*Why are the so many different parts in ppci, should you not better split
this package into several smaller ones?*

   This would certainly be possible, but for now I would like to keep all
   code in a single package. This simplifies the dependencies, and also
   ensures that a single version works as a whole. Another benefit is that
   the packaging overhead is reduced. Also, functionality can be easily
   shared (but should not lead to spaghetti code of course).
