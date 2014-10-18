from setuptools import setup, find_packages

with open('readme.rst') as f:
    long_description = f.read()

setup(
    name='ppci',
    description="Pure python compiler infrastructure",
    scripts=["bin/zcc.py", "bin/st-flash.py", 'bin/hexutil.py'],
    long_description=long_description,
    version='0.0.2',
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data={'': ['*.grammar', "*.brg", "*.sled", "*.rst"]},
    url='https://bitbucket.org/windel/ppci',
    license='BSD',
    test_suite="test",
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Embedded Systems',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
