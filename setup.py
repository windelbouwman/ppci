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
    description="Pure python compiler infrastructure",
    scripts=[
        "bin/ppci-asm.py",
        "bin/ppci-build.py",
        "bin/ppci-c3c.py",
        "bin/ppci-cc.py",
        "bin/ppci-dbg.py",
        "bin/ppci-disasm.py",
        'bin/ppci-hexutil.py',
        "bin/ppci-ld.py",
        "bin/ppci-llc.py",
        "bin/ppci-objdump.py",
        "bin/ppci-objcopy.py"],
    long_description=long_description,
    version=ppci.__version__,
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data={'': ['*.grammar', "*.rst"]},
    url='https://ppci.readthedocs.io/',
    license='BSD',
    test_suite="setup.ppci_test_suite",
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Assemblers',
        'Topic :: Software Development :: Embedded Systems',
    ]
)
