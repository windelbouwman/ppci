"""
Test if a program can be expanded endlessly by going ir->wasm->ir->wasm-> ...
"""

import logging

from ppci.programs import PythonProgram  # or ppci.lang.python.PythonCode

logging.basicConfig(level=logging.DEBUG)

py3 = """
a = 2
b = 3
c = a + b
# print(c)
"""

prog = PythonProgram(py3)
for i in range(
    7
):  # todo: With more cycles there is a recursionerror in dagsplit.py
    print(prog.get_report())
    prog = prog.to_wasm()
    print(prog.get_report())
    prog = prog.to_ir()
    # prog.optimize(level=2)
    print(prog.get_report())
    print("Iteration:", i, "ir code stats:", prog.items[0].stats())
