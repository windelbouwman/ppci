from .transform import FunctionPass
from .ir import Alloc, Load, Store, Phi, i32, Undefined
from .domtree import CfgInfo


def is_alloc_promotable(alloc_inst):
    """ Check if alloc value is only used by load and store operations. """
    # TODO: check that all load and stores are 32 bits and the alloc is 
    # 4 bytes.
    assert type(alloc_inst) is Alloc
    if alloc_inst.amount != 4:
        return False
    if len(alloc_inst.used_by) == 0:
        return False
    if not all(type(use) in [Load, Store] for use in alloc_inst.used_by):
        return False
    loads = [i for i in alloc_inst.used_by if isinstance(i, Load)]
    stores = [i for i in alloc_inst.used_by if isinstance(i, Store)]

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

        # Step 1: place phi-functions where required:
        # Each node in the df(x) requires a phi function, where x is a block where the variable is defined.
        defining_blocks = set(st.block for st in stores)

        # Create worklist:
        W = set(defining_blocks)
        has_phi = set()
        phis = list()
        while W:
            x = W.pop()
            for y in cfg_info.df[x]:
                if y not in has_phi:
                    has_phi.add(y)
                    W.add(y)
                    phi_name = "phi_{}".format(name)
                    phi = Phi(phi_name, phi_ty)
                    phis.append(phi)
                    # self.logger.debug('Adding phi-node {} to {}'.format(phi, y))
                    y.insert_instruction(phi)

        # Create undefined value at start:
        initial_value = Undefined('undef_{}'.format(name), phi_ty)
        cfg_info.f.entry.insert_instruction(initial_value)
        # Step 2: renaming:

        # Start a top down sweep over the dominator tree to visit all statements
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
            # For all successors with phi functions, insert the proper variable:
            for y in cfg_info.succ[b]:
                for phi in (p for p in phis if p.block == y):
                    phi.set_incoming(b, stack[-1])

            # Recurse into children:
            for y in cfg_info.children(b):
                search(y)

            # Cleanup stack:
            for _ in range(defs):
                stack.pop(-1)

        search(cfg_info.f.entry)

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

    def onFunction(self, f):
        self.cfg_info = CfgInfo(f)
        for block in f.blocks:
            allocs = [i for i in block if isinstance(i, Alloc)]
            for alloc_inst in allocs:
                if is_alloc_promotable(alloc_inst):
                    self.promote(alloc_inst, self.cfg_info)
