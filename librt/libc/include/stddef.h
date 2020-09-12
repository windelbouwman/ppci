
#ifndef STDDEF_H
#define STDDEF_H


typedef int wchar_t;
typedef unsigned int size_t;
typedef int ssize_t;

#define offsetof(TYPE, MEMBER) __builtin_offsetof(TYPE, MEMBER)

#define NULL 0

typedef int ptrdiff_t;

#endif
