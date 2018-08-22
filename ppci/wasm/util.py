"""
Utils for working with WASM and binary data.
"""

import io
import logging
import os
import math
import re
import tempfile
import struct
import subprocess
import keyword
import shutil
from functools import lru_cache


__all__ = ['export_wasm_example',
           'run_wasm_in_node', 'run_wasm_in_notebook',
           'has_node']


PAGE_SIZE = 64 * 1024  # 64 KiB
hex_prog = re.compile(r'-?0x[0-9a-fA-F]+')
hex_float_prog = re.compile(r'[-+]?0x[0-9a-fA-F]+')
hex_nan_prog = re.compile(r'[-+]?nan:.+')


def is_int(s):
    """ Check if the given s is integer or can be converted to int """
    if isinstance(s, int):
        return True
    elif isinstance(s, str):
        return hex_prog.match(s)
    else:
        return False


def make_int(s, bits=None):
    """ Try to make an integer """
    if isinstance(s, int):
        v = s
    elif isinstance(s, float):
        v = int(s)
    elif isinstance(s, str):
        if hex_prog.match(s):
            v = int(s, 16)
        else:
            v = int(s)
    else:
        raise NotImplementedError(str(s))

    if bits is not None:
        # Wrap sign if needed:
        if v >= (1 << (bits - 1)):
            v -= (1 << bits)

    return v


def make_float(s):
    """ Try to make an integer """
    if isinstance(s, float):
        return s
    elif isinstance(s, int):
        return float(s)
    elif isinstance(s, str):
        if hex_nan_prog.match(s):
            return math.nan
        elif hex_float_prog.match(s):
            return float.fromhex(s.replace('_', ''))
        else:
            return float(s)
    else:
        raise NotImplementedError(str(s))


def sanitize_name(name):
    """ Strip illegal characters from name, such as '.' and '-' """
    # TODO: we need to escape many things..
    name = name.replace('.', '_').replace('-', '_').replace('/', '_')

    # To allow access by python attribute, check if the name is a
    # python keyword:
    if keyword.iskeyword(name):
        name = name + '_'

    # No identifiers starting with a digit:
    if name and name[0].isdigit():
        name = '_' + name

    return name


def inspect_bytes_at(bb, offset):
    """ Inspect bytes at the specified offset.
    """
    start = max(0, offset - 16)
    end = offset + 16
    bytes2show = bb[start:end]
    bytes2skip = bb[start:offset]
    text_offset = len(repr(bytes2skip))
    print(bytes2show)
    print('|'.rjust(text_offset))


def datastring2bytes(s):
    # return eval('b"' + s + '"')  # can we do this without evil?
    f = io.BytesIO()
    i = 0
    while i < len(s):
        if s[i] == '\\':
            try:
                v = int(s[i+1:i+3], 16)
                delta = 3
            except ValueError:
                # Escape ... we cant do Unicode yet
                v = {'t': 9, 'n': 10, 'r': 13, '"': 34, '\'': 39, '\\': 92}[s[i+1]]
                delta = 2
            f.write(struct.pack('<B', v))
            i += delta
        else:
            f.write(s[i].encode())
            i += 1
    return f.getvalue()


def bytes2datastring(b):
    f = io.StringIO()
    for v in b:
        if 48 >= v >= 122 and v not in (92, 96):
            f.write(chr(v))
        else:
            f.write('\\' + hex(v)[2:].rjust(2, '0'))
    return f.getvalue()


def export_wasm_example(filename, code, wasm, main_js=''):
    """ Generate an html file for the given code and wasm module.
    """
    from .components import Module

    if filename.startswith('~/'):
        filename = os.path.expanduser(filename)

    if isinstance(wasm, Module):
        wasm = wasm.to_bytes()
    elif isinstance(wasm, bytes):
        if not wasm.startswith(b'\x00asm'):
            raise ValueError(
                'given bytes do not look like a wasm module.')
    else:
        raise TypeError('expects a wasm module or bytes.')

    wasm_text = str(list(wasm))  # [0, 1, 12, ...]

    fname = os.path.basename(filename).rsplit('.', 1)[0]

    # Read templates
    src_filename_js = os.path.join(os.path.dirname(__file__), 'template.js')
    src_filename_html = os.path.join(
        os.path.dirname(__file__), 'template.html')
    with open(src_filename_js, 'rb') as f:
        js = f.read().decode()
    with open(src_filename_html, 'rb') as f:
        html = f.read().decode()

    # Produce HTML
    js = js.replace(
        'WASM_PLACEHOLDER',
        'var wasm_data = new Uint8Array(' + wasm_text + ');')
    js = js.replace('MAIN_JS_PLACEHOLDER', main_js)
    html = html.replace('<title></title>', '<title>%s</title>' % fname)
    html = html.replace('CODE_PLACEHOLDER', code)
    html = html.replace('JS_PLACEHOLDER', js)

    # Export HTML file
    with open(filename, 'wb') as f:
        f.write(html.encode())
    logging.info('Wrote example HTML to %s', filename)


