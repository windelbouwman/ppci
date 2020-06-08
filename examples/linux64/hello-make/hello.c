void puts(char *s);
void putc(char c);
void exit(int status);
void syscall(long nr, long a, long b, long c);

int main()
{
    puts("Hello, World!");
    /* As we don't have any C startup code in this example, and main is
       the executable entrypoint, we can't just return, but have to
       call exit syscall explicitly. */
    exit(0);
}

void puts(char *s)
{
    while (*s) {
        putc(*s++);
    }
    putc('\n');
}

void putc(char c)
{
    syscall(1, 1, (long int)&c, 1);
}

void exit(int status)
{
    syscall(60, status, 0, 0);
}

void syscall(long nr, long a, long b, long c)
{
    asm(
        "mov rax, %0 \n"
        "mov rdi, %1 \n"
        "mov rsi, %2 \n"
        "mov rdx, %3 \n"
        "syscall \n"
        :
        : "r" (nr), "r" (a), "r" (b), "r" (c) // input registers, patched into %0 .. %3
        : "rax", "rdi", "rsi", "rdx"  // clobber registers, handled by the register allocator
    );
}
