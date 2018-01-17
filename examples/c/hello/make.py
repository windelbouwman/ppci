import logging
from ppci.api import cc, COptions

logging.basicConfig(level=logging.DEBUG)
with open('main.c', 'r') as f:
    obj = cc(f, 'x86_64')

print('Object file created:', obj)

with open('hello.oj', 'w') as f:
    obj.save(f)

