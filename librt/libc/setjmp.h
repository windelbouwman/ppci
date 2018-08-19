
#ifndef STDARG_H
#define STDARG_H

typedef int jmp_buf;
int setjmp(jmp_buf env);
void longjmp(jmp_buf env, int val);

#endif
