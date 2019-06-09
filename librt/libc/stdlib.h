#ifndef STDLIB_H
#define STDLIB_H

#include <stddef.h>

// Memory
void* malloc(size_t size);
void* calloc(size_t num, size_t size);
void free(void* ptr);

void abort(void);

#define NULL 0

void* alloca(size_t size);
#define alloca alloca

#endif
