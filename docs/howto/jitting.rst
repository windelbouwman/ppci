
Jitting
=======

.. warning::

    This section is a work in progress. It is outlined as to how things
    should work, but it is not thorougly tested. Also, keep in mind
    that C support is very premature. An alternative is c3.

This howto is about how to JIT (just-in-time-compile) code and use it from
python. It can occur that at some point in time, you have some python code
that becomes a performance bottleneck. At this point, you have multiple
options:

- Rewrite your code in C/Fortran/Rust/Go/Swift, compile it to machine code
  with gcc and load it with swig/ctypes.
- Use pypy, which contains a built-in JIT function. Usually the usage of pypy
  means more speed.

There are lots of more options, but in this howto we will use ppci to compile
and load a piece of code that forms a bottleneck.

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
a major bottleneck. So we decide to rewrite the thing in C:

.. code-block:: c

    int x(int a, int b)
    {
      return a + b + 13;
    }

Having this function, we put this function in a python string and compile it.

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
python process:

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

Follow-up
---------

Instead of translating our code to C, we can as well compile
python directly, by using type hints and a restricted subset of
the python language. For this we can use the :mod:`ppci.lang.python` module:


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
be more preferable to C. Please note that integer arithmatic is
unlimited on python, but not when using compiled code.

To easily load you code as native code, use the :func:`ppci.lang.python.jit`
function:

.. testcode:: jitting

    from ppci.lang.python import jit

    @jit
    def y(a: int, b: int) -> int:
        return a + b + 13

Now the function can be called as before, except that now native code is
invoked:

.. doctest:: jitting

   >>> y(2, 3)
   18


Calling python functions
------------------------

In order to callback python functions, we can do the following:

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

Benchmarking
------------

Now for an intersting plot twist, lets compare the two functions in a
benchmark:

.. code:: python

    >>> import timeit
    >>> timeit.timeit('x(2,3)', number=100000, globals={'x': x})
    0.015114138000171806
    >>> timeit.timeit('x(2,3)', number=100000, globals={'x': m.x})
    0.07410199400010242

Turns out that the compiled code is actually slower. This can be due to
the overhead of calling C functions or bad compilation.
Lessons learned: first profile, then use pypy, then improve python code,
and lastly: convert your code into C.

.. warning::
    Before optimizing anything, run a profiler. Your
    expectations about performance bottlenecks might be wrong!

