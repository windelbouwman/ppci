#ifndef STDARG_H
#define STDARG_H

typedef int* va_list;

// #define va_start(a,f) __builtin_va_start(a,f)
#define va_start(a,f) __builtin_va_start(a)
#define va_arg(a,t) __builtin_va_arg(a,t)
#define va_end(a)

#endif
