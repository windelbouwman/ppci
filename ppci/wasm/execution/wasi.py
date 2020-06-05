""" WASI API.

These are some of the WASI api functions implemented in python.

See also: https://wasi.dev
"""

import time
import logging
import struct
from ... import ir

ESUCCESS = 0
EBADF = 8
EINVAL = 28

PREOPENTYPE_DIR = 0

FILETYPE_BLOCK_DEVICE = 1
FILETYPE_CHARACTER_DEVICE = 2
FILETYPE_DIRECTORY = 3
FILETYPE_REGULAR_FILE = 4

FDFLAG_APPEND = 0x1
FDFLAG_DSYNC = 0x2
FDFLAG_NONBLOCK = 0x4
FDFLAG_RSYNC = 0x8
FDFLAG_SYNC = 0x10


class WasiApi:
    logger = logging.getLogger("wasi")

    def __init__(self):
        self._instance = None

        self._available_fd = {
            3: ".",
        }

    def _write_mem_u8(self, address: int, value: int):
        self._write_mem_fmt(address, "<B", value)

    def _write_mem_u16(self, address: int, value: int):
        self._write_mem_fmt(address, "<H", value)

    def _write_mem_u32(self, address: int, value: int):
        self._write_mem_fmt(address, "<I", value)

    def _write_mem_u64(self, address: int, value: int):
        self._write_mem_fmt(address, "<Q", value)

    def _write_mem_fmt(self, address: int, fmt: str, value: int):
        data = struct.pack(fmt, value)
        self._write_mem_data(address, data)

    def _write_mem_data(self, address, data: bytes):
        memory = self._instance.exports["memory"]
        memory.write(address, data)

    def _read_mem_u16(self, address: int) -> int:
        return self._read_mem_fmt(address, "<H")

    def _read_mem_u32(self, address: int) -> int:
        return self._read_mem_fmt(address, "<I")

    def _read_mem_u64(self, address: int) -> int:
        return self._read_mem_fmt(address, "<Q")

    def _read_mem_fmt(self, address: int, fmt: str):
        size = struct.calcsize(fmt)
        data = self._read_mem_data(address, size)
        return struct.unpack(fmt, data)[0]

    def _read_mem_data(self, address: int, size: int) -> bytes:
        memory = self._instance.exports["memory"]
        return memory.read(address, size)

    def fd_prestat_get(self, fd: ir.i32, buf: ir.i32) -> ir.i32:
        self.logger.debug("fd_prestat_get(%s, %s)", fd, buf)
        if fd in self._available_fd:
            self._write_mem_u32(buf, PREOPENTYPE_DIR)
            name_len = len(self._available_fd[fd])
            self._write_mem_u32(buf + 4, name_len)
            return ESUCCESS
        else:
            return EBADF

    def fd_prestat_dir_name(
        self, fd: ir.i32, path: ir.i32, path_len: ir.i32
    ) -> ir.i32:
        self.logger.debug(
            "fd_prestat_dir_name(%s, %s, %s)", fd, path, path_len
        )
        if fd in self._available_fd:
            path_str = self._available_fd[fd]
            assert path_len == len(path_str)
            path_data = path_str.encode("ascii")
            self._write_mem_data(path, path_data)
            # raise NotImplementedError()
            return ESUCCESS
        else:
            return EBADF

    def clock_time_get(
        self, id: ir.i32, precision: ir.i64, timestamp_ptr: ir.i32
    ) -> ir.i32:
        self.logger.debug("clock_time_get called!")
        nanos = int(time.time() * 1e9)
        self._write_mem_u64(timestamp_ptr, nanos)
        return ESUCCESS

    def proc_exit(self, code: ir.i32) -> None:
        self.logger.debug("proc_exit(%s)", code)
        raise NotImplementedError()

    def fd_fdstat_get(self, fd: ir.i32, fdstat: ir.i32) -> ir.i32:
        self.logger.debug("fd_fdstat_get(%s, %s)", fd, fdstat)
        # assert fd == 0
        if fd in self._available_fd:
            fs_filetype = FILETYPE_DIRECTORY
            fs_flags = 0

            fs_rights_base = 2 ** 64 - 1
            fs_rights_inheriting = 2 ** 64 - 1
            self._write_mem_u8(fdstat, fs_filetype)
            self._write_mem_u16(fdstat + 2, fs_flags)
            self._write_mem_u64(fdstat + 8, fs_rights_base)
            self._write_mem_u64(fdstat + 16, fs_rights_inheriting)
            # raise NotImplementedError()
            return ESUCCESS
        else:
            return EBADF

    def fd_close(self, fd: ir.i32) -> ir.i32:
        self.logger.debug("TODO: fd_close")
        raise NotImplementedError()
        return ESUCCESS

    def args_sizes_get(
        self, argc_ptr: ir.i32, argv_buf_size_ptr: ir.i32
    ) -> ir.i32:
        self.logger.debug(
            "args_sizes_get(%s, %s)", argc_ptr, argv_buf_size_ptr
        )
        self._write_mem_u32(argc_ptr, 0)
        self._write_mem_u32(argv_buf_size_ptr, 0)
        return ESUCCESS

    def args_get(self, argv: ir.i32, argv_buf: ir.i32) -> ir.i32:
        self.logger.debug("args_get(%s, %s)", argv, argv_buf)
        # raise NotImplementedError()
        return ESUCCESS

    def fd_seek(self, a: ir.i32, b: ir.i64, c: ir.i32, d: ir.i32) -> ir.i32:
        raise NotImplementedError()

    def fd_write(
        self, fd: ir.i32, iovs: ir.i32, iovs_len: ir.i32, n_written: ir.i32
    ) -> ir.i32:
        self.logger.debug("fd_write %s iovs!", iovs_len)

        total_bytes = 0

        # Loop over all iovs:
        for i in range(iovs_len):
            ciovec_offset = iovs + i * 8
            buf_addr = self._read_mem_u32(ciovec_offset)
            buf_size = self._read_mem_u32(ciovec_offset + 4)
            self.logger.debug(
                "Read %s bytes from address %s", buf_size, buf_addr
            )
            data = self._read_mem_data(buf_addr, buf_size)
            total_bytes += len(data)

            # Assume standard output:
            import os
            os.write(1, data)
            # print(data.decode("ascii", errors="ignore"), end="")
            # sys.stdout.write(data)

        self._write_mem_u32(n_written, total_bytes)
        return ESUCCESS

    def environ_sizes_get(
        self, environc_ptr: ir.i32, environ_buf_size_ptr: ir.i32
    ) -> ir.i32:
        self.logger.debug(
            "environ_sizes_get(%s, %s)", environc_ptr, environ_buf_size_ptr
        )
        # TODO
        self._write_mem_u32(environc_ptr, 0)
        self._write_mem_u32(environ_buf_size_ptr, 0)
        return ESUCCESS

    def environ_get(self, environ: ir.i32, environ_buf: ir.i32) -> ir.i32:
        self.logger.debug("environ_get(%s, %s)", environ, environ_buf)
        # TODO
        return ESUCCESS
