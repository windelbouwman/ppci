# Custom extension that zips all the examples for download.
from zipfile import ZipFile
import os
import glob


def zip_examples(app):
    glob_patterns = [
        "examples/blinky/*.c3",
        "examples/blinky/*.asm",
        "examples/blinky/*.mmap",
        "examples/blinky/build.xml",
        "examples/arduino/build.xml",
        "examples/arduino/*.c3",
        "examples/arduino/*.asm",
        "examples/arduino/*.mmap",
        "examples/linux64/*.mmap",
        "examples/linux64/*.asm",
        "examples/linux64/*.c3",
        "examples/linux64/hello/*.c3",
        "examples/linux64/hello/build.xml",
        "librt/*.c3"]
    my_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath(os.path.join(my_path, '..', '..'))
    zip_filename = os.path.join(root_path, 'docs', 'examples.zip')
    with ZipFile(zip_filename, 'w') as myzip:
        for glob_pattern in glob_patterns:
            for fn in glob.iglob(os.path.join(root_path, glob_pattern)):
                zfn = os.path.relpath(fn, root_path)
                app.info('zipping {} as {}'.format(fn, zfn))
                myzip.write(fn, zfn)


def setup(app):
    app.connect('builder-inited', zip_examples)
    return {'version': '0.1'}
