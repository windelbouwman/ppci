"""
Test that we can run the official WASM spec test-suite.
We bypass our own parser here, at least for now.
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


# TODO: fix DeprecationWarning: Buffer() is deprecated
def tst_spec_suite_running():
    """ Test all our WASM parsing on the spec suite.
    """
    for fname in sorted(os.listdir(get_spec_suite_dir())):
        if fname.lower().endswith('.wast'):
            do_func(fname)


def do_func(fname):
    """ Test running on a single test file.
    Its great to call this at the botton during dev!
    """
    
    print('Testing {} - "{}"'.format(fname, os.path.join(get_spec_suite_dir(), fname)))
    
    mod = None
    
    for text in get_test_script_parts(fname):
        sexpr = parse_sexpr(text)
        exp_kind = sexpr[0]
        
        # Triage over toplevel expressions
        # https://github.com/WebAssembly/spec/blob/master/interpreter/README.md#s-expression-syntax
        
        if exp_kind == 'module':
            if 'binary' in sexpr:
                # Combine binary parts
                parts = None
                for elem in sexpr:
                    if parts is None:
                        if elem == 'binary':
                            parts = []
                    else:
                        parts.append(datastring2bytes(elem))
                data = b''.join(parts)
                # Load module from binary data
                mod = Module(data)
            else:
                # Load module from text, via wabt
                data = wabt.wat2wasm(text)
                mod = Module(data)
        
        elif exp_kind == 'register':
            raise NotImplementedError('I suppose we need this, but not sure how to do it yet.')
        
        elif exp_kind == 'invoke':
            raise NotImplementedError()
        
        elif exp_kind == 'assert_return':
            assert len(sexpr) == 3 and sexpr[1][0] == 'invoke'
            _, func_id, params = sexpr[1]
            expected_result = sexpr[2]
            raise NotImplementedError()
        
        elif expr_kind in ( 'assert_invalid', 'assert_trap',
                            'assert_malformed', 'assert_exhaustion', 'assert_unlinkable',
                            'assert_return_canonical_nan', 'assert_return_arithmetic_nan',
                            'func', 'memory',  # inline-module.wast
                            ):
            pass  # not implemented yet
        
        else:
            assert False, '{}: unexpected expression in'.format(fname)


if __name__ == '__main__':
    
    # testfunc('names.wast')
    test_spec_suite_running()
