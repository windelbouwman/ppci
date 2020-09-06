import logging
from ._instantiate import instantiate
from . import wasi


logger = logging.getLogger("wasm-execute")


def execute_wasm(
    module,
    args,
    target="python",
    function=None,
    function_args=(),
    reporter=None,
):
    """ Execute the given wasm module. """
    wasi_api = wasi.WasiApi(args)
    imports = {
        "wasi_unstable": {
            "args_sizes_get": wasi_api.args_sizes_get,
            "args_get": wasi_api.args_get,
            "clock_time_get": wasi_api.clock_time_get,
            "environ_sizes_get": wasi_api.environ_sizes_get,
            "environ_get": wasi_api.environ_get,
            "fd_prestat_get": wasi_api.fd_prestat_get,
            "fd_prestat_dir_name": wasi_api.fd_prestat_dir_name,
            "fd_fdstat_get": wasi_api.fd_fdstat_get,
            "fd_fdstat_set_flags": wasi_api.fd_fdstat_set_flags,
            "fd_close": wasi_api.fd_close,
            "fd_read": wasi_api.fd_read,
            "fd_seek": wasi_api.fd_seek,
            "fd_write": wasi_api.fd_write,
            "path_filestat_get": wasi_api.path_filestat_get,
            "path_open": wasi_api.path_open,
            "path_symlink": wasi_api.path_symlink,
            "path_unlink_file": wasi_api.path_unlink_file,
            "poll_oneoff": wasi_api.poll_oneoff,
            "proc_exit": wasi_api.proc_exit,
            "random_get": wasi_api.random_get,
        }
    }
    instance = instantiate(
        module, imports=imports, target=target, reporter=reporter
    )

    logger.info("Created instance %s", instance)

    # Hack hack hack, give wasi api access to the instance:
    # This is handy for memory access.
    wasi_api._instance = instance

    try:
        if function:
            # Run a specific function in the wasm module
            result = instance.exports[function](*function_args)
            print("Result:", result)
        else:
            # Assume WASI
            instance.exports["_start"]()
    except wasi.ProcExit as ex:
        logger.info("Process quit: {}".format(ex.exit_code))
