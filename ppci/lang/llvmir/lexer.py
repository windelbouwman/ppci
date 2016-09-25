
import re
from ...common import make_num
from ...pcc.baselex import BaseLexer
from . import nodes


class LlvmIrLexer(BaseLexer):
    types = [
        'void', 'double', 'float',
        'label',
        'i64', 'i32', 'i16', 'i8', 'i1',
        'f32', 'f16']

    keywords = [
        'define', 'declare',
        'target', 'triple', 'datalayout',
        'attributes',
        'nounwind', 'sspstrong', 'uwtable', 'readonly',
        'nonnull',
        'align', 'inbounds',
        'nocapture',
        'ret', 'br', 'call',
        'icmp', 'fcmp',
        'eq', 'ne', 'slt', 'sgt', 'sle', 'sge', 'ule', 'ult', 'uge', 'ugt',
        'ueq',
        'select',
        'x', 'zeroinitializer', 'undef',
        'alloca', 'load', 'store', 'getelementptr',
        'extractelement', 'insertelement', 'shufflevector',
        'add', 'sub', 'mul', 'shl', 'srem',
        'fadd', 'fsub', 'fmul', 'fdiv', 'frem',
        'sext', 'zext', 'trunc', 'fptrunc',
        'uitofp', 'fptoui', 'sitofp', 'fptosi',
        'ptrtoint', 'inttoptr',
        'to',
        'or', 'xor', 'and',
        'true', 'false']
    glyphs = (
        ',', '=', '{', '}', '(', ')', '*', '<', '>', '[', ']', '!')

    def __init__(self, context):
        # Construct the string of possible glyphs:
        op_txt = '|'.join(re.escape(g) for g in self.glyphs)
        tok_spec = [
            ('HEXDOUBLE', r'0x[KLMHJ]?[\da-fA-F]+',
             lambda typ, val: (typ, val)),
            # ('HEXNUMBER', r'0x[\da-fA-F]+',
            #  lambda typ, val: ('NUMBER', make_num(val))),
            ('NUMBER', r'[\-\+]?\d+', lambda typ, val: (typ, int(val))),
            ('GID', r'@[A-Za-z\d_]+', self.handle_id),
            ('LID', r'%[A-Za-z\d_]+', self.handle_id),
            ('ATTRID', r'#\d+', lambda t, v: (t, v)),
            ('MDVAR', r'![a-zA-Z_][a-zA-Z\d\.]*', lambda t, v: (t, v)),
            ('LBL', r'[A-Za-z_][A-Za-z\d_]*:', lambda t, v: (t, v)),
            ('ID', r'[A-Za-z_][A-Za-z\d_]*', self.handle_id),
            ('LINECOMMENT', r';[^\n\r]*', None),
            ('STR', r'"[^"]*"', lambda typ, val: (typ, val[1:-1])),
            ('NEWLINE', r'\n', lambda typ, val: self.newline()),
            ('SKIP', r'[ \t]', None),
            ('GLYPH', op_txt, lambda typ, val: (val, val)),
        ]
        super().__init__(tok_spec)
        self.context = context

    def handle_id(self, typ, val):
        if val in self.keywords:
            typ = val
        elif val in self.types:
            typ = 'type'
            if val == 'void':
                val = self.context.void_ty
            elif val == 'float':
                val = self.context.float_ty
            elif val == 'double':
                val = self.context.double_ty
            elif val == 'label':
                val = self.context.label_ty
            elif val.startswith('i'):
                bits = int(val[1:])
                val = nodes.IntegerType.get(self.context, bits)
            else:  # pragma: no cover
                raise NotImplementedError(val)
        return typ, val
