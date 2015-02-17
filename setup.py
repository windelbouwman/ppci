from setuptools import setup, find_packages
import ppci

with open('readme.rst') as f:
    long_description = f.read()


setup(
    name='ppci',
    description="Pure python compiler infrastructure",
    scripts=[
        "bin/ppci-build.py",
        "bin/ppci-asm.py",
        "bin/st-flash.py", 'bin/hexutil.py'],
    long_description=long_description,
    version=ppci.version,
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data={'': ['*.grammar', "*.sled", "*.rst"]},
    url='https://bitbucket.org/windel/ppci',
    license='BSD',
    test_suite="test",
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Embedded Systems',
    ]
)
