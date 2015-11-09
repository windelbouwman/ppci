
section code

; exit with code 42:
; syscall 60 = exit
mov rax, 60
mov rdi, 42
syscall

mov rdx, 1
; lea rcx, [msg]
mov rbx, 1
mov rax, 4
int 0x80


msg:
db 65
