
#ifndef STDDEF_H
#define STDDEF_H


typedef int wchar_t;
typedef unsigned int size_t;
/**
 * we can probably identify the glibc in a beter way. 
 * This has to be defined outside of the compiler -DGLIBC
 **/
#ifdef GLIBC
typedef __builtin_va_list __gnuc_va_list;
#else
typedef int ssize_t;
#endif

#define offsetof(TYPE, MEMBER) __builtin_offsetof(TYPE, MEMBER)

#define NULL 0

typedef int ptrdiff_t;

#endif
