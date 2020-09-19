""" Compare regex execution times.

The python builtin re module performs rather
poorly for some example regular expressions.

Basically recreate the charts listed here:

https://swtch.com/~rsc/regexp/regexp1.html


"""

import time
import re
import contextlib
from ppci.lang.tools import regex
import matplotlib.pyplot as plt

data = {
    'n': [],
    'builtin': [],
    'derivatives': [],
}


@contextlib.contextmanager
def add_bench(name):
    t1 = time.time()
    yield
    t2 = time.time()
    delta = t2 - t1
    data[name].append(delta)


for N in range(2, 17):
    # Construct regex and test text:
    test_pattern = r'a?' * N + r'a' * N
    text = 'a' * N
    print('test pattern:', test_pattern, 'test text:', text)

    # Builtin re module:
    prog = re.compile(test_pattern)
    t1 = time.time()
    with add_bench('builtin'):
        mo = prog.match(text)
    t2 = time.time()
    delta1 = t2 - t1
    print('match', mo)
    print('builtin re: N =', N, 'time =', delta1)

    # with derivatives:
    prog2 = regex.compile(test_pattern)
    print(prog2)
    t1 = time.time()
    with add_bench('derivatives'):
        res = list(regex.scan(prog2, text))
    t2 = time.time()
    delta2 = t2 - t1
    print('match', res)
    print('with derivatives: N =', N, 'time =', delta2)

    print('Speedup', delta1 / delta2)

    # For plot:
    data['n'].append(N)

# Plot the results:
plt.title('Execution time of matching')
plt.plot(data['n'], data['builtin'], label='builtin re module')
plt.plot(data['n'], data['derivatives'], label='using derivatives')
plt.grid()
plt.ylabel('Time [s]')
plt.xlabel('n')
plt.legend()
plt.show()
