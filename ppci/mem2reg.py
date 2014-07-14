import logging
from transform import FunctionPass
from ir import *

def isAllocPromotable(allocinst):
    # Check if alloc value is only used by load and store operations.
    assert type(allocinst) is Alloc
    return all(type(use) in [Load, Store] for use in allocinst.value.used_by)


class Mem2RegPromotor(FunctionPass):
    def promoteSingleBlock(self, ai):
        v = ai.value
        bb = ai.Block

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
            logging.debug('replaced {} with {}'.format(load, store.value))
            bb.removeInstruction(load)

        # Remove store instructions:
        for store in stores:
            sv = store.value
            logging.debug('removing {}'.format(store))
            bb.removeInstruction(store)
            #assert sv.Used
        
        # Remove alloca instruction:
        assert not ai.value.Used, ai.value.used_by
        bb.removeInstruction(ai)

    def promote(self, ai):
        # Find load operations and replace them with assignments
        v = ai.value
        if len(ai.value.UsedInBlocks) == 1:
            self.promoteSingleBlock(ai)
            return
        
        loads = [i for i in v.used_by if isinstance(i, Load)]
        stores = [i for i in v.used_by if isinstance(i, Store)]

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

    def onFunction(self, f):
        for bb in f.BasicBlocks:
            allocs = [i for i in bb.Instructions if isinstance(i, Alloc)]
            for i in allocs:
                if isAllocPromotable(i):
                    self.promote(i)
