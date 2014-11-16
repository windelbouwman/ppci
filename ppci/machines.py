
import io
from .buildfunctions import assemble, c3compile, link, objcopy, bfcompile


def wrap_arm(objs, filename):
    """ Wrap objects into startercode for reavb-pb """
    march = "arm"
    startercode = """
    section reset
    mov sp, 0x30000   ; setup stack pointer
    BL sample_start     ; Branch to sample start
    local_loop:
    B local_loop
    """

    arch_mmap = """
    MEMORY image LOCATION=0x10000 SIZE=0x10000 {
        SECTION(reset)
        SECTION(code)
    }

    MEMORY ram LOCATION=0x20000 SIZE=0x10000 {
        SECTION(data)
    }
    """
    # Construct binary file from snippet:
    o1 = assemble(io.StringIO(startercode), march)
    o2 = link([o1] + objs, io.StringIO(arch_mmap), march)

    objcopy(o2, 'image', 'bin', filename)


def wrap(objs, machine, filename):
    if machine == "arm":
        return wrap_arm(objs, filename)
    raise NotImplementedError('machine {} not implemented'.format(machine))

