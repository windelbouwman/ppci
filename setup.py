from setuptools import setup, find_packages
import ppci


with open('readme.rst') as f:
    long_description = f.read()


setup(
    name='ppci',
    description="A compiler for ARM, X86, MSP430, xtensa and more implemented in pure Python",
    long_description=long_description,
    version=ppci.__version__,
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data={'': ['*.grammar', "*.rst", 'template.js', 'template.html']},
    entry_points={
        'console_scripts': [
            'ppci-archive = ppci.cli.archive:archive',
            'ppci-asm = ppci.cli.asm:asm',
            'ppci-build = ppci.cli.build:build',
            'ppci-c3c = ppci.cli.c3c:c3c',
            'ppci-cc = ppci.cli.cc:cc',
            'ppci-dbg = ppci.cli.dbg:dbg',
            'ppci-disasm = ppci.cli.disasm:disasm',
            'ppci-hexdump = ppci.cli.hexdump:hexdump',
            'ppci-hexutil = ppci.cli.hexutil:hexutil',
            'ppci-java = ppci.cli.java:java',
            'ppci-ld = ppci.cli.link:link',
            'ppci-llc = ppci.cli.llc:llc',
            'ppci-mkuimage = ppci.cli.mkuimage:mkuimage',
            'ppci-objcopy = ppci.cli.objcopy:objcopy',
            'ppci-objdump = ppci.cli.objdump:objdump',
            'ppci-ocaml = ppci.cli.ocaml:ocaml',
            'ppci-opt = ppci.cli.opt:opt',
            'ppci-pascal = ppci.cli.pascal:pascal',
            'ppci-pedump = ppci.cli.pedump:pedump',
            'ppci-pycompile = ppci.cli.pycompile:pycompile',
            'ppci-readelf = ppci.cli.readelf:readelf',
            'ppci-wasm2wat = ppci.cli.wasm2wat:wasm2wat',
            'ppci-wasmcompile = ppci.cli.wasmcompile:wasmcompile',
            'ppci-wat2wasm = ppci.cli.wat2wasm:wat2wasm',
            'ppci-wabt = ppci.cli.wabt:wabt',
            'ppci-yacc = ppci.cli.yacc:yacc',
        ]
    },
    url='https://ppci.readthedocs.io/',
    license='BSD',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Assembly',
        'Programming Language :: C',
        'Programming Language :: Java',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Assemblers',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Pre-processors',
    ]
)
