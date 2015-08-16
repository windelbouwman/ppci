"""
    This file implements memory to register promotion. When a memory location
    is only used by store and load, the stored value can also be stored
    into a register, to improve performance.
"""

from .transform import FunctionPass
from ..ir import Alloc, Load, Store, Phi, Undefined
from ..domtree import CfgInfo


def is_alloc_promotable(alloc_inst):
    """ Check if alloc value is only used by load and store operations. """
    # TODO: check that all load and stores are 32 bits and the alloc is
    # 4 bytes.
    assert type(alloc_inst) is Alloc
    if alloc_inst.amount != 4:
        return False
    if len(alloc_inst.used_by) == 0:
        return False

    # Check if alloc is only used by load and store instructions:
    if not all(isinstance(use, (Load, Store)) for use in alloc_inst.used_by):
        return False

    # Extract loads and stores:
    loads = [i for i in alloc_inst.used_by if isinstance(i, Load)]
    stores = [i for i in alloc_inst.used_by if isinstance(i, Store)]

    # Check if the alloc is used as a value instead of an address:
    if any(store.value is alloc_inst for store in stores):
        return False

    # Check for volatile:
    if any(store.volatile for store in stores):
        return False
    if any(load.volatile for load in loads):
        return False

    # Check for types:
    load_types = [load.ty for load in loads]
    store_types = [store.value.ty for store in stores]
    all_types = load_types + store_types
    assert len(all_types) > 0
    if not all(all_types[0] is ty for ty in all_types):
        return False
    return True


class Mem2RegPromotor(FunctionPass):
    """ Tries to find alloc instructions only used by load and store
    instructions and replace them with values and phi nodes """

    def place_phi_nodes(self, stores, phi_ty, name, cfg_info):
        """
         Step 1: place phi-functions where required:
         Each node in the df(x) requires a phi function,
         where x is a block where the variable is defined.
        """
        defining_blocks = set(st.block for st in stores)

        # Create worklist:
        W = set(defining_blocks)

        # TODO: hack to prevent phi from being inserted into block at end:
        has_phi = set([cfg_info.function.epilog])

        phis = list()
        while W:
            defining_block = W.pop()
            for frontier_block in cfg_info.df[defining_block]:
                if frontier_block not in has_phi:
                    has_phi.add(frontier_block)
                    W.add(frontier_block)
                    phi_name = "phi_{}".format(name)
                    phi = Phi(phi_name, phi_ty)
                    phis.append(phi)
                    frontier_block.insert_instruction(phi)
        return phis

    def promote(self, alloc_inst, cfg_info):
        """ Promote a single alloc instruction.
        Find load operations and replace them with assignments """
        name = alloc_inst.name
        self.logger.debug('Promoting {} to register'.format(alloc_inst))

        loads = [i for i in alloc_inst.used_by if isinstance(i, Load)]
        stores = [i for i in alloc_inst.used_by if isinstance(i, Store)]

        self.logger.debug('Alloc used by {} load and {} stores'.
                          format(len(loads), len(stores)))

        # Determine the type of the phi node:
        load_types = [load.ty for load in loads]
        store_types = [store.value.ty for store in stores]
        all_types = load_types + store_types
        assert len(all_types) > 0
        phi_ty = all_types[0]

        phis = self.place_phi_nodes(stores, phi_ty, name, cfg_info)

        # Create undefined value at start:
        initial_value = Undefined('undef_{}'.format(name), phi_ty)
        cfg_info.function.entry.insert_instruction(initial_value)
        # Step 2: renaming:

        # Start a top down sweep over the dominator tree to visit all
        # statements
        stack = [initial_value]

        def search(b):
            # Crawl down block:
            defs = 0
            for a in b.Instructions:
                if a in phis:
                    stack.append(a)
                    defs += 1
                if a in stores:
                    stack.append(a.value)
                    defs += 1
                if a in loads:
                    # Replace all uses of a with cur_V
                    a.replace_by(stack[-1])
            # At the end of the block
            # For all successors with phi functions, insert the proper
            # variable:
            for y in cfg_info.succ[b]:
                for phi in (p for p in phis if p.block == y):
                    phi.set_incoming(b, stack[-1])

            # Recurse into children:
            for y in cfg_info.children(b):
                search(y)

            # Cleanup stack:
            for _ in range(defs):
                stack.pop(-1)

        search(cfg_info.function.entry)

        # Check that all phis have the proper number of inputs.
        for phi in phis:
            assert len(phi.inputs) == len(cfg_info.pred[phi.block])

        # Each store instruction can be removed.
        for store in stores:
            # self.logger.debug('Removing {}'.format(store))
            store.remove_from_block()

        # for each load, track back what the defining store
        for load in loads:
            assert not load.is_used
            # self.logger.debug('Removing {}'.format(load))
            load.remove_from_block()

        # Finally the alloc instruction can be deleted:
        assert not alloc_inst.is_used
        alloc_inst.remove_from_block()

    def on_function(self, f):
        self.cfg_info = CfgInfo(f)
        for block in f.blocks:
            allocs = [i for i in block if isinstance(i, Alloc)]
            for alloc_inst in allocs:
                if is_alloc_promotable(alloc_inst):
                    self.promote(alloc_inst, self.cfg_info)
