""" Main entry point """

# from ppci.cli import main


import sys
import importlib


valid_programs = [
    "archive",
    "asm",
    "build",
    "c3c",
    "cc",
    "disasm",
    "hexdump",
    "hexutil",
    "java",
    "link",
    "llc",
    "mkuimage",
    "objcopy",
    "objdump",
    "ocaml",
    "opt",
    "pascal",
    "pedump",
    "pycompile",
    "readelf",
    "wabt",
    "wasm2wat",
    "wasmcompile",
    "wat2wasm",
    "yacc",
]


def main():
    if len(sys.argv) < 2:
        print_help_message()
    else:
        subcommand = sys.argv[1]
        cmd_args = sys.argv[2:]
        if subcommand in valid_programs:
            m = importlib.import_module("ppci.cli." + subcommand)
            func = getattr(m, "main", None) or getattr(m, subcommand)
            func(cmd_args)
        else:
            print_help_message()


def print_help_message():
    print("Welcome to PPCI command line!")
    print()
    print("Please use one of the subcommands below:")
    for cmd in valid_programs:
        print("  $ python -m ppci {} -h".format(cmd))
    print()


if __name__ == "__main__":
    main()
