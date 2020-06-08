""" Provide function to load a wasm module into the current process.

Note that for this to work, we require compiled wasm code and a runtime.

The wasm runtime contains the following:

- Implement function like sqrt, floor, bit rotations etc..
"""


from ...utils.reporting import DummyReportGenerator
from .runtime import create_runtime
from ..components import Import
from ._native_instance import native_instantiate
from ._python_instance import python_instantiate


__all__ = ("instantiate",)


def instantiate(
    module, imports, target="native", reporter=None, cache_file=None
):
    """ Instantiate a wasm module.

    Args:
        module (ppci.wasm.Module): The wasm-module to instantiate
        imports: A collection of functions available to the wasm module.
        target: Use 'native' to compile wasm to machine code.
                Use 'python' to generate python code. This option is slower
                but more reliable.
        reporter: A reporter which can record detailed compilation information.
        cache_file: a file to use as cache

    """
    if reporter is None:
        reporter = DummyReportGenerator()

    reporter.heading(2, "Wasm instantiation")

    if "wasm_rt" in imports:
        raise ValueError("wasm_rt is a special import section")

    symbols = {}
    # Check if all required imports are given:
    for definition in module:
        if isinstance(definition, Import):
            modname, name = definition.modname, definition.name
            if modname not in imports:
                raise ValueError(
                    'imported module "{}" not found'.format(modname)
                )
            if name not in imports[modname]:
                raise ValueError(
                    'imported object "{}" not found in "{}"'.format(
                        name, modname
                    )
                )
            symbols["{}_{}".format(modname, name)] = imports[modname][name]

    # Inject wasm runtime functions:
    for func_name, func in create_runtime().items():
        symbols["wasm_rt_{}".format(func_name)] = func

    if target == "native":
        instance = native_instantiate(module, symbols, reporter, cache_file)
    elif target == "python":
        instance = python_instantiate(module, symbols, reporter, cache_file)
    else:
        raise ValueError("Unknown instantiation target {}".format(target))

    # Initialize memory:
    instance.load_memory(module)

    instance.populate_exports(module)

    # Call magic function _run_init which initializes tables and optionally
    # calls start function as defined by the wasm start section.
    instance._run_init()
    return instance
