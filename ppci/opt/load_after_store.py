from .transform import BlockPass
from .. import ir


class LoadAfterStorePass(BlockPass):
    """ Remove load after store to the same location.

        .. code::

            [x] = a
            b = [x]
            c = b + 2

        transforms into:

        .. code::

            [x] = a
            c = a + 2
    """
    def find_store_backwards(
            self, i, ty,
            stop_on=(ir.FunctionCall, ir.ProcedureCall, ir.Store)):
        """ Go back from this instruction to beginning """
        block = i.block
        instructions = block.instructions
        pos = instructions.index(i)
        for x in range(pos - 1, 0, -1):
            i2 = instructions[x]
            if isinstance(i2, ir.Store) and ty is i2.value.ty:
                # Got first store!
                if i2.address is i.address:
                    return i2
                else:
                    return None
            elif isinstance(i2, stop_on):
                # A call can change memory, store not found..
                return None
        return None

    def on_block(self, block):
        self.replace_load_after_store(block)
        self.remove_redundant_stores(block)

    def replace_load_after_store(self, block):
        """ Replace load after store with the value of the store """
        load_instructions = [
            ins for ins in block if isinstance(ins, ir.Load) and
            not ins.volatile]

        # Replace loads after store of same address by the stored value:
        count = 0
        for load in load_instructions:
            # Find store instruction preceeding this load:
            store = self.find_store_backwards(load, load.ty)
            if store is not None:
                # Assert type equivalence:
                assert load.ty is store.value.ty
                load.replace_by(store.value)
                count += 1
                # TODO: after one try, the instructions are different
                # reload of instructions required?
        if count > 0:
            self.logger.debug('Replaced %s loads after store', count)

    def remove_redundant_stores(self, block):
        """ From two stores to the same address remove the previous one """
        store_instructions = [
            i for i in block if isinstance(i, ir.Store) and not i.volatile]

        count = 0
        # TODO: assume volatile memory stores always!
        # Replace stores to the same location:
        for store in store_instructions:
            store_prev = self.find_store_backwards(
                store, store.value.ty,
                stop_on=(ir.FunctionCall, ir.ProcedureCall, ir.Store, ir.Load))
            if store_prev is not None and not store_prev.volatile:
                store_prev.remove_from_block()

        if count > 0:
            self.logger.debug('Replaced %s redundant stores', count)
