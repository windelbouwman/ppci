#include <stdlib.h>

long syscall(long nr, long a, long b, long c)
{   
    long ret;

    asm(
        "mov rax, %0 \n"
        "mov rdi, %1 \n"
        "mov rsi, %2 \n"
        "mov rdx, %3 \n"
        "syscall \n"
        : "=r" (ret)
        : "r" (nr), "r" (a), "r" (b), "r" (c)
        : "rax", "rdi", "rsi", "rdx"  // clobber registers, handled by the register allocator
    );

    return ret;
}

void exit(int status)
{   
    syscall(60, status, 0, 0);
}