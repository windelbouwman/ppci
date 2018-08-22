""" Main entry point """

# from ppci.cli import main


import sys
import importlib

def main():
    subcommand = sys.argv[1]
    sys.argv[:] = sys.argv[1:]
    m = importlib.import_module('ppci.cli.' + subcommand)
    
    func = getattr(m, 'main', None) or getattr(m, subcommand)
    func()

if __name__ == '__main__':
    main()
