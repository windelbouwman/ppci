
section code

_main:
; jmp foo
; mov rcx, 65
; call bsp_putchar
call main_main

mov rcx, 42
call kernel32_ExitProcess

section data

db 0xaa

section code

kernel32_ExitProcess:
jmp [imp_ExitProcess]

kernel32_GetStdHandle:
jmp [imp_GetStdHandle]

kernel32_WriteFile:
jmp [imp_WriteFile]

bsp_putchar:
; TODO
; push rcx  ; first arg
; jmp [imp__putch]
ret
