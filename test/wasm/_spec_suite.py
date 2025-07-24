"""
This module manages (downloads when needed) the test suite from the official
WebAssembly spec: https://github.com/WebAssembly/spec/tree/master/test
The suite is versioned using the Git commit.

Test scripts can use get_spec_suite_dir() and get_test_script_parts().
Run this script explicitly to (re)download the suite.
"""

import io
import os
import shutil
import zipfile
from urllib.request import urlopen


# The commit of the WASM spec repo to use
COMMIT = "626e231e2f01e2"


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
SPEC_TEST_SUITE_DIR = os.path.join(THIS_DIR, "spec_suite_" + COMMIT)


def download():
    print("Downloading WASM spec test suite @ " + COMMIT)
    # Prepare directory
    if os.path.isdir(SPEC_TEST_SUITE_DIR):
        shutil.rmtree(SPEC_TEST_SUITE_DIR)
    os.mkdir(SPEC_TEST_SUITE_DIR)
    # Download
    url = "https://github.com/WebAssembly/spec/archive/{}.zip".format(COMMIT)
    zipped = urlopen(url, timeout=5).read()
    # Extract
    with zipfile.ZipFile(io.BytesIO(zipped)) as zf:
        for name in [name for name in zf.namelist() if "/test/core/" in name]:
            shortname = name.split("/test/core/")[-1]
            if not shortname:
                continue
            with open(os.path.join(SPEC_TEST_SUITE_DIR, shortname), "wb") as f:
                f.write(zf.read(name))


def get_spec_suite_dir():
    """Get the directory that contains the files for the official WASM
    spec test-suite. The suite will be downloaded as needed.
    """
    if not os.path.isdir(SPEC_TEST_SUITE_DIR):
        download()
    return SPEC_TEST_SUITE_DIR


def get_test_script_parts(fname):
    """Get the toplevel expressions in fname as strings."""
    text1 = (
        open(os.path.join(get_spec_suite_dir(), fname), "rb").read().decode()
    )
    text2 = _normalize_sexpr(text1)

    pieces = text2.split("\n(")
    return ["(" + piece for piece in pieces[1:]]


def _normalize_sexpr(text):
    """Normalize s-expr by making sure each toplevel expr is on a new line,
    and sub-expressions are always indented. Starts of block comments are
    also alwats indented. As a result, the text can now be split on "\n(" to
    get all expressions.
    """

    # You probably dont want to touch it if it aint broken

    text = "\n" + text.replace("\r\n", "\n")  # Defend against Windows
    parts = []
    in_line_comment = False
    in_block_comment = False
    in_string = False
    level = 0
    i0 = i = 0

    while i < len(text) - 2:
        i += 1
        c = text[i]

        if in_line_comment:
            if c in "\r\n":
                in_line_comment = False
        elif in_block_comment:
            if c == "(" and text[i + 1] == ";":
                in_block_comment += 1
                if text[i - 1] in "\r\n":
                    parts.append(text[i0:i] + "  ")  # indent block comment
                    i0 = i
                i += 1
            elif c == ";" and text[i + 1] == ")":
                in_block_comment -= 1
                i += 1
        elif in_string:
            if c == '"' and text[i - 1] != "\\":
                in_string = False
        else:
            if c == '"':
                in_string = True
            if c == ";" and text[i + 1] == ";":
                in_line_comment = True
            elif c == "(" and text[i + 1] == ";":
                in_block_comment = 1
                if text[i - 1] in "\r\n":
                    parts.append(text[i0:i] + "  ")  # indent block comment
                    i0 = i
                i += 1  # skip one char!
            elif c == "(":
                level += 1
                if level == 1 and text[i - 1] not in "\r\n":
                    parts.append(text[i0:i] + "\n")  # dedent toplevel expr
                    i0 = i
                elif level > 1 and text[i - 1] in "\r\n":
                    parts.append(text[i0:i] + "  ")  # indent sub-expr
                    i0 = i
            elif c == ")":
                level -= 1

    parts.append(text[i0:])
    return "".join(parts)


if __name__ == "__main__":
    download()
