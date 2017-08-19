
Jitting
=======

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
        return sum(x * y for x,y in zip(a, b))

This code calculates the sum of the product of all element pairs:

.. doctest:: jitting

    >>> x([1,2,3], [5,4,9])
    40

Now, after profiling we could potentially discover that this function is
a major bottleneck. So we decide to rewrite the thing in C:

.. code-block:: c

    int x(int *a, int *b, int count)
    {
      int sum = 0;
      int i;
      for (i = 0; i < count; i++)
      {
      }
    }

Having this function, we put this function in a python string and compile it.

.. doctest:: jitting

    >>> from ppci.api import cc, get_current_platform
    >>> import io
    >>> src = io.StringIO("""
    ... int x(int *a, int *b, int count)
    ... {
    ...   int sum = 0;
    ...   int i;
    ...   for (i = 0; i < count; i++)
    ...   {
    ...     sum += a[i] * b[i];
    ...   }
    ...   return sum;
    ... }""")
    >>> arch = get_current_platform()
    >>> obj = cc(src, arch, debug=True)
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

Now, lets call the function. For this we need some ctypes extras:

.. doctest:: jitting

    >>> import ctypes
    >>> T = ctypes.c_int * 3
    >>> a = T()
    >>> b = T()
    >>> ap = ctypes.cast(a, ctypes.POINTER(ctypes.c_int))
    >>> bp = ctypes.cast(b, ctypes.POINTER(ctypes.c_int))
    >>> s = m.x(ap, bp, 3)
    >>> s
    40

.. warning::
    Before optimizing anything, run a profiler. Your
    expectations about performance bottlenecks might be wrong!

