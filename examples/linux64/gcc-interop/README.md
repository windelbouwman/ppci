# gcc-interop

This example shows interoperability with a host compiler (the example
name talks about GCC, but it should work with any other full-fledged
host compiler, the only requirement is that is able to process ELF
object files).

The idea is to compile some source files with PPCI (this example uses
C source files, but it can be any other language supported by PPCI),
while other source files - with the host compiler, and perform final
link with the host compiler too. This enables a number of useful
scenarios not yet supported natively by PPCI:

* Accessing functions in the C standard library and other libraries.
* Supporting dynamic linking.
