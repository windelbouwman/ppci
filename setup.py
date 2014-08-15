from setuptools import setup, find_packages

setup(
    name='ppci',
    description="Pure python compiler infrastructure",
    scripts=["bin/zcc.py", "bin/st-flash.py", 'bin/hexutil.py'],
    version='0.0.1',
    author='Windel Bouwman',
    include_package_data=True,
    packages=find_packages(exclude=["*.test.*", "test"]),
    package_data = {'': ['*.grammar', "*.brg", "*.sled"]},
    url='https://bitbucket.org/windel/ppci',
    license='license.txt',
    test_suite="test"
)