_nb_output = 0


def run_wasm_in_notebook(wasm):
    """ Load a WASM module in the Jupyter notebook.
    """
    from .components import Module
    from IPython.display import display, HTML, Javascript

    if isinstance(wasm, Module):
        wasm = wasm.to_bytes()
    elif isinstance(wasm, bytes):
        if not wasm.startswith(b'\x00asm'):
            raise ValueError('given bytes do not look like a wasm module.')
    else:
        raise TypeError('expects a wasm module or bytes.')

    wasm_text = str(list(wasm))  # [0, 1, 12, ...]

    # Read templates
    src_filename_js = os.path.join(os.path.dirname(__file__), 'template.js')
    with open(src_filename_js, 'rb') as f:
        js = f.read().decode()

    # Get id
    global _nb_output
    _nb_output += 1
    id = 'wasm_output_%u' % _nb_output

    # Produce JS
    js = js.replace('wasm_output', id)
    js = js.replace('MAIN_JS_PLACEHOLDER', '')
    js = js.replace(
        'WASM_PLACEHOLDER',
        'var wasm_data = new Uint8Array(' + wasm_text + ');')
    js = '(function() {\n%s;\ncompile_my_wasm();\n})();' % js

    # Output in current cell
    display(HTML("<div style='border: 2px solid blue;' id='%s'></div>" % id))
    display(Javascript(js))


@lru_cache(maxsize=None)
def has_node() -> bool:
    """ Check if nodejs is available """
    return 'WASMFUN_NODE_EXE' in os.environ

    # TODO: enable the code below.
    # On appveyor this failed:
    # https://ci.appveyor.com/project/WindelBouwman/ppci-786/build/1.0.537
    if hasattr(shutil, 'which'):
        return bool(shutil.which('node'))
    else:
        return False


def run_wasm_in_node(wasm, silent=False):
    """ Load a WASM module in node.
    Just make sure that your module has a main function.
    """
    from .components import Module

    if isinstance(wasm, Module):
        wasm = wasm.to_bytes()
    elif isinstance(wasm, bytes):
        if not wasm.startswith(b'\x00asm'):
            raise ValueError('given bytes do not look like a wasm module.')
    else:
        raise TypeError('expects a wasm module or bytes.')

    wasm_text = str(list(wasm))  # [0, 1, 12, ...]

    # Read templates
    src_filename_js = os.path.join(os.path.dirname(__file__), 'template.js')
    with open(src_filename_js, 'rb') as f:
        js = f.read().decode()

    # Produce JS
    js = js.replace('MAIN_JS_PLACEHOLDER', '')
    js = js.replace(
        'WASM_PLACEHOLDER',
        'var wasm_data = new Uint8Array(' + wasm_text + ');')
    js += '\nprint_ln("Hello from Nodejs!");\ncompile_my_wasm();\n'

    # Write temporary file
    filename = os.path.join(
        tempfile.gettempdir(), 'pyscript_%i.js' % os.getpid())
    with open(filename, 'wb') as f:
        f.write(js.encode())

    # Execute JS in nodejs
    try:
        res = subprocess.check_output(
            [get_node_exe(), '--use_strict', filename])
    except Exception as err:
        if hasattr(err, 'output'):
            err = err.output.decode()
        else:
            err = str(err)
        err = err[:200] + '...' if len(err) > 200 else err
        raise Exception(err)
    finally:
        try:
            os.remove(filename)
        except Exception:
            pass

    # Process output
    output = res.decode()
    result = output.split('Result:', 1)[-1].strip()
    if not silent:
        print(output.rstrip())
    return result


NODE_EXE = None


def get_node_exe():
    """ Small utility that provides the node exe. The first time this
    is called both 'nodejs' and 'node' are tried. To override the
    executable path, set the ``FLEXX_NODE_EXE`` environment variable.
    """
    # This makes things work on Ubuntu's nodejs as well as other node
    # implementations, and allows users to set the node exe if necessary
    global NODE_EXE
    NODE_EXE = os.getenv('WASMFUN_NODE_EXE') or NODE_EXE
    if NODE_EXE is None:
        NODE_EXE = 'nodejs'
        try:
            subprocess.check_output([NODE_EXE, '-v'])
        except Exception:  # pragma: no cover
            NODE_EXE = 'node'
    return NODE_EXE
