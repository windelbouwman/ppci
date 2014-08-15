from setuptools import setup, find_packages

setup(
    name='ppci',
    description="Pure python compiler infrastructure",
    version='0.0.1',
    author='Windel Bouwman',
    packages=find_packages(exclude=["*.test.*", "test"]),
    include_package_data=True,
    url='https://bitbucket.org/windel/ppci',
    license='license.txt',
    test_suite="test"
)
