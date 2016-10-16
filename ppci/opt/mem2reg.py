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
    assert type(alloc_inst) is Alloc
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
    if any(mem_op.volatile for mem_op in stores + loads):
        return False

    # Check for types:
    load_types = [load.ty for load in loads]
    store_types = [store.value.ty for store in stores]
    all_types = load_types + store_types
    assert len(all_types) > 0
    if not all(all_types[0] is ty for ty in all_types):
        return False

    # Check that the alloc has the right amount of bytes:
    # phi_type = all_types[0]
    # TODO: re-enable this check, but it requires target knowledge?
    # if alloc_inst.amount != phi_type.byte_size:
    #    return False

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
        block_backlog = set(defining_blocks)

        has_phi = set()

        phis = list()
        idx = 0
        while block_backlog:
            defining_block = block_backlog.pop()
            for frontier_block in cfg_info.df[defining_block]:
                if frontier_block not in has_phi:
                    has_phi.add(frontier_block)
                    block_backlog.add(frontier_block)
                    phi_name = "phi_{}_{}".format(name, idx)
                    idx += 1
                    phi = Phi(phi_name, phi_ty)
                    phis.append(phi)
                    frontier_block.insert_instruction(phi)
        return phis

    def rename(self, initial_value, phis, loads, stores, cfg_info):
        """
        Step 2: renaming:

        Start a top down sweep over the dominator tree to visit all
        statements
        """
        stack = [initial_value]

        def search(block):
            # Crawl down block:
            defs = 0
            for instruction in block:
                if instruction in phis:
                    stack.append(instruction)
                    defs += 1
                if instruction in stores:
                    stack.append(instruction.value)
                    defs += 1
                if instruction in loads:
                    # Replace all uses of a with cur_V
                    instruction.replace_by(stack[-1])
                    aloc = instruction.address
                    assert isinstance(aloc, Alloc)
                    # self.debug_db.map(aloc, stack[-1])

            # At the end of the block
            # For all successors with phi functions, insert the proper
            # variable:
            for y in cfg_info.succ[block]:
                for phi in (p for p in phis if p.block == y):
                    phi.set_incoming(block, stack[-1])

            # Recurse into children:
            for y in cfg_info.children(block):
                search(y)

            # Cleanup stack:
            for _ in range(defs):
                stack.pop(-1)

        search(cfg_info.function.entry)

    def promote(self, alloc: Alloc, cfg_info):
        """ Promote a single alloc instruction.
        Find load operations and replace them with assignments """
        name = alloc.name

        loads = [i for i in alloc.used_by if isinstance(i, Load)]
        stores = [i for i in alloc.used_by if isinstance(i, Store)]

        self.logger.debug('Alloc {} used by {} load and {} stores'.
                          format(alloc, len(loads), len(stores)))

        # Determine the type of the phi node:
        load_types = [load.ty for load in loads]
        store_types = [store.value.ty for store in stores]
        all_types = load_types + store_types
        assert len(all_types) > 0
        phi_ty = all_types[0]

        phis = self.place_phi_nodes(stores, phi_ty, name, cfg_info)

        # Preserve debug info:
        for phi in phis:
            self.debug_db.map(alloc, phi)

        # Create undefined value at start:
        initial_value = Undefined('und_{}'.format(name), phi_ty)
        cfg_info.function.entry.insert_instruction(initial_value)

        self.rename(initial_value, phis, loads, stores, cfg_info)

        # Check that all phis have the proper number of inputs.
        for phi in phis:
            assert len(phi.inputs) == len(cfg_info.pred[phi.block])

        # Remove unused instructions:
        new_instructions = [initial_value] + phis
        while True:
            change = False
            for i in new_instructions:
                if not i.is_used:
                    i.remove_from_block()
                    new_instructions.remove(i)
                    change = True
            if not change:
                break

        # Each store instruction can be removed.
        for store in stores:
            store.remove_from_block()

        # Remove all load instructions:
        for load in loads:
            assert not load.is_used
            load.remove_from_block()

        # Finally the alloc instruction can be deleted:
        assert not alloc.is_used
        alloc.remove_from_block()

    def on_function(self, f):
        cfg_info = CfgInfo(f)
        for block in f.blocks:
            allocs = [i for i in block if isinstance(i, Alloc)]
            for alloc in allocs:
                if is_alloc_promotable(alloc):
                    self.promote(alloc, cfg_info)
