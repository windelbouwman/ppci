iverilog-vpi vpi_uart.c uart.c
iverilog-vpi -DDBGUART --name=vpi_uartdbg vpi_uart.c uart.c
iverilog -o sim system_tb.v ../system.v ../picorv32.v simuart.v
