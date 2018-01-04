
from .utils.cfg import ir_function_to_graph


class CfgInfo:
    """ Calculate control flow graph info, such as dominators
    dominator tree and dominance frontier """
    def __init__(self, function):
        # Store ir related info:
        self.function = function
        self.cfg, self._block_map = ir_function_to_graph(function)
        self._node_map = {n: b for b, n in self._block_map.items()}

        self._calculate_df()

    def __repr__(self):
        return 'CfgInfo(function={})'.format(self.function)

    def get_node(self, block):
        return self._block_map[block]

    def get_block(self, node):
        return self._node_map[node]

    def has_block(self, node):
        return node in self._node_map

    def _calculate_df(self):
        self.cfg.calculate_dominance_frontier()
        self.df = {
            self._node_map[n]: set(
                self.get_block(o) for o in m if self.has_block(o))
            for n, m in self.cfg.df.items()
            if self.has_block(n)
        }
