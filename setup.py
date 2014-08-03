from setuptools import setup, find_packages

setup(
    name='ppci',
    version='0.0.1',
    author='Windel Bouwman',
    packages=find_packages(exclude=["*.test.*", "test"]),
    url='https://bitbucket.org/windel/ppci',
    license='LICENSE.txt',
    test_suite="test"
)


