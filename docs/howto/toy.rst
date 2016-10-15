

Creating a toy language
=======================

In this how-to, we will develop our own toy language. We will use textx to
define our own language and use the ppci backend for optimization and code
generation.

As an example we will create a simple language that can calculate simple
expressions and use variables. An example of this toy language looks like
this:

.. code::

    b = 2;
    c = 5 + 5 * b;
    d = 133 * c - b;
    print b;
    print c;


The language is very limited (which makes it easy to implement), but it
contains enough for an example. The example above is stored in a file called
'example.tcf' (tcf stands for toy calculator format).

Part 0 - preparation
--------------------

Before we can begin creating the toy language compiler, we need the required
dependencies. For that a virtualenv can be created like this:

.. code:: bash

    [windel@hoefnix toydsl]$ virtualenv dslenv
    Using base prefix '/usr'
    New python executable in /home/windel/HG/ppci/examples/toydsl/dslenv/bin/python3
    Also creating executable in /home/windel/HG/ppci/examples/toydsl/dslenv/bin/python
    Installing setuptools, pip, wheel...done.
    [windel@hoefnix toydsl]$ source dslenv/bin/activate
    (dslenv) [windel@hoefnix toydsl]$ pip install textx ppci
    Collecting textx
    Collecting ppci
      Using cached ppci-0.5-py3-none-any.whl
    Collecting Arpeggio (from textx)
    Installing collected packages: Arpeggio, textx, ppci
    Successfully installed Arpeggio-1.5 ppci-0.5 textx-1.4
    (dslenv) [windel@hoefnix toydsl]$

After this step, we now have a virtual environment with textx and ppci
installed.

Part 1 - textx
--------------

In this part the parsing of the language will be done. A great deal will be
done by textx.
For a detailed
explanation of the workings of textx, please see:
http://igordejanovic.net/textX/

Lets define a grammar file, called toy.tx:

.. code::

    Program: statements*=Statement;
    Statement: (PrintStatement | AssignmentStatement) ';';
    PrintStatement: 'print' var=ID;
    AssignmentStatement: var=ID '=' expr=Expression;
    Expression: Sum;
    Sum: Product (('+'|'-') Product)*;
    Product: Value ('*' Value)*;
    Value: ID | INT | ('(' Expression ')');

This grammar is able to parse our toy language. Next we create a python
script to load this grammar and parse the toy example program:

.. code:: python

    from textx.metamodel import metamodel_from_file

    toy_mm = metamodel_from_file('toy.tx')

    # Load the program:
    program = toy_mm.model_from_file('example.tcf')

    for statement in program.statements:
        print(statement)

Now if we run this file, we see the following:

.. code:: bash

    (dslenv) [windel@hoefnix toydsl]$ python toy.py 
    <textx:AssignmentStatement object at 0x7f20c9d87cc0>
    <textx:AssignmentStatement object at 0x7f20c9d87908>
    <textx:AssignmentStatement object at 0x7f20c9d870b8>
    <textx:PrintStatement object at 0x7f20c9d87ac8>
    <textx:PrintStatement object at 0x7f20c9d95588>

We now have a simple parser for the toy language, and can parse it.

Part 2 - connecting the backend
-------------------------------

Now that we can parse the dsl, it is time to create new code from the parsed
format. To generate code, first the program must be translated to ir code.

The following snippet creates an IR-module, a procedure and a block to
store instructions in. Instructions at this point are not machine instructions
but abstract instructions that can be translated into any kind of machine
code later on.

.. code:: python

    from ppci import ir
    ir_module = ir.Module('toy')
    ir_function = ir.Procedure('toy')
    ir_module.add_function(ir_function)
    ir_block = ir.Block('entry')
    ir_function.entry = ir_block
    ir_function.add_block(ir_block)


Next, we need to translate each statement into some code, but we will do that
later.

.. code:: python

    for statement in program.statements:
        print(statement)

First we will add the closing code, that verifies our own constructed
module, and compiles the ir code to object code, links this and creates an
oj file.

.. code:: python

    ir_block.add_instruction(ir.Exit())

The code above creates an Exit instruction and adds the instruction to the
block. Next we can verify the IR-code, to make sure that the program we
created contains no errors. The ir_to_object function translates the program
from IR-code into an object for the given target architecture, in this case
x86_64, but you could as well use AVR or riscv here.

.. code:: python

    Verifier().verify(ir_module)
    obj1 = api.ir_to_object([ir_module], 'x86_64')
    obj = api.link([obj1])
    print(obj)

The printed object shows that it conains 11 bytes.

.. code:: bash

    (dslenv) [windel@hoefnix toydsl]$ python toy.py
    ...
    CodeObject of 11 bytes
    (dslenv) [windel@hoefnix toydsl]$

We can write the object to file using the following code:

.. code:: python

    with open('example.oj', 'w') as f:
        obj.save(f)

The oj file is a ppci format for object files, pronounced 'ojee'. It is
a readable json format with the object information in it:

.. code:: json

    {
      "arch": "x86_64",
      "images": [],
      "relocations": [
        {
          "offset": "0x4",
          "section": "code",
          "symbol": "toy_toy_epilog",
          "type": "apply_b_jmp32"
        }
      ],
      "sections": [
        {
          "address": "0x0",
          "alignment": "0x4",
          "data": "",
          "name": "data"
        },
        {
          "address": "0x0",
          "alignment": "0x4",
          "data": "55488bece9000000005dc3",
          "name": "code"
        }
      ],
      "symbols": [
        {
          "name": "toy_toy",
          "section": "code",
          "value": "0x0"
        },
        {
          "name": "toy_toy_block_entry",
          "section": "code",
          "value": "0x4"
        },
        {
          "name": "toy_toy_epilog",
          "section": "code",
          "value": "0x9"
        }
      ]
    }

