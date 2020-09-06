""" WASI API.

These are some of the WASI api functions implemented in python.

See also: https://wasi.dev
"""

import time
import os
import logging
import stat
import struct
from ... import ir


ESUCCESS = 0
E2BIG = 1
EACCES = 2
EADDRINUSE = 3
EADDRNOTAVAIL = 4
EAFNOSUPPORT = 5
EAGAIN = 6
EALREADY = 7
EBADF = 8
EBADMSG = 9
EBUSY = 10
ECANCELED = 11
ECHILD = 12
ECONNABORTED = 13
ECONNREFUSED = 14
ECONNRESET = 15
EDEADLK = 16
EDESTADDRREQ = 17
EDOM = 18
EDQUOT = 19
EEXIST = 20
EFAULT = 21
EFBIG = 22
EHOSTUNREACH = 23
EIDRM = 24
EILSEQ = 25
EINPROGRESS = 26
EINTR = 27
EINVAL = 28
EIO = 29
EISCONN = 30
EISDIR = 31
ELOOP = 32
EMFILE = 33
EMLINK = 34
EMSGSIZE = 35
EMULTIHOP = 36

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


class ProcExit(RuntimeError):
    """WASI process exit.

    Having an exception for this allows catching it, and cleanly shutting down.
    """

    def __init__(self, exit_code):
        super().__init__()
        self.exit_code = exit_code


def encode_strings(items):
    """Encode a sequence of strings into a binary blob
    with zero terminated bytes and a list with offsets
    into this blob.
    """
    blob = bytearray()
    offsets = []
    for item in items:
        offset = len(blob)
        data = item.encode("utf8") + bytes([0])

        blob.extend(data)
        offsets.append(offset)

    return blob, offsets


