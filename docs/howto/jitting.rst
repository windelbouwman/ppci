JITting
=======

.. warning::

    This section is a work in progress. It is outlined as to how things
    should work, but it is not thorougly tested. Also, keep in mind
    that C support is very premature. An alternative is C3.

This howto is about how to JIT (just-in-time-compile) code and use it from
Python. It can occur that at some point in time, you have some Python code
that becomes a performance bottleneck. At this point, you have multiple
options:

- Rewrite your code in C/Fortran/Rust/Go/Swift, compile it to machine code
  with GCC or similar compiler and load it with SWIG/ctypes.
- Use PyPy, which contains a built-in JIT functionality. Usually the usage
  of PyPy means more speed.
- Use a specialized JIT engine, like Numba.

In this HowTo we will implement our own specialized JIT engine, using PPCI
as a backend.

To do this, first we need some example code. Take the following function
as an example:

.. testcode:: jitting

    def x(a, b):
        return a + b + 13

This function does some magic calculations :)

.. doctest:: jitting

    >>> x(2, 3)
    18

C-way
-----

Now, after profiling we could potentially discover that this function is
a bottleneck. We may decide to rewrite it in C:

.. code-block:: c

    int x(int a, int b)
    {
      return a + b + 13;
    }

Having this function, we put this function in a Python string and compile it.

.. doctest:: jitting

    >>> from ppci import api
    >>> import io
    >>> src = io.StringIO("""
    ... int x(int a, int b) {
    ...   return a + b + 13;
    ... }""")
    >>> arch = api.get_current_arch()
    >>> obj = api.cc(src, arch, debug=True)
    >>> obj  # doctest: +ELLIPSIS
    CodeObject of ... bytes

Now that the object is compiled, we can load it into the current
Python process:

.. doctest:: jitting

    >>> from ppci.utils.codepage import load_obj
    >>> m = load_obj(obj)
    >>> dir(m)  # doctest: +ELLIPSIS
    [..., 'x']
    >>> m.x  # doctest: +ELLIPSIS
    <CFunctionType object at ...>

Now, lets call the function:

.. doctest:: jitting

    >>> m.x(2, 3)
    18

Python-way
----------

Instead of translating our code to C, we can as well compile
Python code directly, by using type hints and a restricted subset of
the Python language. For this we can use the :mod:`ppci.lang.python` module:


.. doctest:: jitting

    >>> from ppci.lang.python import load_py
    >>> f = io.StringIO("""
    ... def x(a: int, b: int) -> int:
    ...     return a + b + 13
    ... """)
    >>> n = load_py(f)
    >>> n.x(2, 3)
    18

By doing this, we do not need to reimplement the function in C,
but only need to add some type hints to make it work. This might
be more preferable to C. Please note that integer arithmetic is
arbitrary-precision in Python, but witth the compiled code above,
large value will silently wrap around.

To easily compile some of your Python functions to native code,
use the :func:`ppci.lang.python.jit` decorator:

.. testcode:: jitting

    from ppci.lang.python import jit

    @jit
    def y(a: int, b: int) -> int:
        return a + b + 13

Now the function can be called as a normal function, JIT compilation
and calling native code is handled transparently:

.. doctest:: jitting

   >>> y(2, 3)
   18


Calling Python functions from native code
-----------------------------------------

In order to callback Python functions, we can do the following:

.. doctest:: jitting

    >>> def callback_func(x: int) -> None:
    ...     print('x=', x)
    ...
    >>> f = io.StringIO("""
    ... def x(a: int, b: int) -> int:
    ...     func(a+3)
    ...     return a + b + 13
    ... """)
    >>> o = load_py(f, imports={'func': callback_func})
    >>> o.x(2, 3)
    x= 5
    18

Benchmarking and call overheads
-------------------------------

To conclude this section, let's benchmark the original function ``x`` with
which we started this section, and its JIT counterpart:

.. code:: python

    >>> import timeit
    >>> timeit.timeit('x(2,3)', number=100000, globals={'x': x})
    0.015114138000171806
    >>> timeit.timeit('x(2,3)', number=100000, globals={'x': m.x})
    0.07410199400010242

Turns out that the compiled code is actually slower. This is due to
the fact that for a trivial function like that, argument conversion and
call preparation overheads dominate the execution time. To see benefits
of native code execution, we would need to JIT functions which perform
many operations in a loop, e.g. while processing large arrays.

.. warning::
    Before optimizing anything, run a profiler. Your
    expectations about performance bottlenecks might be wrong!
