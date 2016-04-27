# Advanced JTAG Bridge

This is a port of the advanced JTAG bridge from the [MinSoC
project](http://opencores.org/project,minsoc) to RISC-V. The port has been done
as part of the [PULP project](http://pulp.ethz.ch).

The bridge connects to a JTAG target and opens a local port for a remote gdb
connection. Supported targets include [RTL simulations via JTAG
DPI](https://github.com/ethz-iis/jtag_dpi), FPGA emulation and FTDI cables.

## Build

Run the following commands to the build the JTAG server:

    ./autogen.sh
    ./configure
    make

## Usage Example

The following command connects to JTAG tap 0 of a running RTL simulation and
listens for connections from GDB on port 1234. The VPI/DPI driver has been
started with port 4567.

    ./adv_jtag_bridge -x 0 -c 8 -l 0:4 -l 1:4 -g 1234 vpi -p 4567

