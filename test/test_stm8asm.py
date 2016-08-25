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
        self.feed('BTJF $1234,#5,label')
        self.check('720B123400')


    def test_btjt(self):
        self.feed('BTJT $1234,#5,label')
        self.check('720A123400')


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


    def test_divw_x_y(self):
        self.feed('DIV X,Y')
        self.check('65')


    def test_nop(self):
        self.feed('NOP')
        self.check('9D')



if __name__ == '__main__':
    unittest.main()
