
""" Helper script to help in compilation of the musl libc.

See for the musl library:
https://www.musl-libc.org/
"""

import os
import glob
import traceback
from ppci.api import cc
from ppci.lang.c import COptions
from ppci.common import CompilerError

home = os.environ['HOME']
musl_folder = os.path.join(home, 'GIT', 'musl')

def do_compile(filename):
    include_paths = [
        os.path.join(musl_folder, 'include'),
        os.path.join(musl_folder, 'src', 'internal'),
        os.path.join(musl_folder, 'obj', 'include'),
        os.path.join(musl_folder, 'arch', 'x86_64'),
        ]
    coptions = COptions()
    coptions.add_include_paths(include_paths)
    with open(filename, 'r') as f:
        obj = cc(f, 'x86_64', coptions=coptions)
    return obj


def main():
    print('Using musl folder:', musl_folder)
    crypt_md5_c = os.path.join(musl_folder, 'src', 'crypt', 'crypt_md5.c')
    failed = 0
    passed = 0
    for filename in glob.iglob(
            os.path.join(musl_folder, 'src', 'crypt', '*.c')):
        print('==> Compiling', filename)
        try:
            do_compile(filename)
        except CompilerError as ex:
            print('Error:', ex.msg, ex.loc)
            ex.print()
            traceback.print_exc()
            failed += 1
            break
        except Exception as ex:
            print('General exception:', ex)
            traceback.print_exc()
            failed += 1
            break
        else:
            print('Great success!')
            passed += 1

    print('Passed:', passed, 'failed:', failed)


if __name__ == '__main__':
    main()
