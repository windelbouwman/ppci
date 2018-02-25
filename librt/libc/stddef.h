
#ifndef STDDEF_H
#define STDDEF_H


typedef int size_t;

#define offsetof(TYPE, MEMBER) __builtin_offsetof(TYPE, MEMBER)

#endif
