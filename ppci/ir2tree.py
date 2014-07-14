from .tree import Tree
from . import ir

""" Create a tree from ir code. """

f_map = {}    # Mapping from types to tree creation functions

def register(tp):
    """ Register a function for type tp """
    def reg_f(f):
        f_map[tp] = f
        return f
    return reg_f

@register(ir.Binop)
@register(ir.Add)
def binop_to_tree(e):
    names = {'+':'ADDI32', '-':'SUBI32', '|':'ORI32', '<<':'SHLI32',
        '*':'MULI32', '&':'ANDI32', '>>':'SHRI32'}
    op = names[e.operation]
    assert e.ty == ir.i32
    return Tree(op, makeTree(e.a), makeTree(e.b))


@register(ir.GlobalVariable)
def global_address_to_tree(e):
    t = Tree('GLOBALADDRESS')
    t.value = ir.label_name(e)
    return t

@register(ir.Const)
def const_to_tree(e):
    if type(e.value) is bytes:
        t = Tree('CONSTDATA')
        t.value = e.value
        return t
    elif type(e.value) is int:
        t = Tree('CONSTI32')
        t.value = e.value
        return t
    else:
        raise Exception('{} not implemented'.format(type(e.value)))


@register(ir.Addr)
def mem_to_tree(e):
    return Tree('ADR', makeTree(e.e))

@register(ir.Call)
def call_to_tree(e):
    t = Tree('CALL')
    t.value = e
    return t

def makeTree(ir_node):
    """ Transform an ir node into a tree usable for matching """
    return f_map[type(ir_node)](ir_node)
