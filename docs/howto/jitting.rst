
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
    >>> arch = api.get_current_platform()
    >>> obj1 = api.cc(src, arch, debug=True)
    >>> obj = api.link([obj1], debug=True)
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
