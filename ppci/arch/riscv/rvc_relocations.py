from ...utils.bitfun import wrap_negative, BitView
from ..encoding import Relocation
from .tokens import RiscvToken, RiscvcToken
import logging

class CRel(Relocation):
    l = []
    
    name = 'c_base'    
    @classmethod
    def isinsrange(cls, bits, val):
        msb = 1<<(bits-1)
        ll = -msb
        if (val<=(msb-1) and (val >=ll)):
            return True
        else:    
            return False

class CBImm11Relocation(CRel):
    name = 'cb_imm11'
    token = RiscvToken
    changesize = False
    
    def apply(self, sym_value, data, reloc_value, opt = False):
        logger = logging.getLogger('linker')
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        bv = BitView(data, 0, 4)        
        if not opt and CRel.isinsrange(12, offset) or self.changesize:                    
            if not opt:
                CRel.l.append(reloc_value)
                self.changesize = True
            rel11 = wrap_negative(offset >> 1, 11)            
            bv[0:2] = 0b01
            bv[2:3] = rel11 >> 4 & 0x1
            bv[3:6] = rel11 & 0x7
            bv[6:7] = rel11 >> 6 & 0x1
            bv[7:8] = rel11 >> 5 & 0x1
            bv[8:9] = rel11 >> 9 & 0x1
            bv[9:11] = rel11 >> 7 & 0x3
            bv[11:12] = rel11 >> 3 & 0x1
            bv[12:13] = rel11 >> 10 & 0x1
            bv[13:16] = 0b101
            bv[16:32] = 0x1
            rsize = 2
            logger.debug('CBRel inrange: symval:%08x,relocval:%08x,diff:%08x,%s' %(sym_value, reloc_value, offset,self.changesize))
        else:
            logger.debug('CBRel not in range: symval:%08x,relocval:%08x,diff:%08x,%s' %(sym_value, reloc_value, offset,self.changesize))
            rel20 = wrap_negative(offset >> 1, 20)            
            bv[21:31] = rel20 & 0x3FF
            bv[20:21] = rel20 >> 10 & 0x1
            bv[12:20] = rel20 >> 11 & 0xFF
            bv[31:32] = rel20 >> 19 & 0x1
            rsize = 4
        if opt:
            return data, rsize
        else:
            return data 

class CBlImm11Relocation(CRel):
    name = 'cbl_imm11'
    token = RiscvToken
    changesize = False
    
    def apply(self, sym_value, data, reloc_value, opt = False):
        logger = logging.getLogger('linker')
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        bv = BitView(data, 0, 4)        
        if not opt and CRel.isinsrange(12, offset) or self.changesize:                    
            if not opt:
                CRel.l.append(reloc_value)
                self.changesize = True
            rel11 = wrap_negative(offset >> 1, 11)            
            bv[0:2] = 0b01
            bv[2:3] = rel11 >> 4 & 0x1
            bv[3:6] = rel11 & 0x7
            bv[6:7] = rel11 >> 6 & 0x1
            bv[7:8] = rel11 >> 5 & 0x1
            bv[8:9] = rel11 >> 9 & 0x1
            bv[9:11] = rel11 >> 7 & 0x3
            bv[11:12] = rel11 >> 3 & 0x1
            bv[12:13] = rel11 >> 10 & 0x1
            bv[13:16] = 0b001
            bv[16:32] = 0x1
            rsize = 2
            logger.debug('CRel in range: symval:%08x,relocval:%08x,diff:%08x,%s' %(sym_value, reloc_value, offset,self.changesize))
        else:
            logger.debug('CRel not in range: symval:%08x,relocval:%08x,diff:%08x,%s' %(sym_value, reloc_value, offset,self.changesize))
            rel20 = wrap_negative(offset >> 1, 20)            
            bv[21:31] = rel20 & 0x3FF
            bv[20:21] = rel20 >> 10 & 0x1
            bv[12:20] = rel20 >> 11 & 0xFF
            bv[31:32] = rel20 >> 19 & 0x1
            rsize = 4
        if opt:
            return data, rsize
        else:
            return data 
            
class BcImm11Relocation(CRel):
    name = 'bc_imm11'
    token = RiscvcToken

    def apply(self, sym_value, data, reloc_value, opt = False):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        rel11 = wrap_negative(offset >> 1, 11)
        bv = BitView(data, 0, 4)
        bv[2:3] = rel11 >> 4 & 0x1
        bv[3:6] = rel11 & 0x7
        bv[6:7] = rel11 >> 6 & 0x1
        bv[7:8] = rel11 >> 5 & 0x1
        bv[8:9] = rel11 >> 9 & 0x1
        bv[9:11] = rel11 >> 7 & 0x3
        bv[11:12] = rel11 >> 3 & 0x1
        bv[12:13] = rel11 >> 10 & 0x1
        if opt:
            return data, 2
        else:
            return data 

class BcImm8Relocation(CRel):
    name = 'bc_imm8'
    token = RiscvcToken

    def apply(self, sym_value, data, reloc_value, opt = False):
        assert sym_value % 2 == 0
        assert reloc_value % 2 == 0
        offset = sym_value - reloc_value
        rel8 = wrap_negative(offset >> 1, 8)
        bv = BitView(data, 0, 4)
        bv[2:3] = rel8 >> 4 & 0x1
        bv[3:5] = rel8 & 0x3
        bv[5:7] = rel8 >> 5 & 0x3
        bv[10:12] = rel8 >> 2 & 0x3
        bv[12:13] = rel8 >> 7 & 0x1
        if opt:
            return data, 2
        else:
            return data 
