""" Wrapper for the WebAssembly Binary Toolkit - https://github.com/WebAssembly/wabt/

The wabt is more or less the reference implementation of WebAssembly,
so its a great tool to have a solid reference implementation for a few tasks.
It's converted to (ASM) js, so we can run it cross-platform using node.
"""

import os
import sys
import subprocess
from urllib.request import urlopen

from ppci.wasm.util import get_node_exe


THIS_DIR = os.path.dirname(__file__)


js_wat2wasm = """
var wabt = require('./libwabt.js');
if (wabt.call) { wabt = wabt(); }
process.stdin.setEncoding('utf8');

/* Collect text */
var pieces = [];
process.stdin.on('data', function (chunk) {
  pieces.push(chunk);
});

/* Convert and write bytes */
process.stdin.on('end', function () {
    var text = pieces.join('');
    var module = wabt.parseWat('in.wat', text);
    module.resolveNames();
    module.validate();
    var binary = module.toBinary({log: false, write_debug_names:false});
    process.stdout.write(new Buffer(binary.buffer));
});
""".strip()


js_wasm2wat = """
var wabt = require('./libwabt.js');
if (wabt.call) { wabt = wabt(); }
process.stdout.setEncoding('utf8');

/* Collect bytes */
var pieces = [];
process.stdin.on('data', function (chunk) {
  pieces.push(chunk);
});

/* Convert and write text */
process.stdin.on('end', function () {
    var binary = new Uint8Array(Buffer.concat(pieces));
    var module = wabt.readWasm(binary, {readDebugNames: READ_DEBUG_NAMES});
    if (GENERATE_NAMES) { module.generateNames(); module.applyNames(); }
    var text = module.toText({foldExprs: false, inlineExport: false});
    process.stdout.write(text);
});
""".strip()


def wat2wasm(wat):
    """ Convert textual WebAssembly (.wat), given as str, to bytes (.wasm),
    using the WebAssembly Binary Toolkit (WABT).
    """
    if not isinstance(wat, str):
        raise TypeError('wat2wasm() expects a str or tuple.')
    
    # Prepare
    libfile = _get_wabt_lib()
    libdir = os.path.dirname(libfile)
    node = get_node_exe()
    
    # Compose JS
    js = js_wat2wasm.replace('libwabt.js', os.path.basename(libfile))
    
    # Run
    p = subprocess.Popen([node, '-e', js], cwd=libdir,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    blob = wat.encode()  # ?? (sys.getfilesystemencoding())
    out, err = p.communicate(blob)
    if err:
        raise RuntimeError(err.decode())
    else:
        return out


def wasm2wat(wasm, resolve_names=False):
    """ Convert binary WebAssembly (.wasm), given as bytes, to text (.wat),
    using the WebAssembly Binary Toolkit (WABT).
    """
    if not isinstance(wasm, bytes):
        raise TypeError('wasm2wat() expects bytes.')
    
    # Prepare
    libfile = _get_wabt_lib()
    libdir = os.path.dirname(libfile)
    node = get_node_exe()
    
    # Compose JS
    js = js_wasm2wat.replace('libwabt.js', os.path.basename(libfile))
    if resolve_names:
        js = js.replace('READ_DEBUG_NAMES', 'true').replace('GENERATE_NAMES', 'true')
    else:
        js = js.replace('READ_DEBUG_NAMES', 'false').replace('GENERATE_NAMES', 'false')
    
    # Run
    p = subprocess.Popen([node, '-e', js], cwd=libdir,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(wasm)
    if err:
        raise RuntimeError(err.decode())
    else:
        return out.decode()


def _get_wabt_lib():
    """ Get the filename of the wabt js lib.
    """
    # Update the commit tag to make use of a newer version. We tag to a specific commit
    # to avoid unexpected regressions as the wabt API changes.
    commit = '409d61ef'
    filename = os.path.join(THIS_DIR, 'libwabt_{}.js'.format(commit))
    if not os.path.isfile(filename):
        print('Downloading libwabt.js ...')
        url = 'https://raw.githubusercontent.com/WebAssembly/wabt/{}/demo/libwabt.js'.format(commit)
        with urlopen(url, timeout=5) as f:
            bb = f.read()
        with open(filename, 'wb') as f:
            f.write(bb)
    return filename


if __name__ == '__main__':
    
    x = wat2wasm('(module)')
    print(x)
    y = wasm2wat(x)
    print(y)
