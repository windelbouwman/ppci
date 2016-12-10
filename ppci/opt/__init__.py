from .clean import CleanPass
from .mem2reg import Mem2RegPromotor
from .cse import CommonSubexpressionEliminationPass
from .constantfolding import ConstantFolder
from .transform import RemoveAddZeroPass, LoadAfterStorePass
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
