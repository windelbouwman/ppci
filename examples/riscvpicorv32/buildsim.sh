iverilog-vpi vpi_uart.c uart.c
iverilog -o sim.out system_tb.v system.v picorv32.v simuart.v

