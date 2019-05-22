section reset

global main_main

reset:
    jal main_main

section code

global bsp_putc
bsp_putc:
    jr ra
