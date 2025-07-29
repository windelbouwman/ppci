import logging
from ppci.lang.python import load_py

logging.basicConfig(level=logging.DEBUG)

# Choose between those two:
import demo1

with open("demo1.py", "r") as f:
    m2 = load_py(f)

for x in range(20):
    print(x, m2.a(x, 2), demo1.a(x, 2))
