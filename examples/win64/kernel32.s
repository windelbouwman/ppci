
section code

_main:
; jmp foo
call main_main

mov rax, 42
push rax
; TODO:
; call imp_ExitProcess

section data

db 0xaa

section import

; create import table

; dcd 0
; dcd 0 ; timestamp
; dcd 0
; dcd 0
; dcd 0

; null end:
; dcd 0 ; rva
; dcd 0 ; timestamp
; dcd 0 ; forward
; dcd 0 ; name rva
; dcd 0 ; import table

; First table:

; _kernel32table:
