
section reset

start:
    call main_main
    call bsp_exit

bsp_putc:
        mov [0x20000000], rdi ; store char passed in rdi

        mov rax, 1 ; 1=sys_write
        mov rdi, 1 ; file descriptor
        mov rsi, char_to_print ; char* buf
        mov rdx, 1 ; count
        syscall
        ret

bsp_syscall:
    mov rax, rdi ; abi param 1
    mov rdi, rsi ; abi param 2
    mov rsi, rdx ; abi param 3
    mov rdx, rcx ; abi param 4
    syscall
    ret

section data
    char_to_print:
    dd 0
    dd 0
