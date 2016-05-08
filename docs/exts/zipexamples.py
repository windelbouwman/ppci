# Custom extension that zips all the examples for download.
from zipfile import ZipFile
from os import path
import glob


def zip_examples(app):
    glob_patterns = [
        "examples/**/*.c3",
        "examples/**/*.asm",
        "examples/**/*.mmap",
        "examples/**/build.xml",
        "librt/*.c3"]
    my_path = path.dirname(path.abspath(__file__))
    root_path = path.abspath(path.join(my_path, '..', '..'))
    zip_filename = path.join(root_path, 'docs', 'examples.zip')
    with ZipFile(zip_filename, 'w') as myzip:
        for glob_pattern in glob_patterns:
            pat = path.join(path.join(root_path, glob_pattern))
            for filename in glob.iglob(pat, recursive=True):
                zfn = path.relpath(filename, root_path)
                app.info('zipping {} as {}'.format(filename, zfn))
                myzip.write(filename, zfn)


def setup(app):
    app.connect('builder-inited', zip_examples)
    return {'version': '0.1'}
