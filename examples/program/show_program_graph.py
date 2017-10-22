""" Show graph structure of how programs can be compiled into one another,
using Matplotlib.
"""

from ppci.programs import create_program_graph

import networkx as nx

# Draw in shell, does not work
# nx.draw_shell(COMPILER_GRAPH, with_labels=True)
g = create_program_graph()
print(g.nodes())
print(g.edges())

# Draw with mpl
import matplotlib.pyplot as plt
nx.draw_circular(g, with_labels=True, node_color=(0.7, 0.7, 1.0))
plt.show()

