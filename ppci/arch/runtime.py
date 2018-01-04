""" Runtime libraries for operations that some platforms do not supprt.

Examples of these are functions like __divsi3. This function performs a
signed integer division.

The same naming conventions are used as in gcc.

https://gcc.gnu.org/onlinedocs/gccint/Integer-library-routines.html
"""

import io


def get_runtime_files(names):
    """ Get a list of files with the required names.

    For example:

        get_runtime_files(['__divsi3', '__udivsi3'])

    """
    files = []
    files.append(io.StringIO(RT_MUL_C3_SRC))
    files.append(io.StringIO(RT_DIV_C3_SRC))
    return files


RT_MUL_C3_SRC = """
module runtime;

function int mulsi3(int a, int b)
{
  return mul_helper(a, b);
}

function int umulsi3(int a, int b)
{
  return mul_helper(a, b);
}

function int mul_helper(int a, int b)
{
  var int res = 0;
  while (b > 0)
  {
    if ((b & 1) == 1)
    {
      res += a;
    }
    a = a << 1;
    b = b >> 1;
  }
  return res;
}

"""

RT_DIV_C3_SRC = """
module runtime;

function int divsi3(int a, int b)
{
  return udiv_helper(a, b, 0);
}

function int udivsi3(int a, int b)
{
  return udiv_helper(a, b, 0);
}

function int modsi3(int a, int b)
{
  return udiv_helper(a, b, 1);
}

function int umodsi3(int a, int b)
{
  return udiv_helper(a, b, 1);
}

function int udiv_helper(int num, int den, int remainder)
{
  var int res = 0;
  var int current = 1;

  while (den < num)
  {
    den = den << 1;
    current = current << 1;
  }

  while (current != 0)
  {
    if (num >= den)
    {
      num -= den;
      res = res | current;
    }
    den = den >> 1;
    current = current >> 1;
  }

  // Return remainer if needed:
  if (remainder != 0)
  {
    res = num;
  }

  return res;
}

"""
