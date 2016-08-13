from ..encoding import Register, Syntax



class Stm8Register(Register):
    syntaxi = 'register', [Syntax(['a'],  new_func=lambda: A),
                           Syntax(['xl'], new_func=lambda: XL),
                           Syntax(['xh'], new_func=lambda: XH),
                           Syntax(['x'],  new_func=lambda: X),
                           Syntax(['yl'], new_func=lambda: YL),
                           Syntax(['yh'], new_func=lambda: YH),
                           Syntax(['y'],  new_func=lambda: Y),
                           Syntax(['sp'], new_func=lambda: SP),
                           Syntax(['pc'], new_func=lambda: PC),
                           Syntax(['cc'], new_func=lambda: CC)]



class Stm88BitRegister(Stm8Register):
    bitsize = 8
    syntaxi = '8bit_register', [Syntax(['a'],  new_func=lambda: A),
                                Syntax(['xl'], new_func=lambda: XL),
                                Syntax(['xh'], new_func=lambda: XH),
                                Syntax(['yl'], new_func=lambda: YL),
                                Syntax(['yh'], new_func=lambda: YH),
                                Syntax(['cc'], new_func=lambda: CC)]

class Stm816BitRegister(Stm8Register):
    bitsize = 16
    syntaxi = '16bit_register', [Syntax(['x'],  new_func=lambda: X),
                                 Syntax(['y'],  new_func=lambda: Y),
                                 Syntax(['sp'], new_func=lambda: SP)]

class Stm824BitRegister(Stm8Register):
    bitsize = 24
    syntaxi = '24bit_register', [Syntax(['pc'], new_func=lambda: PC)]



class Stm8AccumulatorRegister(Stm88BitRegister):
    syntaxi = 'accumulator_register', [Syntax(['a'], new_func=lambda: A)]


class Stm8IndexLowRegister(Stm88BitRegister):
    syntaxi = 'index_low_register', [Syntax(['xl'], new_func=lambda: XL),
                                     Syntax(['yl'], new_func=lambda: YL)]

class Stm8IndexHighRegister(Stm88BitRegister):
    syntaxi = 'index_high_register', [Syntax(['xh'], new_func=lambda: XH),
                                      Syntax(['yh'], new_func=lambda: YH)]

class Stm8IndexRegister(Stm816BitRegister):
    syntaxi = 'index_register', [Syntax(['x'], new_func=lambda: X),
                                 Syntax(['y'], new_func=lambda: Y)]


class Stm8StackPointerRegister(Stm816BitRegister):
    syntaxi = 'stack_pointer_register', [Syntax(['sp'], new_func=lambda: SP)]


class Stm8ProgramCounterRegister(Stm824BitRegister):
    syntaxi = 'program_counter_register', [Syntax(['pc'], new_func=lambda: PC)]


class Stm8ConditionCodeRegister(Stm88BitRegister):
    syntaxi = 'condition_code_register', [Syntax(['cc'], new_func=lambda: CC)]



class Stm8RegisterA(Stm8AccumulatorRegister):
    syntaxi = 'register_a', [Syntax(['a'], new_func=lambda: A)]


class Stm8RegisterXL(Stm8IndexLowRegister):
    syntaxi = 'register_xl', [Syntax(['xl'], new_func=lambda: XL)]

class Stm8RegisterXH(Stm8IndexHighRegister):
    syntaxi = 'register_xh', [Syntax(['xh'], new_func=lambda: XH)]

class Stm8RegisterX(Stm8IndexRegister):
    syntaxi = 'register_x', [Syntax(['x'], new_func=lambda: X)]


class Stm8RegisterYL(Stm8IndexLowRegister):
    syntaxi = 'register_yl', [Syntax(['yl'], new_func=lambda: YL)]

class Stm8RegisterYH(Stm8IndexHighRegister):
    syntaxi = 'register_yh', [Syntax(['yh'], new_func=lambda: YH)]

class Stm8RegisterY(Stm8IndexRegister):
    syntaxi = 'register_y', [Syntax(['y'], new_func=lambda: Y)]


class Stm8RegisterSP(Stm8StackPointerRegister):
    syntaxi = 'register_sp', [Syntax(['sp'], new_func=lambda: SP)]


class Stm8RegisterPC(Stm8ProgramCounterRegister):
    syntaxi = 'register_pc', [Syntax(['pc'], new_func=lambda: PC)]


class Stm8RegisterCC(Stm8ConditionCodeRegister):
    syntaxi = 'register_cc', [Syntax(['cc'], new_func=lambda: CC)]



A = Stm8RegisterA('A')

XL = Stm8RegisterXL('XL')
XH = Stm8RegisterXH('XH')
X = Stm8RegisterX('X', aliases=(XL, XH))

YL = Stm8RegisterYL('YL')
YH = Stm8RegisterYH('YH')
Y = Stm8RegisterY('Y', aliases=(YL, YH))

SP = Stm8RegisterSP('SP')

PC = Stm8RegisterPC('PC')

CC = Stm8RegisterCC('CC')
