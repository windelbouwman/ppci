
section reset

start:
    call sample_start
    call bsp_exit

bsp_putc:
        mov [0x20000000], rdi ; store char passed in rdi

        mov rax, 1 ; 1=sys_write
        mov rdi, 1 ; file descriptor
        mov rsi, char_to_print ; char* buf
        mov rdx, 1 ; count
        syscall
        ret

bsp_exit:
        mov rax, 60
        mov rdi, 0
        syscall
        ret

section data
    char_to_print:
    dd 0
    dd 0
