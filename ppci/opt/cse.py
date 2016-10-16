from .transform import BlockPass
from .. import ir


class CommonSubexpressionEliminationPass(BlockPass):
    """
        Replace common sub expressions (cse) with the previously defined one.
    """
    def on_block(self, block):
        ins_map = {}
        stats = 0
        for i in block:
            if isinstance(i, ir.Binop):
                k = (i.a, i.operation, i.b, i.ty)
            elif isinstance(i, ir.Const):
                k = (i.value, i.ty)
            else:  # pragma: no cover
                # This branch is actually covered, but is optimized by
                # the python peep-hole optimizer!
                continue
            if k in ins_map:
                ins_new = ins_map[k]
                i.replace_by(ins_new)
                stats += 1
            else:
                ins_map[k] = i
        if stats > 0:
            self.logger.debug('Replaced %i instructions', stats)
