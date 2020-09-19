""" Demonstrate how to build scanners using regular expression
derivatives.

See also:

https://en.wikipedia.org/wiki/Brzozowski_derivative

And:

https://github.com/MichaelPaddon/epsilon

"""

import io
from ppci.lang.tools.regex import compile, scan, make_scanner, generate_code

r = compile('[0-9]+hi')

print('state machine', r)

for m in scan(r, '1234hi77hi88hi9hi'):
    print('match', m)

f = io.StringIO()
generate_code(r, f)
print('================= C code ===============')
print(f.getvalue())
print('================= C code ===============')

# Scanner demo:
token_definitions = {
    'identifier': '[a-z]+',
    'space': ' +',
    'operator': r'[=\-\+]',
    'number': '[0-9]+',
}
scanner = make_scanner(token_definitions)
text = 'bla = 99 + fu - 1'
print('Lexing this text:', text)
tokens = scanner.scan(text)
for token in tokens:
    print(token)
