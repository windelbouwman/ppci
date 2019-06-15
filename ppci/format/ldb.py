from ..binutils.debuginfo import DebugAddress


def write_ldb(obj, output_file):
    """ Export debug info from object to ldb format.

    See for example:
    - https://github.com/embedded-systems/qr/blob/master/in4073_xufo/
      x32-debug/ex2.dbg
    """

    def fx(address):
        assert isinstance(address, DebugAddress)
        return obj.get_symbol_id_value(address.symbol_id)

    debug_info = obj.debug_info
    for debug_location in debug_info.locations:
        filename = debug_location.loc.filename
        row = debug_location.loc.row
        address = fx(debug_location.address)
        print(
            'line: "{}":{} @ 0x{:08X}'.format(filename, row, address),
            file=output_file,
        )

    for func in debug_info.functions:
        name = func.name
        address = fx(func.begin)
        print(
            "function: {} <0> @ 0x{:08X}".format(name, address),
            file=output_file,
        )

    for var in debug_info.variables:
        name = var.name
        address = fx(var.address)
        print(
            "global: {} <0> @ 0x{:08X}".format(name, address), file=output_file
        )
