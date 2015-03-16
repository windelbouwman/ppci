

Introduction
============

The ppci project is a compiler, assembler, linker and build-system written 
entirely in
python. The project contains everything from language front-end to code
generation.
It contains a front-end for the c3 language, can optimize this code
and generate ARM-code.

The project contains the following:

- Language front-ends: Brainfuck, :doc:`c3`
- Various code optimizers
- Backends for various platforms: ARM, Thumb, Python
- Assembler
- Linker


Table of contents
=================

.. toctree::
    :maxdepth: 2

    self
    usage
    c3
    buildxml
    api
    utils
    compiler
    development

