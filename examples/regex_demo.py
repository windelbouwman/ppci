""" Demonstrate how to build scanners using regular expression
derivatives.

See also:

https://en.wikipedia.org/wiki/Brzozowski_derivative

And:

https://github.com/MichaelPaddon/epsilon

"""

from ppci.lang.tools.regex import compile, scan

r = compile('[0-9]+hi')

print('state machine', r)

for m in scan(r, '1234hi77hi88hi'):
    print('match', m)

