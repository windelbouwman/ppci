"""

This adapter can check the fortrans suite: '1978 FORTRAN COMPILER VALIDATION SYSTEM' (fcvs21.tar.Z)

See:

http://www.itl.nist.gov/div897/ctg/fortran_form.htm

"""

import unittest
import glob
import os.path

from ppci.api import fortrancompile, get_arch


def create_test_function(cls, filename):
    """Create a test function for a single snippet"""
    _, snippet_filename = os.path.split(filename)
    test_function_name = "test_" + snippet_filename.replace(".", "_")

    def test_function(self):
        march = get_arch("arm")
        with open(filename) as f:
            fortrancompile([f.read()], march)
        # TODO: check output for correct values:

    if hasattr(cls, test_function_name):
        raise ValueError(f"Duplicate test {test_function_name}")

    setattr(cls, test_function_name, test_function)


def populate(cls):
    if "FCVS_DIR" in os.environ:
        directory = os.path.normpath(os.environ["FCVS_DIR"])
        for filename in sorted(glob.iglob(os.path.join(directory, "*.FOR"))):
            create_test_function(cls, filename)
    return cls


@populate
class FCVSTestCase(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
