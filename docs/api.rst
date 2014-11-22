
API
===

Instead of using the commandline, it is also possible to use the build
functions of ppci via the buildfunctions.

For example to assemble, compile, link and objcopy, code could look like:

.. code-block:: python
   :linenos:

    march = "thumb"
    o1 = assemble('start.asm', march)
    o2 = c3compile(['source_code.c3'], [], march)
    o3 = link([o2, o1], 'mem.ld', march)
    objcopy(o3, 'code', 'bin', 'output.bin')


buildfunctions module
---------------------

.. automodule:: ppci.buildfunctions
   :members:

ir
--

.. automodule:: ppci.ir
   :members:

c3
--

.. automodule:: ppci.c3
   :members:

.. automodule:: ppci.c3.parser
   :members:

ppci
----

.. automodule:: ppci
   :members:
   :undoc-members:
