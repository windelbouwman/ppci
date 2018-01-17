import unittest
from setuptools import setup, find_packages
import ppci


with open('readme.rst') as f:
    long_description = f.read()


def ppci_test_suite():
    """ Load the ppci test suite """
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('test', pattern='test*.py')
    return test_suite


setup(
    name='ppci',
    description="A compiler for ARM, X86, MSP430, xtensa and more implemented in pure Python",
    long_description=long_description,
    version=ppci.__version__,
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data={'': ['*.grammar', "*.rst"]},
    entry_points={
        'console_scripts': [
            'ppci-asm = ppci.cli.asm:asm',
            'ppci-build = ppci.cli.build:build',
            'ppci-c3c = ppci.cli.c3c:c3c',
            'ppci-cc = ppci.cli.cc:cc',
            'ppci-dbg = ppci.cli.dbg:dbg',
            'ppci-disasm = ppci.cli.disasm:disasm',
            'ppci-hexutil = ppci.cli.hexutil:hexutil',
            'ppci-ld = ppci.cli.link:link',
            'ppci-llc = ppci.cli.llc:llc',
            'ppci-mkuimage = ppci.cli.mkuimage:mkuimage',
            'ppci-objcopy = ppci.cli.objcopy:objcopy',
            'ppci-objdump = ppci.cli.objdump:objdump',
            'ppci-opt = ppci.cli.opt:opt',
            'ppci-pascal = ppci.cli.pascal:pascal',
            'ppci-pedump = ppci.cli.pedump:pedump',
            'ppci-pycompile = ppci.cli.pycompile:pycompile',
            'ppci-wasm2wat = ppci.cli.wasm2wat:wasm2wat',
            'ppci-wasmcompile = ppci.cli.wasmcompile:wasmcompile',
            'ppci-yacc = ppci.cli.yacc:yacc',
        ]
    },
    url='https://ppci.readthedocs.io/',
    license='BSD',
    test_suite="setup.ppci_test_suite",
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Assemblers',
        'Topic :: Software Development :: Embedded Systems',
    ]
)
