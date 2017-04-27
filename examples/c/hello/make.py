import logging
from ppci.api import cc, COptions

logging.basicConfig(level=logging.DEBUG)
obj = cc('main.c', 'x86_64')
print('Object file created:', obj)
with open('hello.oj', 'w') as f:
    obj.save(f)

