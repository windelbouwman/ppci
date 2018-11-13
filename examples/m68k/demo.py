
import io
from ppci.api import cc, link, asm
from ppci.format.srecord import write_srecord
from ppci.format.hunk import write_hunk


source = """
int add(int x, int y) {
  return x + y;
}

"""

obj = cc(io.StringIO(source), 'm68k')
obj = link([obj])
print(obj)

print("""
Please now open the online disassembler:

https://onlinedisassembler.com/odaweb/

Select m68k:68000

and paste:
{}

""".format(obj.get_section('code').data.hex()))

# TODO:
with open('demo.srec', 'w') as f:
    write_srecord(obj, f)


obj = asm('amiga_hello_world.asm', 'm68k')
obj = link([obj])
print(obj)

print(obj.get_section('code').data.hex())

write_hunk('demo', obj.get_section('code').data)

