#!/usr/bin/python

import unittest
import io
from ppci import ir
from ppci.irutils import Builder, Writer
from ppci.codegen.irdag import SelectionGraphBuilder, DagSplitter
from ppci.codegen.irdag import FunctionInfo, prepare_function_info
from ppci.arch.example import ExampleArch
from ppci.binutils.debuginfo import DebugDb
from ppci.api import get_arch


def print_module(m):
    f = io.StringIO()
    Writer().write(m, f)
    print(f.getvalue())


class IrDagTestCase(unittest.TestCase):
    """ Test if ir dag works good """
    @unittest.skip('TODO')
    def test_phi_register(self):
        """ When a phi node is mapped to a register, this register
        can be written and used afterwards. This happens for example
        when the CSE-pass has not run, and the common sub expression is
        not eliminated


        This IR-code:

        procedure main()
          block0:
            i64 cnst = 2
            i64 cnst_0 = 0
            jump block2
          block1:
            strval = Literal b'040000000000000041203d20'
            io_print2(strval, phi_var_i_0)
            i64 cnst_4 = 1
            i64 binop = phi_var_i_0 + cnst_4
            i64 binop_5 = phi_var_b_0 * binop
            i64 cnst_7 = 1
            i64 binop_8 = phi_var_i_0 + cnst_7
            jump block2
          block2:
            i64 phi_var_i_0 = Phi {'block1': 'binop_8', 'block0': 'cnst_0'}
            i64 phi_var_b_0 = Phi {'block1': 'binop_5', 'block0': 'cnst'}
            i64 cnst_1 = 10
            if phi_var_i_0 < cnst_1 then block1 else block3
          block3:
            strval_9 = Literal b'040000000000000042203d20'
            io_print2(strval_9, phi_var_b_0)
            exit

        Generates this tree list:

        block0:
          MOVI64[vreg0phi_var_i_0](CONSTI64[0])
          MOVI64[vreg1phi_var_b_0](CONSTI64[2])
          JMP[main_main_block_block2:]
        block1:
          MOVI64[vreg4](LABEL[main_main_literal_1])
          MOVI64[vreg5](REGI64[vreg0phi_var_i_0])
          CALL[('io_print2', [ptr, i64], [vreg4, vreg5])]
          MOVI64[vreg0phi_var_i_0](ADDI64(REGI64[vreg0phi_var_i_0], CONSTI64[1]))
          MOVI64[vreg1phi_var_b_0](MULI64(REGI64[vreg1phi_var_b_0], ADDI64(REGI64[vreg0phi_var_i_0], CONSTI64[1])))  <---- Here vreg0phi_var_i_0 is re-defined!
          JMP[main_main_block_block2:]
        block2:
          MOVI64[vreg0phi_var_i_0](REGI64[vreg0phi_var_i_0])
          MOVI64[vreg1phi_var_b_0](REGI64[vreg1phi_var_b_0])
          CJMP[('<', main_main_block_block1:, main_main_block_block3:)](REGI64[vreg0phi_var_i_0], CONSTI64[10])
        block3:
          MOVI64[vreg2](LABEL[main_main_literal_0])
          MOVI64[vreg3](REGI64[vreg1phi_var_b_0])
          CALL[('io_print2', [ptr, i64], [vreg2, vreg3])]
          JMP[main_main_epilog:]
        """

        # TODO: implement test case!!
        pass

    def test_bug2(self):
        """ Check that if blocks are in function in strange order, the dag
        builder works """
        module = ir.Module('dut')
        function = ir.Procedure('tst')
        module.add_function(function)
        block1 = ir.Block('b1')
        block2 = ir.Block('b2')
        function.add_block(block1)
        function.add_block(block2)
        function.entry = block2
        con = ir.Const(2, 'con', ir.i32)
        block2.add_instruction(con)
        block2.add_instruction(ir.Jump(block1))
        block1.add_instruction(ir.Cast(con, 'con_cast', ir.i8))
        block1.add_instruction(ir.Exit())

        # Target generation
        target = get_arch('arm')
        frame = target.new_frame('a', function)
        function_info = FunctionInfo(frame)
        debug_db = DebugDb()
        prepare_function_info(target, function_info, function)
        dag_builder = SelectionGraphBuilder(target, debug_db)
        sgraph = dag_builder.build(function, function_info)
        dag_splitter = DagSplitter(target, debug_db)

    def test_bug1(self):
        """
            This is the bug:

            function XXX sleep(i32 ms)
              entry:
                JUMP block12
              block12:
                i32 loaded = load global_tick
                i32 binop = loaded + ms
                JUMP block14
              block14:
                i32 loaded_2 = load global_tick
                IF binop > loaded_2 THEN block14 ELSE epilog
              epilog:
                exit

            Selection graph for function XXX sleep(i32 ms)

            entry:
                MOVI32[vreg0ms](REGI32[R1])
                JMP[bsp_sleep_block12:]
            block12:
                MOVI32[vreg1loaded](LDRI32(LABEL[bsp_global_tick]))
                JMP[bsp_sleep_block14:]
            block14:
                MOVI32[vreg4loaded_2](LDRI32(LABEL[bsp_global_tick]))
                CJMP[('>', bsp_sleep_block14:, bsp_sleep_epilog:)]
                    (REGI32[vreg5binop], REGI32[vreg4loaded_2])
            epilog:
        """
        builder = Builder()
        module = ir.Module('fuzz')
        global_tick = ir.Variable('global_tick', 4)
        module.add_variable(global_tick)
        builder.module = module
        function = builder.new_procedure('sleep')
        ms = ir.Parameter('ms', ir.i32)
        function.add_parameter(ms)
        builder.set_function(function)
        entry = builder.new_block()
        function.entry = entry
        builder.set_block(entry)
        block12 = builder.new_block()
        builder.emit(ir.Jump(block12))
        builder.set_block(block12)
        loaded = builder.emit(ir.Load(global_tick, 'loaded', ir.i32))
        binop = builder.emit(ir.Binop(loaded, '+', ms, 'binop', ir.i32))
        block14 = builder.new_block()
        builder.emit(ir.Jump(block14))
        builder.set_block(block14)
        loaded2 = builder.emit(ir.Load(global_tick, 'loaded2', ir.i32))
        epilog = builder.new_block()
        builder.emit(ir.CJump(binop, '>', loaded2, block14, epilog))
        builder.set_block(epilog)
        builder.emit(ir.Exit())
        # print('module:')
        # print_module(module)

        # Target generation
        target = ExampleArch()
        frame = target.new_frame('a', function)
        function_info = FunctionInfo(frame)
        debug_db = DebugDb()
        prepare_function_info(target, function_info, function)
        dag_builder = SelectionGraphBuilder(target, debug_db)
        sgraph = dag_builder.build(function, function_info)
        dag_splitter = DagSplitter(target, debug_db)

        # print(function_info.value_map)
        for b in function:
            # root = function_info.block_roots[b]
            #print('root=', root)
            #for tree in dag_splitter.split_into_trees(root, frame):
            #    print('tree=', tree)
            pass
        # sg_value = function_info.value_map[binop]
        # print(function_info.value_map)
        # self.assertTrue(sg_value.vreg)


if __name__ == '__main__':
    unittest.main()
