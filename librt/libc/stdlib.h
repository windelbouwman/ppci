#ifndef STDLIB_H
#define STDLIB_H

#include <stddef.h>

// Memory
void* malloc(size_t size);
void* calloc(size_t num, size_t size);
void free(void* ptr);

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
