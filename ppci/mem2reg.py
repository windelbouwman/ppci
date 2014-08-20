from .transform import FunctionPass
from .ir import Alloc, Load, Store


def isAllocPromotable(allocinst):
    """ Check if alloc value is only used by load and store operations. """
    # TODO: check that all load and stores are 32 bits and the alloc is 
    # 4 bytes.
    assert type(allocinst) is Alloc
    if allocinst.amount != 4:
        return False
    if len(allocinst.used_by) == 0:
        return False
    return all(type(use) in [Load, Store] for use in allocinst.used_by)


class Mem2RegPromotor(FunctionPass):
    """ Tries to find alloc instructions only used by load and store
    instructions and replace them with values and phi nodes """
    def promoteSingleBlock(self, alloc_inst):
        """ Simple case in which no phi nodes need be placed """
        block = alloc_inst.block

        # Replace all loads with the value:
        loads = [i for i in v.used_by if isinstance(i, Load)]
        stores = [i for i in v.used_by if isinstance(i, Store)]
        stores.sort(key=lambda s: s.Position)
        stores.reverse()

        for load in loads:
            idx = load.Position
            # Search upwards:
            for store in stores:
                if store.Position < load.Position:
                    break
            load.value.replaceby(store.value)
            self.logger.debug('replaced {} with {}'.format(load, store.value))
            block.removeInstruction(load)

        # Remove store instructions:
        for store in stores:
            sv = store.value
            self.logger.debug('removing {}'.format(store))
            block.remove_instruction(store)
            # assert sv.Used

        # Remove alloca instruction:
        assert not ai.value.Used, ai.value.used_by
        block.removeInstruction(alloc_inst)

    def promote(self, alloc_inst):
        """ Promote a single alloc instruction.
        Find load operations and replace them with assignments """
        self.logger.debug('Promoting {} to register'.format(alloc_inst))

        # If only within one block:
        if len(alloc_inst.used_in_blocks()) == 1:
            self.logger.debug('{} only used in one block'.format(alloc_inst))
            self.promoteSingleBlock(alloc_inst)
            return

        self.logger.debug('Multiple blocks use {}'.format(alloc_inst))

        loads = [i for i in alloc_inst.used_by if isinstance(i, Load)]
        stores = [i for i in alloc_inst.used_by if isinstance(i, Store)]

        self.logger.debug('Alloc used by {} load and {} stores'.
                          format(len(loads), len(stores)))

        # Each store instruction can be removed (later).
        # Instead of storing the value, we use it
        # where the load would have been!
        replMap = {}
        for store in stores:
            replMap[store] = store.value

        # for each load, track back what the defining store
        # was.
        for load in loads:
            pass
        raise Exception("Not implemented")

    def onFunction(self, f):
        dom_tree = f.dominator_tree()
        print(dom_tree)
        for bb in f.Blocks:
            allocs = [i for i in bb.Instructions if isinstance(i, Alloc)]
            for alloc_inst in allocs:
                if isAllocPromotable(alloc_inst):
                    self.promote(alloc_inst)
