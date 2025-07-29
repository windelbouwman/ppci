import logging
from ppci.api import cc

logging.basicConfig(level=logging.DEBUG)
with open("main.c", "r") as f:
    obj = cc(f, "x86_64", debug=True)

print("Object file created:", obj)

with open("hello.oj", "w") as f:
    obj.save(f)
