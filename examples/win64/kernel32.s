
section code

global _main
_main:
; jmp foo
; mov rcx, 65
; call bsp_putchar
global main_main
call main_main

mov rcx, 42
call kernel32_ExitProcess

section data

db 0xaa

section code

global kernel32_ExitProcess
global imp_ExitProcess
kernel32_ExitProcess:
jmp [imp_ExitProcess]

global kernel32_GetStdHandle
global imp_GetStdHandle
kernel32_GetStdHandle:
jmp [imp_GetStdHandle]

global kernel32_WriteFile
global imp_WriteFile
kernel32_WriteFile:
jmp [imp_WriteFile]

bsp_putchar:
; TODO
; push rcx  ; first arg
; jmp [imp__putch]
ret
