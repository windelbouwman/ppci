""" Test that we do the parsing of .wat correctly.
"""

import os
import sys

from ppci.wasm import read_wat, Module
from ppci.wasm import wabt
from ppci.lang.sexpr import parse_sexpr
from ppci.utils.hexdump import hexdump
from ppci.wasm.util import datastring2bytes

# Load spec test-suite iterator
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from _spec_suite import get_spec_suite_dir, get_test_script_parts
sys.path.pop(0)


def test_spec_suite_parsing():
    """ Test all our .wat parsing on the spec suite.
    """
    for fname in sorted(os.listdir(get_spec_suite_dir())):
        if fname.lower().endswith('.wast'):
            testfunc(fname)


def testfunc(fname):
    """ Test parsing on a single test file.
    Its great to call this at the botton during dev!
    """
    
    print('Testing {} - "{}"'.format(fname, os.path.join(get_spec_suite_dir(), fname)))
    
    for text in get_test_script_parts(fname):
        sexpr = parse_sexpr(text)
        
        # Assert that the toplevel expression makes sense
        assert sexpr[0] in ('module', 'invoke', 'register',
                            'assert_return', 'assert_invalid', 'assert_trap',
                            'assert_malformed', 'assert_exhaustion', 'assert_unlinkable',
                            'assert_return_canonical_nan', 'assert_return_arithmetic_nan',
                            'func', 'memory',  # inline-module.wast
                            ), '{}: unexpected expression in'.format(fname)
        
        # But in this script we only do modules
        if sexpr[0] != 'module':
            continue
        
        # todo: skipping a few here, for now
        if fname in ('names.wast', 'comments.wast',  # because sending Unicode over Pipes seems to go wrong
                     ):
            continue
        
        wasm_bin0 = wabt.wat2wasm(text)
        
        m1 = Module(wasm_bin0)
        m2 = Module(text)
        m3 = Module(sexpr)
        
        wasm_bin1 = m1.to_bytes()
        wasm_bin2 = m2.to_bytes()
        wasm_bin3 = m3.to_bytes()
        
        assert wasm_bin0 == wasm_bin1, '{}: our binary parsing is broken'.format(fname)
        assert wasm_bin2 == wasm_bin3, '{}: our text/tuple paring differs'.format(fname)
        assert wasm_bin0 == wasm_bin2, '{}: our text parsing is broken'.format(fname)
        
        if False:  # debug helpers
            print(len(wasm_bin1), len(wasm_bin2))
            print(len(m1.definitions), len(m2.definitions))
            hexdump(wasm_bin1); print(); hexdump(wasm_bin2)
        

if __name__ == '__main__':
    testfunc('address.wast')
    # testfunc('names.wast')
    
    # test_spec_suite_parsing()
