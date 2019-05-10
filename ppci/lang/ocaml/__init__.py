from .cmo import read_file
from .gen_ir import ocaml_to_ir


__all__ = ["read_file", "ocaml_to_ir"]


if __name__ == "__main__":
    import sys

    read_file(sys.argv[0])
