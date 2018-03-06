import io
from ppci import wasm
from ppci.api import ir_to_object, get_current_arch
from ppci.utils.codepage import load_obj
from ppci.binutils.outstream import TextOutputStream

from ppci.wasm import wasm_to_ir, export_wasm_example

wasm_module = wasm.Module(
    ('import', 'py', 'add', ('func', '$add', ('param', 'i64', 'i64'), ('result', 'i64'))),
    ('func', ('export', 'main'), ('param', 'i64'), ('result', 'i64'),
        ('get_local', 0),
        ('i64.const', 42),
        ('call', '$add'),
    )
)

print(wasm_module.to_string())

ppci_module = wasm_to_ir(wasm_module)
ppci_module.display()

arch = get_current_arch()
print('using this arch: ', arch)
f = io.StringIO()
txt_stream = TextOutputStream(f=f, add_binary=True)
obj = ir_to_object([ppci_module], arch, debug=True, outstream=txt_stream)
print(f.getvalue())

def my_add(x: int, y: int) -> int:
    print('my add called', x, y)
    return x + y + 1

# Run in memory
imports = {
    'py_add': my_add
}

native_module = load_obj(obj, imports=imports)
print(dir(native_module))
result = getattr(native_module, '0')(42)
print(result, '(should be 85)')
