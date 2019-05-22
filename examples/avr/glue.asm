; interrupt vector

section reset

rjmp reset
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled
rjmp unhandled

unhandled:
reti

global bsp_init
global bsp_putc
global main_main

reset:
ldi r16, 0x8
out 0x3e, r16  ; Setup stack pointer (SPH)
ldi r16, 0xff
out 0x3d, r16   ; SPL

call __do_copy_data


call bsp_init

; sei  ; enable interrupts
call main_main

; end of transmission:
ldi r24, 4
call bsp_putc

endless:
rjmp endless


section init2

; load data section from program memory to RAM:
global __data_end
global __data_start
global __data_load_start

__do_copy_data:
    ldi r16, low(__data_end)
    ldi r17, high(__data_end)

    ; X at data start:
    ldi r26, low(__data_start)
    ldi r27, high(__data_start)

    ; Z at program memory:
    ldi r30, low(__data_load_start)
    ldi r31, high(__data_load_start)

__do_copy_data_loop:
    lpm r0, Z+
    st X+, r0

    cp r26, r16
    cpc r27, r17
    brne __do_copy_data_loop
    ret
