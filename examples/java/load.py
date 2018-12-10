
""" Show how to dynamically load java code.
"""

import logging
from ppci.arch.jvm import load_class


logging.basicConfig(level=logging.DEBUG)
x = load_class('Test14.class')
print(x.my_add(1, 5), ' <== must be 7')

