""" This demo is demonstrating the performance boost when code is compiled """

import timeit
import io
from ppci.utils import codepage


def heavy_math(a, b):
    x = a * b + 200
    y = x // 20 + b
    for i in range(10):
        z = y * 4 + x * 2 + a * 3 + b * 8
        y = y + z // 100 + i
    return x + y + z


src = """
module heavy;

function int math(int a, int b)
{
  var int x, y, z, i;
  x = a * b + 200;
  y = x / 20 + b;
  i = 0
  z = 0;
  for (i=0; i<10; i = i+1)
  {
    z = y * 4 + x * 2 + a * 3 + b * 8;
    y = y + z / 100 + i;
  }
  return x + y + z;
}

"""

mod = codepage.load_code_as_module(io.StringIO(src))

for a in range(10):
    x = 7 * a
    y = 13 * a
    assert heavy_math(x, y) == mod.math(x, y), str(x)

def mk_func(f):
    def x():
        for a in range(100):
            f(a, 13)
    return x

f1 = mk_func(heavy_math)
f2 = mk_func(mod.math)

f1()
f2()

print('Python:', timeit.timeit('f1()', globals={'f1': f1}, number=1000))
print('Compiled:', timeit.timeit('f2()', globals={'f2': f2}, number=1000))
