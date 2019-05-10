# Custom extension that zips all the examples for download.
import logging
from zipfile import ZipFile
import fnmatch
from os import path, walk


my_path = path.dirname(path.abspath(__file__))
root_path = path.abspath(path.join(my_path, '..', '..'))
zip_filename = path.join(root_path, 'docs', 'examples.zip')


def my_glob(folder, ext):
    """ glob does not work recursively in all python versions """
    for root, dirnames, filenames in walk(folder):
        for filename in fnmatch.filter(filenames, ext):
            yield path.join(root, filename)


def zip_examples(app):
    glob_patterns = [
        ("examples", "*.c3"),
        ("examples", "*.asm"),
        ("examples", "*.mmap"),
        ("examples", "build.xml"),
        ("librt", "*.c3")]
    with ZipFile(zip_filename, 'w') as myzip:
        for folder, ext in glob_patterns:
            pat = path.join(path.join(root_path, folder))
            for filename in my_glob(pat, ext):
                zfn = path.relpath(filename, root_path)
                logging.info('zipping {} as {}'.format(filename, zfn))
                myzip.write(filename, zfn)


def setup(app):
    app.connect('builder-inited', zip_examples)
    return {'version': '0.1'}