class WasiApi:
    logger = logging.getLogger("wasi")

    def __init__(self, args):
        self._instance = None
        self._trace_calls = True

        self._args = ["prog1337.wasm"] + args
        self._encoded_args = encode_strings(self._args)

        self._env = {}
        env_entries = ["{}={}".format(k, v) for k, v in self._env.items()]
        self._encoded_env = encode_strings(env_entries)

        # 0 -> stdin
        # 1 -> stdout
        # 2 -> stderr
        self._available_fd = {
            3: ".",
        }
        self._next_fd = 7

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

    def _read_string(self, address: int, size: int) -> str:
        data = self._read_mem_data(address, size)
        return data.decode("utf8")

    def _trace(self, txt):
        """ Trace execution. """
        if self._trace_calls:
            self.logger.debug(txt)

    def args_sizes_get(
        self, argc_ptr: ir.i32, argv_buf_size_ptr: ir.i32
    ) -> ir.i32:
        """Get sizes of arguments passed to the WASI program."""
        self._trace(
            "args_sizes_get(argc_ptr={}, {})".format(
                argc_ptr, argv_buf_size_ptr
            )
        )
        blob, offsets = self._encoded_args
        argc = len(offsets)
        buf_size = len(blob)
        self._write_mem_u32(argc_ptr, argc)
        self._write_mem_u32(argv_buf_size_ptr, buf_size)
        return ESUCCESS

    def args_get(self, argv: ir.i32, argv_buf: ir.i32) -> ir.i32:
        self._trace("args_get(argv={}, {})".format(argv, argv_buf))
        blob, offsets = self._encoded_args

        # Table with pointers:
        for nr, offset in enumerate(offsets):
            address = argv_buf + offset
            self._write_mem_u32(argv + 4 * nr, address)

        # Actual buffer with the data:
        self._write_mem_data(argv_buf, blob)

        return ESUCCESS

    def clock_time_get(
        self, id: ir.i32, precision: ir.i64, timestamp_ptr: ir.i32
    ) -> ir.i32:
        self._trace("clock_time_get(id={})".format(id))
        nanos = int(time.time() * 1e9)
        self._write_mem_u64(timestamp_ptr, nanos)
        return ESUCCESS

    def environ_sizes_get(
        self, environc_ptr: ir.i32, environ_buf_size_ptr: ir.i32
    ) -> ir.i32:
        self._trace(
            "environ_sizes_get(environc_ptr={}, environ_buf_size_ptr={})".format(
                environc_ptr, environ_buf_size_ptr
            )
        )
        blob, offsets = self._encoded_env

        self._write_mem_u32(environc_ptr, len(offsets))
        self._write_mem_u32(environ_buf_size_ptr, len(blob))
        return ESUCCESS

    def environ_get(self, environ: ir.i32, environ_buf: ir.i32) -> ir.i32:
        self._trace(
            "environ_get(environ={}, environ_buf={})".format(
                environ, environ_buf
            )
        )
        blob, offsets = self._encoded_env

        # Fill table with pointers:
        for nr, offset in enumerate(offsets):
            address = environ_buf + offset
            self._write_mem_u32(environ + 4 * nr, address)

        # Fill memory buffer:
        self._write_mem_data(environ_buf, blob)
        return ESUCCESS

    def fd_prestat_get(self, fd: ir.i32, buf: ir.i32) -> ir.i32:
        self._trace("fd_prestat_get(fd={}, buf={})".format(fd, buf))
        if fd in self._available_fd:
            path_str = self._available_fd[fd]
            if isinstance(path_str, str):
                self._write_mem_u32(buf, PREOPENTYPE_DIR)
                name_len = len(path_str)
                self._write_mem_u32(buf + 4, name_len)
                return ESUCCESS
            else:
                return EBADF
        else:
            return EBADF

    def fd_prestat_dir_name(
        self, fd: ir.i32, path: ir.i32, path_len: ir.i32
    ) -> ir.i32:
        self._trace(
            "fd_prestat_dir_name(fd={}, {}, {})".format(fd, path, path_len)
        )
        if fd in self._available_fd:
            path_str = self._available_fd[fd]
            if isinstance(path_str, str):
                assert path_len == len(path_str)
                path_data = path_str.encode("ascii")
                self._write_mem_data(path, path_data)
                return ESUCCESS
            else:
                return EBADF
        else:
            return EBADF

    def fd_fdstat_get(self, fd: ir.i32, fdstat: ir.i32) -> ir.i32:
        self._trace("fd_fdstat_get(fd={}, fdstat={})".format(fd, fdstat))
        # assert fd == 0
        if fd in self._available_fd:
            path_str = self._available_fd[fd]
            if isinstance(path_str, str):
                fs_filetype = FILETYPE_DIRECTORY
                fs_flags = 0

                fs_rights_base = 2 ** 64 - 1
                fs_rights_inheriting = 2 ** 64 - 1
                self._write_mem_u8(fdstat, fs_filetype)
                self._write_mem_u16(fdstat + 2, fs_flags)
                self._write_mem_u64(fdstat + 8, fs_rights_base)
                self._write_mem_u64(fdstat + 16, fs_rights_inheriting)

                return ESUCCESS
            else:
                return EBADF
        else:
            return EBADF

    def fd_fdstat_set_flags(self, fd: ir.i32, fdflags: ir.i32) -> ir.i32:
        self.logger.error(
            "fd_fdstat_set_flags(fd=%s, fdflags=%s)", fd, fdflags
        )
        return EACCES

    def fd_close(self, fd: ir.i32) -> ir.i32:
        self._trace("fd_close(fd={})".format(fd))
        if fd in self._available_fd:
            py_f = self._available_fd[fd]
            if hasattr(py_f, "close"):
                py_f.close()
                return ESUCCESS
            else:
                return EBADF
        else:
            return EACCES

    def _read_iovecs(self, iovs_address: int, iovs_len: int):
        iovs = []
        for nr in range(iovs_len):
            ciovec_address = iovs_address + nr * 8
            buf_addr = self._read_mem_u32(ciovec_address)
            buf_size = self._read_mem_u32(ciovec_address + 4)
            iovs.append((buf_addr, buf_size))
        return iovs

    def fd_read(
        self, fd: ir.i32, iovs: ir.i32, iovs_len: ir.i32, nread: ir.i32
    ) -> ir.i32:
        self._trace(
            "fd_read(fd={}, iovs={}, iovs_len={})".format(fd, iovs, iovs_len)
        )

        # Check fd:
        if fd == 0:
            py_f = fd
        elif fd in self._available_fd:
            py_f = self._available_fd[fd]
            if not hasattr(py_f, "read"):
                return EACCES
        else:
            return EBADF

        total_bytes = 0
        for buf_addr, buf_size in self._read_iovecs(iovs, iovs_len):
            if isinstance(py_f, int):
                data = os.read(py_f, buf_size)
            else:
                data = py_f.read(buf_size)

            assert len(data) <= buf_size
            self._write_mem_data(buf_addr, data)
            total_bytes += len(data)
        self._write_mem_u32(nread, total_bytes)
        return ESUCCESS

    def fd_seek(
        self, fd: ir.i32, offset: ir.i64, whence: ir.i32, new_pos_ptr: ir.i32
    ) -> ir.i32:
        self._trace(
            "fd_seek(fd={}, offset={}, whence={})".format(fd, offset, whence)
        )
        if fd in self._available_fd:
            py_f = self._available_fd[fd]
            if hasattr(py_f, "seek"):
                if whence not in [0, 1, 2]:
                    return EINVAL
                new_pos = py_f.seek(offset, whence)
                self._write_mem_u64(new_pos_ptr, new_pos)
                return ESUCCESS
            else:
                return EACCES
        else:
            return EBADF

    def fd_write(
        self, fd: ir.i32, iovs: ir.i32, iovs_len: ir.i32, n_written: ir.i32
    ) -> ir.i32:
        self._trace("fd_write(fd={}, iovs_len={})".format(fd, iovs_len))

        # Check fd:
        if fd == 1 or fd == 2:
            # Assume standard output / stderr:
            py_f = fd
        elif fd in self._available_fd:
            py_f = self._available_fd[fd]
            if not hasattr(py_f, "write"):
                return EACCES
        else:
            return EACCES

        total_bytes = 0

        # Loop over all iovs:
        for buf_addr, buf_size in self._read_iovecs(iovs, iovs_len):
            self.logger.debug(
                "Read %s bytes from address %s", buf_size, buf_addr
            )
            data = self._read_mem_data(buf_addr, buf_size)
            total_bytes += len(data)

            if isinstance(py_f, int):
                os.write(py_f, data)
            else:
                py_f.write(data)
            # print(data.decode("ascii", errors="ignore"), end="")
            # sys.stdout.write(data)

        self._write_mem_u32(n_written, total_bytes)
        return ESUCCESS

    def path_create_directory(
        self,
        fd: ir.i32,
        path_buf: ir.i32,
        path_len: ir.i32,
    ) -> ir.i32:
        """ Similar to mkdirat in POSIX """
        path = self._read_string(path_buf, path_len)

        self._trace("path_create_directory(fd={}, path={})".format(fd, path))

        # Check if we have a base folder:
        if fd not in self._available_fd:
            return EBADF

        # Base folder must be string
        base_folder = self._available_fd[fd]
        if not isinstance(base_folder, str):
            return EBADF

        # This is the full path:
        full_path = os.path.join(base_folder, path)

        if os.path.exists(full_path):
            return EEXIST

        os.mkdir(full_path)

        return ESUCCESS

    def path_filestat_get(
        self,
        fd: ir.i32,
        flags: ir.i32,
        path_buf: ir.i32,
        path_len: ir.i32,
        buf: ir.i32,
    ) -> ir.i32:
        """ Return attributes of file or directory. Similar to POSIX stat. """
        path = self._read_string(path_buf, path_len)
        self._trace(
            "path_filestat_get(fd={}, flags={}, path={}, buf={})".format(
                fd, flags, path, buf
            )
        )

        # Check if we have a base folder:
        if fd not in self._available_fd:
            return EBADF

        # Base folder must be string
        base_folder = self._available_fd[fd]
        if not isinstance(base_folder, str):
            return EBADF

        # This is the full path:
        full_path = os.path.join(base_folder, path)

        if not os.path.exists(full_path):
            return EEXIST

        # TODO: use flags
        stat_res = os.stat(full_path)

        device = stat_res.st_dev
        inode = stat_res.st_ino
        if stat.S_ISREG(stat_res.st_mode):
            filetype = 4  # regular_file
        elif stat.S_ISDIR(stat_res.st_mode):
            filetype = 3  # directory
        else:
            filetype = 0  # unknown
        nlink = stat_res.st_nlink
        size = stat_res.st_size
        atim = stat_res.st_atime_ns
        mtim = stat_res.st_mtime_ns
        ctim = stat_res.st_ctime_ns

        # Fill filestat struct:
        self._write_mem_u64(buf, device)  # device ID (u64)
        self._write_mem_u64(buf + 8, inode)  # file inode (u64)
        self._write_mem_u8(buf + 16, filetype)  # u8
        self._write_mem_u64(buf + 24, nlink)  # number of hard links (u64)
        self._write_mem_u64(buf + 32, size)  # File size (u64)
        self._write_mem_u64(buf + 40, atim)  # time in nano seconds
        self._write_mem_u64(buf + 48, mtim)
        self._write_mem_u64(buf + 56, ctim)
        return EACCES

    def path_open(
        self,
        fd: ir.i32,
        dirflags: ir.i32,
        path_buf: ir.i32,
        path_len: ir.i32,
        oflags: ir.i32,
        fs_rights_base: ir.i64,
        fs_rights_inheriting: ir.i64,
        fdflags: ir.i32,
        opened_fd_ptr: ir.i32,
    ) -> ir.i32:
        path = self._read_string(path_buf, path_len)
        self._trace(
            "path_open(fd={}, dirflags={}, path={}, oflags={}, fs_rights_base={}, fs_rights_inheriting={})".format(
                fd,
                dirflags,
                path,
                oflags,
                fs_rights_base,
                fs_rights_inheriting,
            )
        )
        # Check if we have a base folder:
        if fd not in self._available_fd:
            return EBADF

        # Base folder must be string
        base_folder = self._available_fd[fd]
        if not isinstance(base_folder, str):
            return EBADF

        # This is the full path:
        full_path = os.path.join(base_folder, path)
        # TODO: check rights_base and right inherting
        # TODO: handle all flags!.

        if oflags == 0:
            # Read only mode!
            if not os.path.exists(full_path):
                return EEXIST
            py_f = open(full_path, "rb")
        elif oflags == 13:
            # Write and create, fail when exists
            if os.path.exists(full_path):
                return EEXIST
            py_f = open(full_path, "wb")
        else:
            return EACCES

        new_fd = self._next_fd
        assert new_fd not in self._available_fd
        self._available_fd[new_fd] = py_f
        self._next_fd += 1

        self._write_mem_u32(opened_fd_ptr, new_fd)
        return ESUCCESS

    def path_symlink(
        self,
        old_path_buf: ir.i32,
        old_path_len: ir.i32,
        fd: ir.i32,
        new_path_buf: ir.i32,
        new_path_len: ir.i32,
    ) -> ir.i32:
        old_path = self._read_string(old_path_buf, old_path_len)
        new_path = self._read_string(new_path_buf, new_path_len)
        self.logger.error(
            "TODO: path_symlink(old_path={}, fd={}, new_path={})".format(
                old_path, fd, new_path
            )
        )
        return EACCES

    def path_unlink_file(
        self, fd: ir.i32, path_buf: ir.i32, path_len: ir.i32
    ) -> ir.i32:
        path = self._read_string(path_buf, path_len)
        self.logger.error(
            "TODO: path_unlink_file(fd={}, path={})".format(fd, path)
        )

        # Check if we have a base folder:
        if fd not in self._available_fd:
            return EBADF

        # Base folder must be string
        base_folder = self._available_fd[fd]
        if not isinstance(base_folder, str):
            return EBADF

        # This is the full path:
        full_path = os.path.join(base_folder, path)

        # TODO: actual removal!

        return EACCES

    def poll_oneoff(
        self,
        events_in: ir.i32,
        events_out: ir.i32,
        nsubscriptions: ir.i32,
        nevents_ptr: ir.i32,
    ) -> ir.i32:
        self.logger.error("TODO: poll_oneoff()")
        return EACCES

    def proc_exit(self, code: ir.i32) -> None:
        """Request program termination.

        Strategy: raise an exception which can be catched elsewhere.
        This ensures program termination.

        TODO: this does not work with native code, since the
        exception does not propagate through the native code.
        """
        self._trace("proc_exit(code={})".format(code))
        raise ProcExit(code)

    def random_get(self, buf: ir.i32, buf_len: ir.i32) -> ir.i32:
        """ Generate some random bytes into buf. """
        noise = os.urandom(buf_len)
        self._write_mem_data(buf, noise)
        return ESUCCESS
