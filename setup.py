from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys
import ppci


with open('readme.rst') as f:
    long_description = f.read()


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


setup(
    name='ppci',
    description="Pure python compiler infrastructure",
    scripts=[
        "bin/ppci-build.py",
        "bin/ppci-ld.py",
        "bin/ppci-asm.py",
        "bin/ppci-c3c.py",
        "bin/ppci-objdump.py",
        "bin/ppci-objcopy.py",
        'bin/ppci-hexutil.py'],
    long_description=long_description,
    version=ppci.version,
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data={'': ['*.grammar', "*.sled", "*.rst"]},
    url='https://ppci.readthedocs.org/',
    license='BSD',
    test_suite="test",
    tests_require=['tox'],
    cmdclass={'test': Tox},
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
        'Topic :: Software Development :: Embedded Systems',
    ]
)
