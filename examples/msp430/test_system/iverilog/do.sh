#!/bin/bash

# Quit on first error:
set -e

# Compile core into simulatable file:
iverilog -o simv -c args.f -D SEED=123
