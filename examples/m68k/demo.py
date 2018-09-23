
import io
from ppci.api import cc


source = """
int add(int x, int y) {
  return x + y;
}

"""

obj = cc(io.StringIO(source), 'm68k')
print(obj)

print("""
Please now open the online disassembler:

https://onlinedisassembler.com/odaweb/

Select m68k:68000

and paste:
{}

""".format(obj.get_section('code').data.hex()))

