import os
from ppci import api

from ppci.graph import cyclo, callgraph
from ppci.graph.cfg import ir_function_to_graph

sources = [
    os.path.join("src", "hello", "hello.c3"),
    os.path.join("..", "librt", "io.c3"),
    os.path.join("linux64", "bsp.c3"),
]
m = api.c3_to_ir(sources, [], "arm")
print(m)
print(m.stats())

cg = callgraph.mod_to_call_graph(m)
print(cg)

# Print callgraph
for func in m.functions:
    cfg, _ = ir_function_to_graph(func)
    complexity = cyclo.cyclomatic_complexity(cfg)
    print("Function: {}, Complexity: {}".format(func.name, complexity))
