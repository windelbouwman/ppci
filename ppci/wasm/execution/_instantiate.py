"""Provide function to load a wasm module into the current process.

Note that for this to work, we require compiled wasm code and a runtime.

The wasm runtime contains the following:

- Implement function like sqrt, floor, bit rotations etc..
"""

from ...utils.reporting import DummyReportGenerator
from .runtime import create_runtime
from ..components import Import
from ._native_instance import native_instantiate
from ._python_instance import python_instantiate
from ._base_instance import ModuleInstance


__all__ = ("instantiate",)


def instantiate(
    module, imports=None, target="native", reporter=None, cache_file=None
) -> ModuleInstance:
    """Instantiate a wasm module.

    Args:
        module (ppci.wasm.Module): The wasm-module to instantiate
        imports: A collection of functions available to the wasm module.
        target: Use 'native' to compile wasm to machine code.
                Use 'python' to generate python code. This option is slower
                but more reliable.
        reporter: A reporter which can record detailed compilation information.
        cache_file: a file to use as cache

    """
    if imports is None:
        imports = {}

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
                raise ValueError(f'imported module "{modname}" not found')
            if name not in imports[modname]:
                raise ValueError(
                    f'imported object "{name}" not found in "{modname}"'
                )
            symbols[f"{modname}_{name}"] = imports[modname][name]

    # Inject wasm runtime functions:
    for func_name, func in create_runtime().items():
        symbols[f"wasm_rt_{func_name}"] = func

    if target == "native":
        instance = native_instantiate(module, symbols, reporter, cache_file)
    elif target == "python":
        instance = python_instantiate(module, symbols, reporter, cache_file)
    else:
        raise ValueError(f"Unknown instantiation target {target}")

    # Init globals and elements by invoking run init:
    instance.invoke("_run_init")

    instance.load_globals(module)
    instance.load_tables(module)

    # Initialize memory:
    instance.load_memory(module)

    instance.populate_exports(module)

    # calls start function as defined by the wasm start section.
    if instance._wasm_info.start_name is not None:
        instance.invoke(instance._wasm_info.start_name)
    return instance
