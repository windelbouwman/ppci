#!/bin/bash

set -e

# This is the script run on the drone.io CI service.

pip install tox codecov wheel --use-mirrors

# Run tox:
tox --version
tox -e py33,cover
codecov

# Run setup script:
python setup.py sdist bdist_wheel
