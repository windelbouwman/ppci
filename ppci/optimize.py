from mem2reg import Mem2RegPromotor
from transform import CommonSubexpressionElimination, CleanPass
from transform import DeadCodeDeleter, ConstantFolder

def optimize(ir):
    return 
    cf = ConstantFolder()
    cf.run(ir)
    return
    dcd = DeadCodeDeleter()
    m2r = Mem2RegPromotor()
    clr = CleanPass()
    cse = CommonSubexpressionElimination()
    dcd.run(ir)
    clr.run(ir)
    m2r.run(ir)
    cse.run(ir)
    cf.run(ir)
    dcd.run(ir)
