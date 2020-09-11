#ifndef STDLIB_H
#define STDLIB_H

#include "stddef.h"
#include "stdbool.h"

// Get insights from https://github.com/embeddedartistry/libc

// Raw
long syscall(long nr, long a, long b, long c);
void *sbrk(long incr);
void *brk(void *addr);

// Memory
void memmove(void *dest, void *src, size_t n);
void memcpy(void *dest, void *src, size_t n);
void memset(void* str, char ch, size_t n);

void *malloc(size_t size);
void *calloc(size_t num, size_t nsize);
void *realloc(void *block, size_t size);
void free(void *block);

void abort(void);

void exit(int status);
#define EXIT_FAILURE 1
#define EXIT_SUCCESS 1

void qsort(void* base, size_t num, size_t size, int(*compar)(const void*, const void*));

// String conversions
int atoi(const char * str);
long int atol(const char * str);
double atof(const char * str);
unsigned long int strtoul(const char* str, char** endptr, int base);
long int strtol(const char* str, char** endptr, int base);
double strtod(const char* str, char** endptr);

#define NULL 0

void* alloca(size_t size);
#define alloca alloca

#endif
