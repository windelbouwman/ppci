# Advanced Debug Interface

This is an imporoved version of the advanced debug interface from
[OpenCores](http://opencores.org/project,adv_debug_sys). It has been adapted
for the use in the [PULP platform](http://pulp.ethz.ch/).

Changes compared to the initial version:
- Replaced WishBone memory interface with AXI
- Support for 32 and 64 bit wide memory interfaces
- Support for up to 16 cores
- Intelligent handling of multi core debugging

The interface has initially been developed for OpenRISC based processors, but
it is universal and can also be used with other cores. In the PULP project it
is used for both OpenRISC and RISC-V based cores.

## Documentation

The existing documentation has been updated to reflect those changes. It can be
found in `docs/AdvancedDebugInterface.pdf`.
