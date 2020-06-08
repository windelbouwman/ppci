
Release procedure
-----------------

This is more a note to self section on how to create a new release.

#. Determine the version numbers of this release and the next.
#. Switch to the release branch and merge the default branch into the
   release branch.

    .. code:: bash

        $ hg update release
        $ hg merge default
        $ hg commit

#. Check the version number in ppci/__init__.py
#. Make sure all tests pass and fix them if not.

    .. code:: bash

        $ tox

#. Tag this release with the intended version number and update to this tag.

    .. code:: bash

        $ hg tag x.y.z
        $ hg update x.y.z

#. Package and upload the python package. The following command creates a
   tar gz archive as well as a wheel package.

    .. code:: bash

        $ python setup.py sdist bdist_wheel upload

#. Switch back to the default branch and merge the release branch into the
   default branch.

    .. code:: bash

        $ hg update default
        $ hg merge release
        $ hg commit

#. Increase the version number in ppci/__init__.py.
#. Update docs/changelog.rst
