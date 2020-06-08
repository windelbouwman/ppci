
# riscv example

Example how to run bare metal on qemu.

# Build

    $ python make.py

# Run

    $ qemu-system-riscv32 -M sifive_u -nographic -kernel kernel.elf

# References

This was done with the guidance of this post:

https://theintobooks.wordpress.com/2019/12/28/hello-world-on-risc-v-with-qemu/
