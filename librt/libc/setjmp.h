
#ifndef SETJMP_H
#define SETJMP_H 1

typedef int jmp_buf;
int setjmp(jmp_buf env);
void longjmp(jmp_buf env, int val);

#endif
