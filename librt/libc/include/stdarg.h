#ifndef STDARG_H
#define STDARG_H

//typedef int* va_list;
typedef __builtin_va_list va_list;

// #define va_start(a,f) __builtin_va_start(a,f)
#define va_start(a,f) __builtin_va_start(a)
#define va_arg(a,t) __builtin_va_arg(a,t)
#define va_end(a)
#define va_copy(dest, src)  __builtin_va_copy(dest,src)

#endif
