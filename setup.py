from setuptools import setup, find_packages

with open('readme.rst') as f:
    long_description = f.read()

setup(
    name='ppci',
    description="Pure python compiler infrastructure",
    scripts=["bin/zcc.py", "bin/st-flash.py", 'bin/hexutil.py'],
    long_description=long_description,
    version='0.0.1',
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data = {'': ['*.grammar', "*.brg", "*.sled", "*.rst"]},
    url='https://bitbucket.org/windel/ppci',
    license='license.txt',
    test_suite="test"
)
