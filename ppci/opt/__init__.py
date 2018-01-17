from .clean import CleanPass
from .mem2reg import Mem2RegPromotor
from .cse import CommonSubexpressionEliminationPass
from .constantfolding import ConstantFolder
from .load_after_store import LoadAfterStorePass
from .transform import RemoveAddZeroPass
from .transform import DeleteUnusedInstructionsPass
from .transform import ModulePass, FunctionPass, BlockPass, InstructionPass


__all__ = [
    'ModulePass', 'FunctionPass', 'BlockPass', 'InstructionPass',
    'CleanPass',
    'CommonSubexpressionEliminationPass',
    'ConstantFolder',
    'DeleteUnusedInstructionsPass',
    'LoadAfterStorePass',
    'Mem2RegPromotor',
    'RemoveAddZeroPass'
    ]