As you can see, there are two sections, for code and for data. The code
section contains some bytes. This is x86_64 machine code.

Part 3 - translating the elements
---------------------------------

In this part we will create code snippets for each type of TCF code. For this
we will use the textx context processor system, and we will also rewrite the
initial code such that we have a class that can translate TCF code into
IR-code. The entry point to the class will be a compile member function
that translates a TCF file into a IR-module.

The whole script now looks like this:

.. code:: python

    import logging
    from textx.metamodel import metamodel_from_file
    from ppci import ir
    from ppci.irutils import Verifier
    from ppci import api


    class TcfCompiler:
        """ Compiler for the Tcf language """
        logger = logging.getLogger('tcfcompiler')

        def __init__(self):
            self.int_size = 8
            self.int_type = ir.i64
            self.toy_mm = metamodel_from_file('toy.tx')
            self.toy_mm.register_obj_processors({
                'PrintStatement': self.handle_print,
                'AssignmentStatement': self.handle_assignment,
                'Expression': self.handle_expression,
                'Sum': self.handle_sum,
                'Product': self.handle_product,
                })

        def compile(self, filename):
            self.variables = {}

            # Prepare the module:
            ir_module = ir.Module('toy')
            ir_function = ir.Procedure('toy')
            ir_module.add_function(ir_function)
            self.ir_block = ir.Block('entry')
            ir_function.entry = self.ir_block
            ir_function.add_block(self.ir_block)

            # Load the program:
            self.toy_mm.model_from_file('example.tcf')

            # Close the procedure:
            self.emit(ir.Exit())

            Verifier().verify(ir_module)
            return ir_module

        def emit(self, instruction):
            self.ir_block.add_instruction(instruction)
            return instruction

        def handle_print(self, print_statement):
            self.logger.debug('print statement %s', print_statement.var)
            name = print_statement.var
            value = self.load_var(name)
            self.emit(ir.ProcedureCall('io_print', [value]))

        def handle_assignment(self, assignment):
            self.logger.debug(
                'assign %s = %s', assignment.var, assignment.expr)
            name = assignment.var
            assert isinstance(name, str)

            # Create the variable on stack, if not already present:
            if name not in self.variables:
                self.variables[name] = self.emit(ir.Alloc(name, self.int_size))
            mem_loc = self.variables[name]
            value = assignment.expr.ir_value
            self.emit(ir.Store(value, mem_loc))

        def handle_expression(self, expr):
            self.logger.debug('expression')
            expr.ir_value = expr.val.ir_value

        def handle_sum(self, sum):
            """ Process a sum element """
            self.logger.debug('sum')
            lhs = sum.base.ir_value
            for term in sum.terms:
                op = term.operator
                rhs = term.value.ir_value
                lhs = self.emit(ir.Binop(lhs, op, rhs, 'sum', self.int_type))
            sum.ir_value = lhs

        def handle_product(self, product):
            self.logger.debug('product')
            lhs = self.get_value(product.base)
            for factor in product.factors:
                rhs = self.get_value(factor.value)
                lhs = self.emit(ir.Binop(lhs, '*', rhs, 'prod', self.int_type))
            product.ir_value = lhs

        def get_value(self, value):
            if isinstance(value, int):
                ir_value = self.emit(ir.Const(value, 'constant', self.int_type))
            elif isinstance(value, str):
                ir_value = self.load_var(value)
            else:  # It must be an expression!
                ir_value = value.ir_value
            return ir_value

        def load_var(self, var_name):
            mem_loc = self.variables[var_name]
            return self.emit(ir.Load(mem_loc, var_name, self.int_type))


    tcf_compiler = TcfCompiler()
    ir_module = tcf_compiler.compile('example.tcf')

    obj = api.ir_to_object([ir_module], 'x86_64')
    # obj = api.link([obj1], partial_link=True)
    print(obj)
    with open('example.oj', 'w') as f:
        obj.save(f)

And the textx description is modified to include sum and product terms:

.. code::

    Program: statements*=Statement;
    Statement: (PrintStatement | AssignmentStatement) ';';
    PrintStatement: 'print' var=ID;
    AssignmentStatement: var=ID '=' expr=Expression;
    Expression: val=Sum;
    Sum: base=Product terms*=ExtraTerm;
    ExtraTerm: operator=Operator value=Product;
    Operator: '+' | '-';
    Product: base=Value factors*=ExtraFactor;
    ExtraFactor: operator='*' value=Value;
    Value: ID | INT | ('(' Expression ')');


When we run this script, the output is the following:

.. code:: bash

    (dslenv) [windel@hoefnix toydsl]$ python toy.py 
    CodeObject of 117 bytes
    (dslenv) [windel@hoefnix toydsl]$ 

As we can see, the object file has increased in size because we translated
the elements.

Part 4 - Creating a linux executable
------------------------------------

To be continued ....


Final words
-----------

In this tutorial we have seen how to create a simple language.
The entire example for this code can be found in the
examples/toydsl directory.



