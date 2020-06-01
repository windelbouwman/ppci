import logging
from ._instantiate import instantiate
from . import wasi


logger = logging.getLogger("wasm-execute")


def execute_wasm(module, args, target="python", function=None, reporter=None):
    """ Execute the given wasm module. """
    wasi_api = wasi.WasiApi()
    imports = {
        "wasi_unstable": {
            "fd_prestat_get": wasi_api.fd_prestat_get,
            "fd_prestat_dir_name": wasi_api.fd_prestat_dir_name,
            "clock_time_get": wasi_api.clock_time_get,
            "proc_exit": wasi_api.proc_exit,
            "fd_fdstat_get": wasi_api.fd_fdstat_get,
            "fd_close": wasi_api.fd_close,
            "args_sizes_get": wasi_api.args_sizes_get,
            "args_get": wasi_api.args_get,
            "fd_seek": wasi_api.fd_seek,
            "fd_write": wasi_api.fd_write,
            "environ_sizes_get": wasi_api.environ_sizes_get,
            "environ_get": wasi_api.environ_get,
        }
    }
    instance = instantiate(module, imports, target=target, reporter=reporter)

    logger.info("Created instance %s", instance)

    # Hack hack hack, give wasi api access to the instance:
    # This is handy for memory access.
    wasi_api._instance = instance

    if function:
        # Run a specific function in the wasm module
        result = instance.exports[function](*args)
        print("Result:", result)
    else:
        # Assume WASI
        instance.exports["_start"]()
