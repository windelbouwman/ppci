
from io import StringIO

from ppci import irutils 

from ppci.programs import IntermediateProgram

from ppci import irutils
from ppci.ir import Module as IrModule
from ppci.api import ir_to_object, get_arch, link, optimize

from ppci.lang.python import ir_to_python


class IrProgram(IntermediateProgram):
    """ PPCI IR code is the intermediate representation used in PPCI.
    """
    
    def _check_items(self, items):
        for item in items:
            assert isinstance(item, IrModule)
        return items
    
    def _copy(self):
        raise NotImplementedError()
        
    def _get_report(self, html):
        
        pieces = []
        for m in self.items:
            f = StringIO()
            irutils.Writer(f).write(m, verify=False)
            pieces.append(f.getvalue())
        return '\n\n==========\n\n'.join(pieces)
    
    def to_x86(self, **options):
        """ Compile to X86 machine code.
        
        Status: ...
        """
        
        if options.get('win', ''):
            arch = get_arch('x86_64:wincc')
        else:
            arch = get_arch('x86_64')
        
        # todo: don't we want to be able to pass debug_db here?
        ppci_modules = [m for m in self.items]
        if self.debugdb:
            ob = ir_to_object(ppci_modules, arch, debug=True)#, debug_db=self.debugdb
        else:
            ob = ir_to_object(ppci_modules, arch, debug=False)
        
        return self._new('x86', [ob])
    
    def to_python(self, **options):
        """ Compile PPCI IR to Python. Not very efficient or pretty code,
        but it can be useful to test the IR code without compiling to machine code.
        
        Status: complete: can compile the full IR spec.
        """
        
        # pieces = []
        # for m in self.items:
        #     
        #     pythonizer = ir_to_python.IrToPython(f)
        #     pythonizer.header()
        #     pythonizer.generate(m)
        #     py_code = f.getvalue()
        #     pieces.append(py_code)
        
        f = StringIO()
        ir_to_python(self.items, f)
        code = f.getvalue()
        
        return self._new('python', [code])
    
    def to_wasm(self, **options):
        """ Compile PPCI IR to WASM.
        """
        raise NotImplementedError()
        #return self._new('wasm', wasm_modules)
