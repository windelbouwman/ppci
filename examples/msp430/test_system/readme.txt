
This directory contains the msp430 opencore.

The core can be run with iverilog.

Run a program by first creating a firmware image:

    mkfirm.py ../hello/hello.oj

Then the file pmem.mem is created.

Now run the simulation by running the iverilog generated core:

    ./iverilog/simv

