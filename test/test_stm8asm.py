from test_asm import AsmTestCaseBase
import unittest



class Stm8AssemblerTestCase(AsmTestCaseBase):
    """ STM8 instruction assembly test case """
    march = 'stm8'


    def test_adc_a_byte(self):
        self.feed('ADC A,#%00010010')
        self.check('A912')

    def test_adc_a_longmem(self):
        self.feed('ADC A,$1234')
        self.check('C91234')

    def test_adc_a_x(self):
        self.feed('ADC A,(X)')
        self.check('F9')

    def test_adc_a_longoff_x(self):
        self.feed('ADC A,($1234,X)')
        self.check('D91234')

    def test_adc_a_y(self):
        self.feed('ADC A,(Y)')
        self.check('90F9')

    def test_adc_a_longoff_y(self):
        self.feed('ADC A,($1234,Y)')
        self.check('90D91234')

    def test_adc_a_shortoff_sp(self):
        self.feed('ADC A,($12,SP)')
        self.check('1912')

    def test_adc_a_longptr(self):
        self.feed('ADC A,[$1234]')
        self.check('72C91234')

    def test_adc_a_longptr_x(self):
        self.feed('ADC A,([$1234],X)')
        self.check('72D91234')

    def test_adc_a_shortptr_y(self):
        self.feed('ADC A,([$12],Y)')
        self.check('91D912')


    def test_add_a_byte(self):
        self.feed('ADD A,#%00010010')
        self.check('AB12')

    def test_add_a_longmem(self):
        self.feed('ADD A,$1234')
        self.check('CB1234')

    def test_add_a_x(self):
        self.feed('ADD A,(X)')
        self.check('FB')

    def test_add_a_longoff_x(self):
        self.feed('ADD A,($1234,X)')
        self.check('DB1234')

    def test_add_a_y(self):
        self.feed('ADD A,(Y)')
        self.check('90FB')

    def test_add_a_longoff_y(self):
        self.feed('ADD A,($1234,Y)')
        self.check('90DB1234')

    def test_add_a_shortoff_sp(self):
        self.feed('ADD A,($12,SP)')
        self.check('1B12')

    def test_add_a_longptr(self):
        self.feed('ADD A,[$1234]')
        self.check('72CB1234')

    def test_add_a_longptr_x(self):
        self.feed('ADD A,([$1234],X)')
        self.check('72DB1234')

    def test_add_a_shortptr_y(self):
        self.feed('ADD A,([$12],Y)')
        self.check('91DB12')


    def test_addw_x_word(self):
        self.feed('ADDW X,#$1234')
        self.check('1C1234')

    def test_addw_x_longmem(self):
        self.feed('ADDW X,$1234')
        self.check('72BB1234')

    def test_addw_x_shortoff_sp(self):
        self.feed('ADDW X,($12,SP)')
        self.check('72FB12')

    def test_addw_y_word(self):
        self.feed('ADDW Y,#$1234')
        self.check('72A91234')

    def test_addw_y_longmem(self):
        self.feed('ADDW Y,$1234')
        self.check('72B91234')

    def test_addw_y_shortoff_sp(self):
        self.feed('ADDW Y,($12,SP)')
        self.check('72F912')

    def test_addw_sp_byte(self):
        self.feed('ADDW SP,#$12')
        self.check('5B12')


    def test_and_a_byte(self):
        self.feed('AND A,#%00010010')
        self.check('A412')

    def test_and_a_longmem(self):
        self.feed('AND A,$1234')
        self.check('C41234')

    def test_and_a_x(self):
        self.feed('AND A,(X)')
        self.check('F4')

    def test_and_a_longoff_x(self):
        self.feed('AND A,($1234,X)')
        self.check('D41234')

    def test_and_a_y(self):
        self.feed('AND A,(Y)')
        self.check('90F4')

    def test_and_a_longoff_y(self):
        self.feed('AND A,($1234,Y)')
        self.check('90D41234')

    def test_and_a_shortoff_sp(self):
        self.feed('AND A,($12,SP)')
        self.check('1412')

    def test_and_a_longptr(self):
        self.feed('AND A,[$1234]')
        self.check('72C41234')

    def test_and_a_longptr_x(self):
        self.feed('AND A,([$1234],X)')
        self.check('72D41234')

    def test_and_a_shortptr_y(self):
        self.feed('AND A,([$12],Y)')
        self.check('91D412')


    def test_bccm(self):
        self.feed('BCCM $1234,#5')
        self.check('901B1234')


    def test_bcp_a_byte(self):
        self.feed('BCP A,#%00010010')
        self.check('A512')

    def test_bcp_a_longmem(self):
        self.feed('BCP A,$1234')
        self.check('C51234')

    def test_bcp_a_x(self):
        self.feed('BCP A,(X)')
        self.check('F5')

    def test_bcp_a_longoff_x(self):
        self.feed('BCP A,($1234,X)')
        self.check('D51234')

    def test_bcp_a_y(self):
        self.feed('BCP A,(Y)')
        self.check('90F5')

    def test_bcp_a_longoff_y(self):
        self.feed('BCP A,($1234,Y)')
        self.check('90D51234')

    def test_bcp_a_shortoff_sp(self):
        self.feed('BCP A,($12,SP)')
        self.check('1512')

    def test_bcp_a_longptr(self):
        self.feed('BCP A,[$1234]')
        self.check('72C51234')

    def test_bcp_a_longptr_x(self):
        self.feed('BCP A,([$1234],X)')
        self.check('72D51234')

    def test_bcp_a_shortptr_y(self):
        self.feed('BCP A,([$12],Y)')
        self.check('91D512')


    def test_bcpl(self):
        self.feed('BCPL $1234,#5')
        self.check('901A1234')


    def test_break(self):
        self.feed('BREAK')
        self.check('8B')



    def test_bres(self):
        self.feed('BRES $1234,#5')
        self.check('721B1234')



    def test_bset(self):
        self.feed('BSET $1234,#5')
        self.check('721A1234')


    def test_btjf(self):
        self.feed('BTJF $1234,#5,$67')
        self.check('720B123467')


    def test_btjt(self):
        self.feed('BTJT $1234,#5,$67')
        self.check('720A123467')


    def test_call_longmem(self):
        self.feed('CALL $1234')
        self.check('CD1234')

    def test_call_x(self):
        self.feed('CALL (X)')
        self.check('FD')

    def test_call_longoff_x(self):
        self.feed('CALL ($1234,X)')
        self.check('DD1234')

    def test_call_y(self):
        self.feed('CALL (Y)')
        self.check('90FD')

    def test_call_longoff_y(self):
        self.feed('CALL ($1234,Y)')
        self.check('90DD1234')

    def test_call_longptr(self):
        self.feed('CALL [$1234]')
        self.check('72CD1234')

    def test_call_longptr_x(self):
        self.feed('CALL ([$1234],X)')
        self.check('72DD1234')

    def test_call_shortptr_y(self):
        self.feed('CALL ([$12],Y)')
        self.check('91DD12')


    def test_callr(self):
        self.feed('CALLR $12')
        self.check('AD12')


    def test_ccf(self):
        self.feed('CCF')
        self.check('8C')


    def test_clr_a(self):
        self.feed('CLR A')
        self.check('4F')

    def test_clr_longmem(self):
        self.feed('CLR $1234')
        self.check('725F1234')

    def test_clr_x(self):
        self.feed('CLR (X)')
        self.check('7F')

    def test_clr_longoff_x(self):
        self.feed('CLR ($1234,X)')
        self.check('724F1234')

    def test_clr_y(self):
        self.feed('CLR (Y)')
        self.check('907F')

    def test_clr_longoff_y(self):
        self.feed('CLR ($1234,Y)')
        self.check('904F1234')

    def test_clr_longptr(self):
        self.feed('CLR [$1234]')
        self.check('723F1234')

    def test_clr_longptr_x(self):
        self.feed('CLR ([$1234],X)')
        self.check('726F1234')

    def test_clr_shortptr_y(self):
        self.feed('CLR ([$12],Y)')
        self.check('916F12')


    def test_clrw_x(self):
        self.feed('CLRW X')
        self.check('5F')

    def test_clrw_y(self):
        self.feed('CLRW Y')
        self.check('905F')


    def test_cp_a_byte(self):
        self.feed('CP A,#%00010010')
        self.check('A112')

    def test_cp_a_longmem(self):
        self.feed('CP A,$1234')
        self.check('C11234')

    def test_cp_a_x(self):
        self.feed('CP A,(X)')
        self.check('F1')

    def test_cp_a_longoff_x(self):
        self.feed('CP A,($1234,X)')
        self.check('D11234')

    def test_cp_a_y(self):
        self.feed('CP A,(Y)')
        self.check('90F1')

    def test_cp_a_longoff_y(self):
        self.feed('CP A,($1234,Y)')
        self.check('90D11234')

    def test_cp_a_shortoff_sp(self):
        self.feed('CP A,($12,SP)')
        self.check('1112')

    def test_cp_a_longptr(self):
        self.feed('CP A,[$1234]')
        self.check('72C11234')

    def test_cp_a_longptr_x(self):
        self.feed('CP A,([$1234],X)')
        self.check('72D11234')

    def test_cp_a_shortptr_y(self):
        self.feed('CP A,([$12],Y)')
        self.check('91D112')


    def test_cpw_x_word(self):
        self.feed('CPW X,#$1234')
        self.check('A31234')

    def test_cpw_x_longmem(self):
        self.feed('CPW X,$1234')
        self.check('C31234')

    def test_cpw_x_y(self):
        self.feed('CPW X,(Y)')
        self.check('90F3')

    def test_cpw_x_longoff_y(self):
        self.feed('CPW X,($1234,Y)')
        self.check('90D31234')

    def test_cpw_x_shortoff_sp(self):
        self.feed('CPW X,($12,SP)')
        self.check('1312')

    def test_cpw_x_longptr(self):
        self.feed('CPW X,[$1234]')
        self.check('72C31234')

    def test_cpw_x_shortptr_y(self):
        self.feed('CPW X,([$12],Y)')
        self.check('91D312')

    def test_cpw_y_word(self):
        self.feed('CPW Y,#$1234')
        self.check('90A31234')

    def test_cpw_y_longmem(self):
        self.feed('CPW Y,$1234')
        self.check('90C31234')

    def test_cpw_y_x(self):
        self.feed('CPW Y,(X)')
        self.check('F3')

    def test_cpw_y_longoff_x(self):
        self.feed('CPW Y,($1234,X)')
        self.check('D31234')

    def test_cpw_y_shortptr(self):
        self.feed('CPW Y,[$12]')
        self.check('91C312')

    def test_cpw_y_longptr_x(self):
        self.feed('CPW Y,([$1234],X)')
        self.check('72D31234')


    def test_cpl_a(self):
        self.feed('CPL A')
        self.check('43')

    def test_cpl_longmem(self):
        self.feed('CPL $1234')
        self.check('72531234')

    def test_cpl_x(self):
        self.feed('CPL (X)')
        self.check('73')

    def test_cpl_longoff_x(self):
        self.feed('CPL ($1234,X)')
        self.check('72431234')

    def test_cpl_y(self):
        self.feed('CPL (Y)')
        self.check('9073')

    def test_cpl_longoff_y(self):
        self.feed('CPL ($1234,Y)')
        self.check('90431234')

    def test_cpl_longptr(self):
        self.feed('CPL [$1234]')
        self.check('72331234')

    def test_cpl_longptr_x(self):
        self.feed('CPL ([$1234],X)')
        self.check('72631234')

    def test_cpl_shortptr_y(self):
        self.feed('CPL ([$12],Y)')
        self.check('916312')


    def test_cplw_x(self):
        self.feed('CPLW X')
        self.check('53')

    def test_cplw_y(self):
        self.feed('CPLW Y')
        self.check('9053')


    def test_dec_a(self):
        self.feed('DEC A')
        self.check('4A')

    def test_dec_longmem(self):
        self.feed('DEC $1234')
        self.check('725A1234')

    def test_dec_x(self):
        self.feed('DEC (X)')
        self.check('7A')

    def test_dec_longoff_x(self):
        self.feed('DEC ($1234,X)')
        self.check('724A1234')

    def test_dec_y(self):
        self.feed('DEC (Y)')
        self.check('907A')

    def test_dec_longoff_y(self):
        self.feed('DEC ($1234,Y)')
        self.check('904A1234')

    def test_dec_longptr(self):
        self.feed('DEC [$1234]')
        self.check('723A1234')

    def test_dec_longptr_x(self):
        self.feed('DEC ([$1234],X)')
        self.check('726A1234')

    def test_dec_shortptr_y(self):
        self.feed('DEC ([$12],Y)')
        self.check('916A12')


    def test_decw_x(self):
        self.feed('DECW X')
        self.check('5A')

    def test_decw_y(self):
        self.feed('DECW Y')
        self.check('905A')


    def test_div_x_a(self):
        self.feed('DIV X,A')
        self.check('62')

    def test_div_y_a(self):
        self.feed('DIV Y,A')
        self.check('9062')


    def test_div_x_y(self):
        self.feed('DIV X,Y')
        self.check('65')


    def test_exg_a_xl(self):
        self.feed('EXG A,XL')
        self.check('41')

    def test_exg_a_yl(self):
        self.feed('EXG A,YL')
        self.check('61')

    def test_exg_a_longmem(self):
        self.feed('EXG A,$1234')
        self.check('311234')


    def test_exgw_x_y(self):
        self.feed('EXGW X,Y')
        self.check('51')


    def test_halt(self):
        self.feed('HALT')
        self.check('8E')


    def test_inc_a(self):
        self.feed('INC A')
        self.check('4C')

    def test_inc_longmem(self):
        self.feed('INC $1234')
        self.check('725C1234')

    def test_inc_x(self):
        self.feed('INC (X)')
        self.check('7C')

    def test_inc_longoff_x(self):
        self.feed('INC ($1234,X)')
        self.check('724C1234')

    def test_inc_y(self):
        self.feed('INC (Y)')
        self.check('907C')

    def test_inc_longoff_y(self):
        self.feed('INC ($1234,Y)')
        self.check('904C1234')

    def test_inc_longptr(self):
        self.feed('INC [$1234]')
        self.check('723C1234')

    def test_inc_longptr_x(self):
        self.feed('INC ([$1234],X)')
        self.check('726C1234')

    def test_inc_shortptr_y(self):
        self.feed('INC ([$12],Y)')
        self.check('916C12')


    def test_incw_x(self):
        self.feed('INCW X')
        self.check('5C')

    def test_incw_y(self):
        self.feed('INCW Y')
        self.check('905C')


    def test_int_longmem(self):
        self.feed('INT $1234')
        self.check('82001234')


    def test_iret(self):
        self.feed('IRET')
        self.check('80')


    def test_jp_a_longmem(self):
        self.feed('JP $1234')
        self.check('CC1234')

    def test_jp_a_x(self):
        self.feed('JP (X)')
        self.check('FC')

    def test_jp_a_longoff_x(self):
        self.feed('JP ($1234,X)')
        self.check('DC1234')

    def test_jp_a_y(self):
        self.feed('JP (Y)')
        self.check('90FC')

    def test_jp_a_longoff_y(self):
        self.feed('JP ($1234,Y)')
        self.check('90DC1234')

    def test_jp_a_longptr(self):
        self.feed('JP [$1234]')
        self.check('72CC1234')

    def test_jp_a_longptr_x(self):
        self.feed('JP ([$1234],X)')
        self.check('72DC1234')

    def test_jp_a_shortptr_y(self):
        self.feed('JP ([$12],Y)')
        self.check('91DC12')


    def test_jra(self):
        self.feed('JRA $12')
        self.check('2012')


    def test_jrc(self):
        self.feed('JRC 0x12')
        self.check('2512')

    def test_jreq(self):
        self.feed('JREQ 0x12')
        self.check('2712')

    def test_jrf(self):
        self.feed('JRF 0x12')
        self.check('2112')

    def test_jrh(self):
        self.feed('JRH 0x12')
        self.check('902912')

    def test_jrih(self):
        self.feed('JRIH 0x12')
        self.check('902F12')

    def test_jril(self):
        self.feed('JRIL 0x12')
        self.check('902E12')

    def test_jrm(self):
        self.feed('JRM 0x12')
        self.check('902D12')

    def test_jrmi(self):
        self.feed('JRMI 0x12')
        self.check('2B12')

    def test_jrnc(self):
        self.feed('JRNC 0x12')
        self.check('2412')

    def test_jrne(self):
        self.feed('JRNE 0x12')
        self.check('2612')

    def test_jrnh(self):
        self.feed('JRNH 0x12')
        self.check('902812')

    def test_jrnm(self):
        self.feed('JRNM 0x12')
        self.check('902C12')

    def test_jrnv(self):
        self.feed('JRNV 0x12')
        self.check('2812')

    def test_jrpl(self):
        self.feed('JRPL 0x12')
        self.check('2A12')

    def test_jrsge(self):
        self.feed('JRSGE 0x12')
        self.check('2E12')

    def test_jrsgt(self):
        self.feed('JRSGT 0x12')
        self.check('2C12')

    def test_jrsle(self):
        self.feed('JRSLE 0x12')
        self.check('2D12')

    def test_jrslt(self):
        self.feed('JRSLT 0x12')
        self.check('2F12')

    def test_jrt(self):
        self.feed('JRT 0x12')
        self.check('2012')

    def test_jruge(self):
        self.feed('JRUGE 0x12')
        self.check('2412')

    def test_jrugt(self):
        self.feed('JRUGT 0x12')
        self.check('2212')

    def test_jrule(self):
        self.feed('JRULE 0x12')
        self.check('2312')

    def test_jrult(self):
        self.feed('JRULT 0x12')
        self.check('2512')

    def test_jrv(self):
        self.feed('JRV 0x12')
        self.check('2912')


    def test_ld_a_byte(self):
        self.feed('LD A,#%00010010')
        self.check('A612')

    def test_ld_a_longmem(self):
        self.feed('LD A,$1234')
        self.check('C61234')

    def test_ld_a_x(self):
        self.feed('LD A,(X)')
        self.check('F6')

    def test_ld_a_longoff_x(self):
        self.feed('LD A,($1234,X)')
        self.check('D61234')

    def test_ld_a_y(self):
        self.feed('LD A,(Y)')
        self.check('90F6')

    def test_ld_a_longoff_y(self):
        self.feed('LD A,($1234,Y)')
        self.check('90D61234')

    def test_ld_a_shortoff_sp(self):
        self.feed('LD A,($12,SP)')
        self.check('7B12')

    def test_ld_a_longptr(self):
        self.feed('LD A,[$1234]')
        self.check('72C61234')

    def test_ld_a_longptr_x(self):
        self.feed('LD A,([$1234],X)')
        self.check('72D61234')

    def test_ld_a_shortptr_y(self):
        self.feed('LD A,([$12],Y)')
        self.check('91D612')

    def test_ld_longmem(self):
        self.feed('LD $1234,A')
        self.check('C71234')

    def test_ld_x(self):
        self.feed('LD (X),A')
        self.check('F7')

    def test_ld_longoff_x(self):
        self.feed('LD ($1234,X),A')
        self.check('D71234')

    def test_ld_y(self):
        self.feed('LD (Y),A')
        self.check('90F7')

    def test_ld_longoff_y(self):
        self.feed('LD ($1234,Y),A')
        self.check('90D71234')

    def test_ld_shortoff_sp(self):
        self.feed('LD ($12,SP),A')
        self.check('6B12')

    def test_ld_longptr(self):
        self.feed('LD [$1234],A')
        self.check('72C71234')

    def test_ld_longptr_x(self):
        self.feed('LD ([$1234],X),A')
        self.check('72D71234')

    def test_ld_shortptr_y(self):
        self.feed('LD ([$12],Y),A')
        self.check('91D712')

    def test_mov_xl_a(self):
        self.feed('LD XL,A')
        self.check('97')

    def test_mov_a_xl(self):
        self.feed('LD A,XL')
        self.check('9F')

    def test_mov_yl_a(self):
        self.feed('LD YL,A')
        self.check('9097')

    def test_mov_a_yl(self):
        self.feed('LD A,YL')
        self.check('909F')

    def test_mov_xh_a(self):
        self.feed('LD XH,A')
        self.check('95')

    def test_mov_a_xh(self):
        self.feed('LD A,XH')
        self.check('9E')

    def test_mov_yh_a(self):
        self.feed('LD YH,A')
        self.check('9095')

    def test_mov_a_yh(self):
        self.feed('LD A,YH')
        self.check('909E')


    def test_ldw_x_word(self):
        self.feed('LDW X,#$1234')
        self.check('AE1234')

    def test_ldw_x_longmem(self):
        self.feed('LDW X,$1234')
        self.check('CE1234')

    def test_ldw_x_x(self):
        self.feed('LDW X,(X)')
        self.check('FE')

    def test_ldw_x_longoff_x(self):
        self.feed('LDW X,($1234,X)')
        self.check('DE1234')

    def test_ldw_x_shortoff_sp(self):
        self.feed('LDW X,($12,SP)')
        self.check('1E12')

    def test_ldw_x_longptr(self):
        self.feed('LDW X,[$1234]')
        self.check('72CE1234')

    def test_ldw_x_longptr_x(self):
        self.feed('LDW X,([$1234],X)')
        self.check('72DE1234')

    def test_ldw_longmem_x(self):
        self.feed('LDW $1234,X')
        self.check('CF1234')

    def test_ldw_x_y(self):
        self.feed('LDW (X),Y')
        self.check('FF')

    def test_ldw_longoff_x_y(self):
        self.feed('LDW ($1234,X),Y')
        self.check('DF1234')

    def test_ldw_shortoff_sp_x(self):
        self.feed('LDW ($12,SP),X')
        self.check('1F12')

    def test_ldw_longptr_x(self):
        self.feed('LDW [$1234],X')
        self.check('72CF1234')

    def test_ldw_longptr_x_y(self):
        self.feed('LDW ([$1234],X),Y')
        self.check('72DF1234')


    def test_ldw_y_word(self):
        self.feed('LDW Y,#$1234')
        self.check('90AE1234')

    def test_ldw_y_longmem(self):
        self.feed('LDW Y,$1234')
        self.check('90CE1234')

    def test_ldw_y_y(self):
        self.feed('LDW Y,(Y)')
        self.check('90FE')

    def test_ldw_y_longoff_y(self):
        self.feed('LDW Y,($1234,Y)')
        self.check('90DE1234')

    def test_ldw_y_shortoff_sp(self):
        self.feed('LDW Y,($12,SP)')
        self.check('1612')

    def test_ldw_y_shortptr(self):
        self.feed('LDW Y,[$12]')
        self.check('91CE12')

    def test_ldw_y_shortptr_y(self):
        self.feed('LDW Y,([$12],Y)')
        self.check('91DE12')

    def test_ldw_longmem_y(self):
        self.feed('LDW $1234,Y')
        self.check('90CF1234')

    def test_ldw_y_x(self):
        self.feed('LDW (Y),X')
        self.check('90FF')

    def test_ldw_longoff_y_x(self):
        self.feed('LDW ($1234,Y),X')
        self.check('90DF1234')

    def test_ldw_shortoff_sp_y(self):
        self.feed('LDW ($12,SP),Y')
        self.check('1712')

    def test_ldw_shortptr_y(self):
        self.feed('LDW [$12],Y')
        self.check('91CF12')

    def test_ldw_shortptr_y_x(self):
        self.feed('LDW ([$12],Y),X')
        self.check('91DF12')

    def test_movw_x_y(self):
        self.feed('LDW X,Y')
        self.check('93')

    def test_movw_y_x(self):
        self.feed('LDW Y,X')
        self.check('9093')

    def test_movw_x_sp(self):
        self.feed('LDW X,SP')
        self.check('96')

    def test_movw_sp_x(self):
        self.feed('LDW SP,X')
        self.check('94')

    def test_movw_y_sp(self):
        self.feed('LDW Y,SP')
        self.check('9096')

    def test_movw_sp_y(self):
        self.feed('LDW SP,Y')
        self.check('9094')


    def test_mov_longmem_byte(self):
        self.feed('MOV $1234,#$56')
        self.check('35561234')

    def test_mov_longmem_longmem(self):
        self.feed('MOV $1234,$5678')
        self.check('5556781234')


    def test_mul_x_a(self):
        self.feed('MUL X,A')
        self.check('42')

    def test_mul_y_a(self):
        self.feed('MUL Y,A')
        self.check('9042')


    def test_neg_a(self):
        self.feed('NEG A')
        self.check('40')

    def test_neg_longmem(self):
        self.feed('NEG $1234')
        self.check('72501234')

    def test_neg_x(self):
        self.feed('NEG (X)')
        self.check('70')

    def test_neg_longoff_x(self):
        self.feed('NEG ($1234,X)')
        self.check('72401234')

    def test_neg_y(self):
        self.feed('NEG (Y)')
        self.check('9070')

    def test_neg_longoff_y(self):
        self.feed('NEG ($1234,Y)')
        self.check('90401234')

    def test_neg_longptr(self):
        self.feed('NEG [$1234]')
        self.check('72301234')

    def test_neg_longptr_x(self):
        self.feed('NEG ([$1234],X)')
        self.check('72601234')

    def test_neg_shortptr_y(self):
        self.feed('NEG ([$12],Y)')
        self.check('916012')


    def test_negw_x(self):
        self.feed('NEGW X')
        self.check('50')

    def test_negw_y(self):
        self.feed('NEGW Y')
        self.check('9050')


    def test_nop(self):
        self.feed('NOP')
        self.check('9D')


    def test_or_a_byte(self):
        self.feed('OR A,#%00010010')
        self.check('AA12')

    def test_or_a_longmem(self):
        self.feed('OR A,$1234')
        self.check('CA1234')

    def test_or_a_x(self):
        self.feed('OR A,(X)')
        self.check('FA')

    def test_or_a_longoff_x(self):
        self.feed('OR A,($1234,X)')
        self.check('DA1234')

    def test_or_a_y(self):
        self.feed('OR A,(Y)')
        self.check('90FA')

    def test_or_a_longoff_y(self):
        self.feed('OR A,($1234,Y)')
        self.check('90DA1234')

    def test_or_a_shortoff_sp(self):
        self.feed('OR A,($12,SP)')
        self.check('1A12')

    def test_or_a_longptr(self):
        self.feed('OR A,[$1234]')
        self.check('72CA1234')

    def test_or_a_longptr_x(self):
        self.feed('OR A,([$1234],X)')
        self.check('72DA1234')

    def test_or_a_shortptr_y(self):
        self.feed('OR A,([$12],Y)')
        self.check('91DA12')


    def test_pop_a(self):
        self.feed('POP A')
        self.check('84')

    def test_pop_cc(self):
        self.feed('POP CC')
        self.check('86')

    def test_pop_longmem(self):
        self.feed('POP $1234')
        self.check('321234')


    def test_popw_x(self):
        self.feed('POPW X')
        self.check('85')

    def test_popw_y(self):
        self.feed('POPW Y')
        self.check('9085')


    def test_push_a(self):
        self.feed('PUSH A')
        self.check('88')

    def test_push_cc(self):
        self.feed('PUSH CC')
        self.check('8A')

    def test_push_byte(self):
        self.feed('PUSH #$12')
        self.check('4B12')

    def test_push_longmem(self):
        self.feed('PUSH $1234')
        self.check('3B1234')


    def test_pushw_x(self):
        self.feed('PUSHW X')
        self.check('89')

    def test_pushw_y(self):
        self.feed('PUSHW Y')
        self.check('9089')


    def test_rcf(self):
        self.feed('RCF')
        self.check('98')


    def test_ret(self):
        self.feed('RET')
        self.check('81')


    def test_rim(self):
        self.feed('RIM')
        self.check('9A')


    def test_rlc_a(self):
        self.feed('RLC A')
        self.check('49')

    def test_rlc_longmem(self):
        self.feed('RLC $1234')
        self.check('72591234')

    def test_rlc_x(self):
        self.feed('RLC (X)')
        self.check('79')

    def test_rlc_longoff_x(self):
        self.feed('RLC ($1234,X)')
        self.check('72491234')

    def test_rlc_y(self):
        self.feed('RLC (Y)')
        self.check('9079')

    def test_rlc_longoff_y(self):
        self.feed('RLC ($1234,Y)')
        self.check('90491234')

    def test_rlc_longptr(self):
        self.feed('RLC [$1234]')
        self.check('72391234')

    def test_rlc_longptr_x(self):
        self.feed('RLC ([$1234],X)')
        self.check('72691234')

    def test_rlc_shortptr_y(self):
        self.feed('RLC ([$12],Y)')
        self.check('916912')


    def test_rlcw_x(self):
        self.feed('RLCW X')
        self.check('59')

    def test_rlcw_y(self):
        self.feed('RLCW Y')
        self.check('9059')


    def test_rlwa_x(self):
        self.feed('RLWA X,A')
        self.check('02')

    def test_rlwa_y(self):
        self.feed('RLWA Y,A')
        self.check('9002')


    def test_rrc_a(self):
        self.feed('RRC A')
        self.check('46')

    def test_rrc_longmem(self):
        self.feed('RRC $1234')
        self.check('72561234')

    def test_rrc_x(self):
        self.feed('RRC (X)')
        self.check('76')

    def test_rrc_longoff_x(self):
        self.feed('RRC ($1234,X)')
        self.check('72461234')

    def test_rrc_y(self):
        self.feed('RRC (Y)')
        self.check('9076')

    def test_rrc_longoff_y(self):
        self.feed('RRC ($1234,Y)')
        self.check('90461234')

    def test_rrc_longptr(self):
        self.feed('RRC [$1234]')
        self.check('72361234')

    def test_rrc_longptr_x(self):
        self.feed('RRC ([$1234],X)')
        self.check('72661234')

    def test_rrc_shortptr_y(self):
        self.feed('RRC ([$12],Y)')
        self.check('916612')


    def test_rrcw_x(self):
        self.feed('RRCW X')
        self.check('56')

    def test_rrcw_y(self):
        self.feed('RRCW Y')
        self.check('9056')


    def test_rrwa_x(self):
        self.feed('RRWA X,A')
        self.check('01')

    def test_rrwa_y(self):
        self.feed('RRWA Y,A')
        self.check('9001')


    def test_rvf(self):
        self.feed('RVF')
        self.check('9C')


    def test_sbc_a_byte(self):
        self.feed('SBC A,#%00010010')
        self.check('A212')

    def test_sbc_a_longmem(self):
        self.feed('SBC A,$1234')
        self.check('C21234')

    def test_sbc_a_x(self):
        self.feed('SBC A,(X)')
        self.check('F2')

    def test_sbc_a_longoff_x(self):
        self.feed('SBC A,($1234,X)')
        self.check('D21234')

    def test_sbc_a_y(self):
        self.feed('SBC A,(Y)')
        self.check('90F2')

    def test_sbc_a_longoff_y(self):
        self.feed('SBC A,($1234,Y)')
        self.check('90D21234')

    def test_sbc_a_shortoff_sp(self):
        self.feed('SBC A,($12,SP)')
        self.check('1212')

    def test_sbc_a_longptr(self):
        self.feed('SBC A,[$1234]')
        self.check('72C21234')

    def test_sbc_a_longptr_x(self):
        self.feed('SBC A,([$1234],X)')
        self.check('72D21234')

    def test_sbc_a_shortptr_y(self):
        self.feed('SBC A,([$12],Y)')
        self.check('91D212')


    def test_sll_a(self):
        self.feed('SLL A')
        self.check('48')

    def test_sll_longmem(self):
        self.feed('SLL $1234')
        self.check('72581234')

    def test_sll_x(self):
        self.feed('SLL (X)')
        self.check('78')

    def test_sll_longoff_x(self):
        self.feed('SLL ($1234,X)')
        self.check('72481234')

    def test_sll_y(self):
        self.feed('SLL (Y)')
        self.check('9078')

    def test_sll_longoff_y(self):
        self.feed('SLL ($1234,Y)')
        self.check('90481234')

    def test_sll_longptr(self):
        self.feed('SLL [$1234]')
        self.check('72381234')

    def test_sll_longptr_x(self):
        self.feed('SLL ([$1234],X)')
        self.check('72681234')

    def test_sll_shortptr_y(self):
        self.feed('SLL ([$12],Y)')
        self.check('916812')


    def test_sllw_x(self):
        self.feed('SLLW X')
        self.check('58')

    def test_sllw_y(self):
        self.feed('SLLW Y')
        self.check('9058')


    def test_sra_a(self):
        self.feed('SRA A')
        self.check('47')

    def test_sra_longmem(self):
        self.feed('SRA $1234')
        self.check('72571234')

    def test_sra_x(self):
        self.feed('SRA (X)')
        self.check('77')

    def test_sra_longoff_x(self):
        self.feed('SRA ($1234,X)')
        self.check('72471234')

    def test_sra_y(self):
        self.feed('SRA (Y)')
        self.check('9077')

    def test_sra_longoff_y(self):
        self.feed('SRA ($1234,Y)')
        self.check('90471234')

    def test_sra_longptr(self):
        self.feed('SRA [$1234]')
        self.check('72371234')

    def test_sra_longptr_x(self):
        self.feed('SRA ([$1234],X)')
        self.check('72671234')

    def test_sra_shortptr_y(self):
        self.feed('SRA ([$12],Y)')
        self.check('916712')


    def test_sraw_x(self):
        self.feed('SRAW X')
        self.check('57')

    def test_sraw_y(self):
        self.feed('SRAW Y')
        self.check('9057')


    def test_srl_a(self):
        self.feed('SRL A')
        self.check('44')

    def test_srl_longmem(self):
        self.feed('SRL $1234')
        self.check('72541234')

    def test_srl_x(self):
        self.feed('SRL (X)')
        self.check('74')

    def test_srl_longoff_x(self):
        self.feed('SRL ($1234,X)')
        self.check('72441234')

    def test_srl_y(self):
        self.feed('SRL (Y)')
        self.check('9074')

    def test_srl_longoff_y(self):
        self.feed('SRL ($1234,Y)')
        self.check('90441234')

    def test_srl_longptr(self):
        self.feed('SRL [$1234]')
        self.check('72341234')

    def test_srl_longptr_x(self):
        self.feed('SRL ([$1234],X)')
        self.check('72641234')

    def test_srl_shortptr_y(self):
        self.feed('SRL ([$12],Y)')
        self.check('916412')


    def test_srlw_x(self):
        self.feed('SRLW X')
        self.check('54')

    def test_srlw_y(self):
        self.feed('SRLW Y')
        self.check('9054')


    def test_sub_a_byte(self):
        self.feed('SUB A,#%00010010')
        self.check('A012')

    def test_sub_a_longmem(self):
        self.feed('SUB A,$1234')
        self.check('C01234')

    def test_sub_a_x(self):
        self.feed('SUB A,(X)')
        self.check('F0')

    def test_sub_a_longoff_x(self):
        self.feed('SUB A,($1234,X)')
        self.check('D01234')

    def test_sub_a_y(self):
        self.feed('SUB A,(Y)')
        self.check('90F0')

    def test_sub_a_longoff_y(self):
        self.feed('SUB A,($1234,Y)')
        self.check('90D01234')

    def test_sub_a_shortoff_sp(self):
        self.feed('SUB A,($12,SP)')
        self.check('1012')

    def test_sub_a_longptr(self):
        self.feed('SUB A,[$1234]')
        self.check('72C01234')

    def test_sub_a_longptr_x(self):
        self.feed('SUB A,([$1234],X)')
        self.check('72D01234')

    def test_sub_a_shortptr_y(self):
        self.feed('SUB A,([$12],Y)')
        self.check('91D012')


    def test_subw_x_word(self):
        self.feed('SUBW X,#$1234')
        self.check('1D1234')

    def test_subw_x_longmem(self):
        self.feed('SUBW X,$1234')
        self.check('72B01234')

    def test_subw_x_shortoff_sp(self):
        self.feed('SUBW X,($12,SP)')
        self.check('72F012')

    def test_subw_y_word(self):
        self.feed('SUBW Y,#$1234')
        self.check('72A21234')

    def test_subw_y_longmem(self):
        self.feed('SUBW Y,$1234')
        self.check('72B21234')

    def test_subw_y_shortoff_sp(self):
        self.feed('SUBW Y,($12,SP)')
        self.check('72F212')

    def test_subw_sp_byte(self):
        self.feed('SUBW SP,#$12')
        self.check('5212')


    def test_swap_a(self):
        self.feed('SWAP A')
        self.check('4E')

    def test_swap_longmem(self):
        self.feed('SWAP $1234')
        self.check('725E1234')

    def test_swap_x(self):
        self.feed('SWAP (X)')
        self.check('7E')

    def test_swap_longoff_x(self):
        self.feed('SWAP ($1234,X)')
        self.check('724E1234')

    def test_swap_y(self):
        self.feed('SWAP (Y)')
        self.check('907E')

    def test_swap_longoff_y(self):
        self.feed('SWAP ($1234,Y)')
        self.check('904E1234')

    def test_swap_longptr(self):
        self.feed('SWAP [$1234]')
        self.check('723E1234')

    def test_swap_longptr_x(self):
        self.feed('SWAP ([$1234],X)')
        self.check('726E1234')

    def test_swap_shortptr_y(self):
        self.feed('SWAP ([$12],Y)')
        self.check('916E12')


    def test_swapw_x(self):
        self.feed('SWAPW X')
        self.check('5E')

    def test_swapw_y(self):
        self.feed('SWAPW Y')
        self.check('905E')


    def test_tnz_a(self):
        self.feed('TNZ A')
        self.check('4D')

    def test_tnz_longmem(self):
        self.feed('TNZ $1234')
        self.check('725D1234')

    def test_tnz_x(self):
        self.feed('TNZ (X)')
        self.check('7D')

    def test_tnz_longoff_x(self):
        self.feed('TNZ ($1234,X)')
        self.check('724D1234')

    def test_tnz_y(self):
        self.feed('TNZ (Y)')
        self.check('907D')

    def test_tnz_longoff_y(self):
        self.feed('TNZ ($1234,Y)')
        self.check('904D1234')

    def test_tnz_longptr(self):
        self.feed('TNZ [$1234]')
        self.check('723D1234')

    def test_tnz_longptr_x(self):
        self.feed('TNZ ([$1234],X)')
        self.check('726D1234')

    def test_tnz_shortptr_y(self):
        self.feed('TNZ ([$12],Y)')
        self.check('916D12')


    def test_tnzw_x(self):
        self.feed('TNZW X')
        self.check('5D')

    def test_tnzw_y(self):
        self.feed('TNZW Y')
        self.check('905D')


    def test_xor_a_byte(self):
        self.feed('XOR A,#%00010010')
        self.check('A812')

    def test_xor_a_longmem(self):
        self.feed('XOR A,$1234')
        self.check('C81234')

    def test_xor_a_x(self):
        self.feed('XOR A,(X)')
        self.check('F8')

    def test_xor_a_longoff_x(self):
        self.feed('XOR A,($1234,X)')
        self.check('D81234')

    def test_xor_a_y(self):
        self.feed('XOR A,(Y)')
        self.check('90F8')

    def test_xor_a_longoff_y(self):
        self.feed('XOR A,($1234,Y)')
        self.check('90D81234')

    def test_xor_a_shortoff_sp(self):
        self.feed('XOR A,($12,SP)')
        self.check('1812')

    def test_xor_a_longptr(self):
        self.feed('XOR A,[$1234]')
        self.check('72C81234')

    def test_xor_a_longptr_x(self):
        self.feed('XOR A,([$1234],X)')
        self.check('72D81234')

    def test_xor_a_shortptr_y(self):
        self.feed('XOR A,([$12],Y)')
        self.check('91D812')



if __name__ == '__main__':
    unittest.main()
