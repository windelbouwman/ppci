
""" Show how to dynamically load java code.
"""

import logging
import os.path
from ppci.arch.jvm import load_class


logging.basicConfig(level=logging.DEBUG)

# Load java compiled file:
filename = 'Test14.class'
if os.path.exists(filename):
    x = load_class(filename)
    print('my_add(1, 5) =', x.my_add(1, 5), ' <== must be 7')
else:
    print('Compile first with: javac Test14.class')

# Load kotlin compiled file:
filename = 'add/AddKt.class'
if os.path.exists(filename):
    x = load_class(filename)
    print('my_add(1, 5) =', x.my_add(1, 5), ' <== must be 7')
    print('my_func(3) =', x.my_func(3), ' <== must be 31.4')
else:
    print('Compile first with: kotlinc add.kt')
