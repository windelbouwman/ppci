
"""
Handy online wasm to text conversion:

https://cdn.rawgit.com/WebAssembly/wabt/7e56ca56/demo/wasm2wast/

https://cdn.rawgit.com/WebAssembly/wabt/fb986fbd/demo/wat2wasm/

https://github.com/WebAssembly/wabt

"""

import argparse
import io
import os
import html
import traceback
import glob
import logging
import time
from ppci.lang.c import COptions
from ppci.api import c_to_ir, get_arch, optimize, c3_to_ir
from ppci.wasm import ir_to_wasm
from ppci.irutils import ir_link

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', '-v', action='count', default=0)
args = parser.parse_args()

if args.verbose:
    loglevel = logging.DEBUG
else:
    loglevel = logging.INFO

logging.basicConfig(level=loglevel)

this_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(this_dir, '..')
wasm_filename = os.path.join(this_dir, 'samples_in_wasm.wasm')
arch = get_arch('arm')
coptions = COptions()
libc_dir = os.path.join(this_dir, '..', 'librt', 'libc')
libc_include_path = os.path.join(libc_dir, 'include')
coptions.add_include_path(libc_include_path)

libc_filename = os.path.join(
    this_dir, '..', 'librt', 'libc', 'lib.c')
libio_filename = os.path.join(
    this_dir, '..', 'librt', 'io.c3')


def c_to_wasm(filename, verbose=False):
    # Compile c source:
    with open(libc_filename, 'r') as f:
        ir_libc = c_to_ir(f, arch, coptions=coptions)

    print(ir_libc, ir_libc.stats())
    optimize(ir_libc, level='2')

    with open(filename, 'r') as f:
        x = c_to_ir(f, arch, coptions=coptions)

    print(x, x.stats())
    optimize(x, level='2')
    print(x, x.stats())

    if verbose:
        x.display()

    wasm_module = ir_to_wasm(ir_link([ir_libc, x]))

    print('Completed generating wasm module', wasm_module)
    if verbose:
        wasm_module.show()
        print(wasm_module.to_bytes())
    # with open(wasm_filename, 'wb') as f:
    #    wasm_module.to_file(f)
    return wasm_module


def c3_to_wasm(filename, verbose=False):
    """ Take c3 to wasm """
    bsp = io.StringIO("""
       module bsp;
       public function void putc(byte c);
       """)
    ir_module = c3_to_ir([bsp, libio_filename, filename], [], arch)

    # ir_modules.insert(0, ir_modules.pop(-1))  # Shuffle bsp forwards
    if verbose:
        print(str(ir_module))
    # optimize(x, level='2')
    # print(x, x.stats())

    # x.display()

    wasm_module = ir_to_wasm(ir_module)

    print('Completed generating wasm module', wasm_module)
    if verbose:
        wasm_module.show()
        print(wasm_module.to_bytes())
    # with open(wasm_filename, 'wb') as f:
    #    wasm_module.to_file(f)
    return wasm_module


samples = list(glob.iglob(os.path.join(
    this_dir, '..', 'test', 'samples', 'simple', '*.c'))) + \
    list(glob.iglob(os.path.join(
        this_dir, '..', 'test', 'samples', 'simple', '*.c3')))

html_filename = os.path.join(this_dir, 'samples_in_wasm.html')
with open(html_filename, 'w') as f:
    print("""<!DOCTYPE html>
    <html>
    <head><title>Samples</title><meta charset="utf-8"></head>
    <body>
    """, file=f)
    print('<p>Sample generated on {}</p>'.format(time.ctime()), file=f)
    print('<p>Generator script: <pre>{}</pre></p>'.format(__file__), file=f)

    fns = []
    for nr, sample in enumerate(samples, 1):
        print('<h1>Example #{}: {}</h1>'.format(nr, sample), file=f)

        # Sourcecode:
        print('<h2>Code</h2>', file=f)
        with open(sample, 'r') as f2:
            txt = f2.read()
        print('<pre>', file=f)
        print(html.escape(txt), file=f)
        print('</pre>', file=f)

        # Expected output:
        print('<h2>Expected output</h2>', file=f)
        expected_output = os.path.splitext(sample)[0] + '.out'
        with open(expected_output, 'r') as f2:
            txt = f2.read()
        print('<pre>', file=f)
        print(html.escape(txt), file=f)
        print('</pre>', file=f)

        # Actual wasm code:
        try:
            if sample.endswith('.c3'):
                wasm_module = c3_to_wasm(sample, verbose=args.verbose)
            else:
                wasm_module = c_to_wasm(sample, verbose=args.verbose)
        except:
            print('Massive error!', file=f)
            print('<pre>', file=f)
            traceback.print_exc(file=f)
            print('</pre>', file=f)
            continue

        print('<h2>Actual output</h2>', file=f)
        print('<pre id="wasm_output{}">'.format(nr), file=f)
        print('</pre>', file=f)

        with open('example_{}.wasm'.format(nr), 'wb') as f3:
            wasm_module.to_file(f3)

        wasm_text = str(list(wasm_module.to_bytes()))
        print("""<script>
        function print_charcode{0}(i) {{
          var c = String.fromCharCode(i);
          var el = document.getElementById('wasm_output{0}');
          el.innerHTML += c;
        }}

        var providedfuncs{0} = {{
          bsp_putc: print_charcode{0},
        }};

        function compile_wasm{0}() {{
          var wasm_data = new Uint8Array({1});
          var module = new WebAssembly.Module(wasm_data);
          var inst = new WebAssembly.Instance(module, {{js: providedfuncs{0}}});
          inst.exports.main_main();
          console.log('calling' + {0});
        }}
        </script>""".format(nr, wasm_text), file=f)
        fns.append('compile_wasm{}'.format(nr))

    print("""
    <script>
    function run_samples() {""", file=f)
    for fn in fns:
        print('{}();'.format(fn), file=f)
    print("""}
    window.onload = run_samples;
    </script>
    </body>
    </html>
    """, file=f)

