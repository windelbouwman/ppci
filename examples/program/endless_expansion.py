
"""
Test if a program can be expanded endlessly by going ir->wasm->ir->wasm-> ...
"""


from ppci.programs import PythonProgram  # or ppci.lang.python.PythonCode


py3 = """
a = 2
b = 3
c = a + b
"""

prog = PythonProgram(py3)
for i in range(10):
    prog = prog.to_wasm().to_ir()
    print('Iteration:', i, 'ir code stats:', prog.items[0].stats())
